import datetime
import json
import re
from typing import Dict, Optional

import beemstorage
import pytz
from beem import Hive
from beem.account import Account
from beem.comment import Comment
from beem.community import Community
from beem.discussions import Discussions_by_created, Query
from beem.exceptions import OfflineHasNoRPCException, AccountDoesNotExistsException

from services.Registry import RegistryHandler


class HiveWallet:
    _hive: Hive
    _hiveCommunity: Community
    _username: str
    _communityTag: str

    @staticmethod
    def create(walletPassword: str, postingKey: str) -> bool:
        try:
            hive = Hive()
            hive.wallet.wipe(True)
            hive.wallet.create(walletPassword)
            hive.wallet.unlock(walletPassword)
            hive.wallet.addPrivateKey(postingKey)
        except:
            return False

        return True

    @staticmethod
    def unlock(walletPassword: str, username: str, community: str, hiveApiUrl: str):
        hiveWallet = HiveWallet(username, community, hiveApiUrl)
        try:
            hiveWallet.hive.wallet.unlock(walletPassword)
        except beemstorage.exceptions.WalletLocked:
            return None

        return hiveWallet

    def __init__(self, username, community, hiveApiUrl: str):
        self._hive = Hive(hiveApiUrl)
        self._hiveCommunity = Community(community, blockchain_instance=self._hive)
        self._username = username
        self._subscribers = {}
        self._communityTag = community

    @property
    def hive(self) -> Hive:
        return self._hive

    @property
    def communityTag(self) -> str:
        return self._communityTag
    
    @property
    def username(self):
        return self._username

    def submitComment(self, toAuthor: str, toPermlink: str, message: str) -> bool:
        comment = Comment('@{author}/{permlink}'.format(author=toAuthor, permlink=toPermlink), blockchain_instance=self._hive)
        comment.reply(message, author=self._username)
        return True

    def muteInCommunity(self, comment: Comment, reason: str):
        self._hiveCommunity.mute_post(comment.author, comment.permlink, reason, self._username)

    def getCommunity(self):
        return self._hiveCommunity


class QueuedHiveMessage:
    _toAuthor: str
    _topPermlink: str
    _message: str

    def __init__(self, toPermlink: str, toAuthor: str, message: str):
        self._toAuthor = toAuthor
        self._toPermlink = toPermlink
        self._message = message

    def submit(self, wallet: HiveWallet):
        wallet.submitComment(self._toAuthor, self._toPermlink, self._message)

    def __str__(self):
        return 'Author: {author}\nPermlink: {permlink}\n\n{message}'.format(author=self._toAuthor, permlink=self._toPermlink, message=self._message)


class HiveComment(Comment):
    _cachedBeneficiaries: dict
    _cachedTags: list
    _cachedVotes: dict

    @staticmethod
    def convert(post: Comment) -> 'HiveComment':
        post.__class__ = HiveComment
        post._cachedVotes = {}
        post._cachedTags = []
        post._cachedBeneficiaries = {}
        return post

    @property
    def cachedVotes(self) -> dict:
        if not self._cachedVotes:
            votes = self.get_votes(True)
            self._cachedVotes = {}
            for vote in votes:
                self._cachedVotes[vote['voter']] = vote['rshares']

        return self._cachedVotes

    @property
    def cachedBeneficiaries(self) -> dict:
        if not self._cachedBeneficiaries:
            jsonData = self.json()

            if 'beneficiaries' not in jsonData.keys():
                return {}

            self._cachedBeneficiaries = {}
            for beneficiary in jsonData['beneficiaries']:
                self._cachedBeneficiaries[beneficiary['account']] = beneficiary['weight']

        return self._cachedBeneficiaries

    @property
    def cachedTags(self) -> list:
        if not self._cachedTags:
            jsonData = json.loads(self.json()['json_metadata'])

            self._cachedTags = jsonData['tags'] if 'tags' in jsonData.keys() else []
            self._cachedTags = [x.lower() for x in self._cachedTags]

        return self._cachedTags

    @property
    def ageInSeconds(self):
        return (datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - self['created']).seconds

    @property
    def ageInDays(self):
        return (datetime.datetime.utcnow().replace(tzinfo=pytz.UTC) - self['created']).days


class QueuedPostToMute:
    _hiveComment: HiveComment
    _reason: str

    def __init__(self, comment: HiveComment, reason: str):
        self._hiveComment = comment
        self._reason = reason

    @property
    def comment(self) -> HiveComment:
        return self._hiveComment

    @property
    def reason(self) -> str:
        return self._reason


class HiveHandler:
    MAX_ALREADY_MONITORED_POSTS_TO_REMEMBER: int = 350

    _instance = None
    _hiveWallet: HiveWallet
    _onPostLoadedHandlers: list
    _onReplyLoadedHandlers: list
    _queuedMessages: list
    _muteQueue: list
    _registryHandler: RegistryHandler
    _simulate: bool
    _alreadyMonitoredPosts: list
    _ignorePostsCommentedBy: list
    _exceptAuthors: list

    _subscribers: Dict

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HiveHandler, cls).__new__(cls)
            cls._hiveWallet = None
            cls._onPostLoadedHandlers = []
            cls._onReplyLoadedHandlers = []
            cls._queuedMessages = []
            cls._muteQueue = []
            cls._registryHandler = RegistryHandler()
            cls._alreadyMonitoredPosts = cls._registryHandler.getProperty('HiveHandler', 'alreadyMonitoredPosts', [])
            cls._simulate = False
            cls._ignorePostsCommentedBy = []
            cls._exceptAuthors = []
            cls._subscribers = {}

        return cls._instance

    def getHiveWallet(self):
        return self._hiveWallet

    def setup(self, hiveWallet: HiveWallet, ignorePostsCommentedBy: list, exceptAuthors: list, simulate: bool):
        self._hiveWallet = hiveWallet
        self._simulate = simulate
        self._ignorePostsCommentedBy = ignorePostsCommentedBy
        self._exceptAuthors = exceptAuthors
        self._loadSubscribers()

    def addOnPostLoadedHandler(self, handlerCallback):
        self._onPostLoadedHandlers.append(handlerCallback)

    def _callOnPostLoadedHandlers(self, post: HiveComment):
        for handler in self._onPostLoadedHandlers:
            handler(post)

    def addOnReplyLoadedHandler(self, handlerCallback):
        self._onReplyLoadedHandlers.append(handlerCallback)

    def _callOnReplyLoadedHandlers(self, post: HiveComment):
        for handler in self._onReplyLoadedHandlers:
            handler(post)

    def loadNewestAccountReplies(self, accountName: str):
        try:
            account = Account(accountName, blockchain_instance=self._hiveWallet.hive)
            history = account.reply_history()
            for reply in history:
                if reply.author in self._exceptAuthors:
                    continue

                self._callOnReplyLoadedHandlers(HiveComment.convert(reply))
        except AccountDoesNotExistsException as e:
            return False
        except Exception as e:
            return False

        return True

    def loadNewestCommunityPosts(self, hiveCommunityId: str, communityTags: list, minimumAgeInSeconds: int = 3600) -> bool:
        posts = []
        for communityTag in communityTags:
            q = Query(limit=100, tag=communityTag)
            try:
                for post in Discussions_by_created(q, blockchain_instance=self._hiveWallet.hive):
                    postLink: str = '@{author}/{permlink}'.format(author=post.author, permlink=post.permlink)
                    post: HiveComment = HiveComment.convert(post)

                    if post.category != hiveCommunityId:
                        continue
                    if self._wasPostAlreadyMonitored(postLink):
                        continue

                    if post.ageInSeconds < minimumAgeInSeconds:
                        continue

                    if post.ageInDays > 7:
                        continue

                    self._markPostAsMonitored(postLink)
                    posts.append(post)
            except OfflineHasNoRPCException as e:
                return False

        for post in posts:
            if self._shouldThisPostBeIgnored(post):
                continue
            self._callOnPostLoadedHandlers(post)

        return True

    def _shouldThisPostBeIgnored(self, post) -> bool:
        comments: list = post.get_all_replies(post)
        for comment in comments:
            if comment.author in self._ignorePostsCommentedBy:
                return True

        if post.author in self._exceptAuthors:
            return True

        return False

    def _wasPostAlreadyMonitored(self, postLink: str) -> bool:
        return postLink in self._alreadyMonitoredPosts

    def _markPostAsMonitored(self, postLink: str):
        self._alreadyMonitoredPosts.append(postLink)
        while len(self._alreadyMonitoredPosts) > HiveHandler.MAX_ALREADY_MONITORED_POSTS_TO_REMEMBER:
            self._alreadyMonitoredPosts.pop(0)

        self._registryHandler.setProperty('HiveHandler', 'alreadyMonitoredPosts', self._alreadyMonitoredPosts)

    def enqueuePostToMuteInCommunity(self, hiveComment: HiveComment, reason: str):

        self._muteQueue.append(QueuedPostToMute(hiveComment, reason))

    def enqueueMessage(self, author: str, permlink: str, message: str):
        hiveMessage = QueuedHiveMessage(permlink, author, message)
        self._queuedMessages.append(hiveMessage)

    def processNextQueuedMessages(self) -> bool:
        if len(self._queuedMessages) == 0:
            return False
        hiveMessage: QueuedHiveMessage = self._queuedMessages.pop()
        if not hiveMessage:
            return False

        if self._simulate:
            print('Send hive post: ' + str(hiveMessage))
        else:
            hiveMessage.submit(self._hiveWallet)

        return True

    def muteNextQueuedPosts(self) -> bool:
        if len(self._muteQueue) == 0:
            return False
        queuedPostToMute: QueuedPostToMute = self._muteQueue.pop()
        if not queuedPostToMute:
            return False

        if self._simulate:
            print('Mute hive post: {author}/{permlink}'.format(author=queuedPostToMute.comment.author, permlink=queuedPostToMute.comment.permlink))
        else:
            self._hiveWallet.muteInCommunity(queuedPostToMute.comment, queuedPostToMute.reason)

        return True

    def finish(self):
        # Save subscribers
        jsonSubscribersObject = json.dumps(self._subscribers, indent=4)
        with open("subscribers.json", "w") as outfile:
            outfile.write(jsonSubscribersObject)

    def _loadSubscribers(self):

        with open("subscribers.json", "r") as subscribersJsonFile:
            self._subscribers = json.load(subscribersJsonFile)

        lastFoundId = 0
        usernameExtractionRegex = re.compile(r'^@([a-z0-9_\-\.]+).*$', re.RegexFlag.DOTALL)

        while True:
            activities = self._hiveWallet.getCommunity().get_activities(
                limit=100,
                last_id=None if lastFoundId == 0 else lastFoundId
            )
            if activities is None or len(activities) == 0:
                break
            else:
                lastFoundId = activities[-1]['id']
                for activity in activities:

                    if activity['type'] != 'subscribe':
                        continue

                    match = usernameExtractionRegex.search(activity['msg'])
                    if not match:
                        continue

                    username = str(match[1])
                    if username in self._subscribers.keys():
                        continue

                    self._subscribers[username] = {
                        'joined': activity['date'],
                        'rejoined': False,
                        'posts': -1,
                        'comments': -1,
                        'averageTrailVote': -1
                    }

        # Clean-up
        for subscriber in list(self._subscribers.keys()):
            now = datetime.datetime.now()
            joinDate = datetime.datetime.strptime(self._subscribers[subscriber]['joined'], '%Y-%m-%dT%H:%M:%S')
            numMonths = (now.year - joinDate.year) * 12 + (now.month - joinDate.month)

            if numMonths > 4:
                del self._subscribers[subscriber]

    def getSubscriberInfo(self, subscriberName) -> Optional[Dict]:
        if subscriberName not in self._subscribers.keys():
            return None

        subscriberInfo = self._subscribers[subscriberName]
        subscriberInfo['posts'] = self._countAuthorPostsInCommunity(subscriberName)
        subscriberInfo['comments'] = self._countAuthorCommentsInCommunity(subscriberName)
        self._subscribers[subscriberName] = subscriberInfo

        return subscriberInfo

    def _countAuthorPostsInCommunity(self, subscriberName: str) -> int:
        comments = 0

        account = Account(subscriberName, blockchain_instance=self._hiveWallet.hive)
        for comment in account.blog_history():
            if comment.category == self._hiveWallet.communityTag:
                comments += 1

        return comments

    def _countAuthorCommentsInCommunity(self, subscriberName: str) -> int:
        comments = 0

        account = Account(subscriberName, blockchain_instance=self._hiveWallet.hive)
        for comment in account.comment_history():
            if comment.category == self._hiveWallet.communityTag:
                comments += 1

        return comments

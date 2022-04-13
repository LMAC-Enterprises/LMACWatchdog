import json

import beemstorage
from beem import Hive
from beem.comment import Comment
from beem.community import Community
from beem.discussions import Discussions_by_created, Query
from beem.exceptions import OfflineHasNoRPCException

from services.Registry import RegistryHandler


class HiveWallet:
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
    def unlock(walletPassword: str, username: str, community: str):
        hiveWallet = HiveWallet(username, community)
        try:
            hiveWallet.hive.wallet.unlock(walletPassword)
        except beemstorage.exceptions.WalletLocked:
            return None

        return hiveWallet

    def __init__(self, username, community):
        self._hive = Hive()
        self._hiveCommunity = Community(community, blockchain_instance=self._hive)
        self._username = username

    @property
    def hive(self) -> Hive:
        return self._hive

    def submitComment(self, toAuthor: str, toPermlink: str, message: str) -> bool:
        comment = Comment('@{author}/{permlink}'.format(author=toAuthor, permlink=toPermlink), blockchain_instance=self._hive)
        comment.reply(message, author=self._username)

    def muteInCommunity(self, comment: Comment, reason: str):
        self._hiveCommunity.mute_post(comment.author, comment.permlink, reason, self._username)


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
    def convert(post: Comment):
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

        return self._cachedTags


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
    _instance = None
    _hiveWallet: HiveWallet
    _onPostLoadedHandlers: list
    _queuedMessages: list
    _muteQueue: list

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HiveHandler, cls).__new__(cls)
            cls._hiveWallet = None
            cls._onPostLoadedHandlers = []
            cls._queuedMessages = []
            cls._muteQueue = []

        return cls._instance

    def setup(self, hiveWallet: HiveWallet):
        self._hiveWallet = hiveWallet

    def addOnPostLoadedHandler(self, handlerCallback):
        self._onPostLoadedHandlers.append(handlerCallback)

    def _callOnPostLoadedHandlers(self, post: HiveComment):
        for handler in self._onPostLoadedHandlers:
            handler(post)

    def loadNewestCommunityPosts(self, hiveCommunityId: str, communityTag: str) -> bool:
        registryHandler = RegistryHandler()
        previousNewestPostTimestamp: int = registryHandler.getProperty(self.__class__.__name__,
                                                                       'previousNewestPostTimestamp', 0)

        q = Query(limit=100, tag=communityTag)
        newestPostTimestamp = 0
        try:
            for post in Discussions_by_created(q):
                postTimestamp = int(round(post['created'].timestamp()))
                if previousNewestPostTimestamp > postTimestamp:
                    continue
                if newestPostTimestamp < postTimestamp:
                    newestPostTimestamp = postTimestamp
                if post.category != hiveCommunityId:
                    continue
                self._callOnPostLoadedHandlers(HiveComment.convert(post))
            registryHandler.setProperty(self.__class__.__name__, 'previousNewestPostTimestamp', newestPostTimestamp)
        except OfflineHasNoRPCException as e:
            return False

        return True

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
        print('Send hive post: ' + str(hiveMessage))
        hiveMessage.submit(self._hiveWallet)

        return True

    def muteNextQueuedPosts(self) -> bool:
        if len(self._muteQueue) == 0:
            return False
        queuedPostToMute: QueuedPostToMute = self._muteQueue.pop()
        if not queuedPostToMute:
            return False
        print('Mute hive post: {author}/{permlink}'.format(author=queuedPostToMute.comment.author, permlink=queuedPostToMute.comment.permlink))
        self._hiveWallet.muteInCommunity(queuedPostToMute.comment, queuedPostToMute.reason)

        return True


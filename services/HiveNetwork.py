import json

import beemstorage
from beem import Hive
from beem.comment import Comment
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
    def unlock(walletPassword: str):
        hive = Hive()
        try:
            hive.wallet.unlock(walletPassword)
        except beemstorage.exceptions.WalletLocked:
            return False
        return hive.wallet.unlocked()


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


class HiveHandler:
    _instance = None
    _hiveWalletPassword: str
    _onPostLoadedHandlers: list

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HiveHandler, cls).__new__(cls)
            cls._hiveWalletPassword = ''
            cls._onPostLoadedHandlers = []

        return cls._instance

    def setup(self, hiveWalletPassword):
        self._hiveWalletPassword = hiveWalletPassword

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

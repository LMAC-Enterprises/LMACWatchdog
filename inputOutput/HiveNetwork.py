import json

from beem.comment import Comment
from beem.discussions import Discussions_by_created, Query
from beem.exceptions import OfflineHasNoRPCException


class HiveComment(Comment):
    beneficiaries: dict
    tags: list


class HiveHandler:
    _instance = None
    _hiveWalletPassword: str
    _onPostLoadedHandlers: list

    def __new__(cls):
        if cls._instance is None:
            print('Creating the object')
            cls._instance = super(HiveHandler, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        self._hiveWalletPassword = ''
        self._onPostLoadedHandlers = []

    def setup(self, hiveWalletPassword):
        self._hiveWalletPassword = hiveWalletPassword

    def addOnPostLoadedHandler(self, handlerCallback):
        self._onPostLoadedHandlers.append(handlerCallback)

    def _callOnPostLoadedHandlers(self, post: Comment):
        for handler in self._onPostLoadedHandlers:
            handler(post)

    @staticmethod
    def _getBeneficiaries(post: Comment):
        jsonData = post.json()

        if 'beneficiaries' not in jsonData.keys():
            return {}

        beneficiaries = {}
        for beneficiary in jsonData['beneficiaries']:
            beneficiaries[beneficiary['account']] = beneficiary['weight']

        return beneficiaries

    @staticmethod
    def _getTags(post: Comment):
        jsonData = json.loads(post.json()['json_metadata'])

        return jsonData['tags'] if 'tags' in jsonData.keys() else []

    def loadNewestCommunityPosts(self, hiveCommunityId: str, communityTag: str) -> bool:
        q = Query(limit=100, tag=communityTag)

        try:

            for post in Discussions_by_created(q):

                if post.category != hiveCommunityId:
                    continue

                hivePost: HiveComment = post

                hivePost.tags = self._getTags(post)
                hivePost.beneficiaries = self._getBeneficiaries(post)
                self._callOnPostLoadedHandlers(hivePost)

            return True
        except OfflineHasNoRPCException as e:
            return False

        return True

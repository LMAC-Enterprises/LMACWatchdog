from abc import ABC

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveHandler, HiveComment


class MuteHivePostAction(PolicyAction, ABC):
    _hiveHandler: HiveHandler
    _post: HiveComment
    _reason: str

    def __init__(self, post: HiveComment, reason: str):
        self._hiveHandler = HiveHandler()
        self._post = post
        self._reason = reason

    def onActionRequest(self):
        self._hiveHandler.enqueuePostToMuteInCommunity(self._post, self._reason)
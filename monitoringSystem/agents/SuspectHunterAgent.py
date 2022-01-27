from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class SuspectHunterAgent(Agent, ABC):
    _downvoterIndicators: list

    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._downvoterIndicators = []

    def onSetupRules(self, rules: dict):
        self._downvoterIndicators = rules['downvoterIndicators']

    def _hasPostDownvoteIndicator(self, post: HiveComment):

        downvoters: list = []

        for downvoteIndicator in self._downvoterIndicators:
            if downvoteIndicator not in post.cachedVotes.keys():
                continue

            if int(post.cachedVotes[downvoteIndicator]) < 0:
                downvoters.append(downvoteIndicator)

        return downvoters

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        downvoters = self._hasPostDownvoteIndicator(post)
        if len(downvoters) > 0:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.CONVICTION_DETECTED,
                'User was punished for this post by {downvoter} with downvote.'.format(downvoter=', '.join(downvoters))
            ), None

        return None, None

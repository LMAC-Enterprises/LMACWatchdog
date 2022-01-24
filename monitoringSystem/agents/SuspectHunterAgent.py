import re
from abc import ABC
from re import Pattern

from inputOutput.HiveNetwork import HiveComment
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
        for downvoteIndicator in self._downvoterIndicators:
            vote = post.get_vote_with_curation(downvoteIndicator, True)

            if vote is None:
                continue

            if int(vote['percent']) < 0:
                return downvoteIndicator

        return None

    def onSuspicionQuery(self, post: HiveComment) -> SuspiciousActivityReport:

        downvoter = self._hasPostDownvoteIndicator(post)
        if downvoter is not None:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.WARNING,
                'User was punished for this post by {downvoter} with downvote.'.format(downvoter=downvoter)
            )

        return SuspiciousActivityReport(
            post.author,
            post.permlink,
            self._agentId,
            SuspiciousActivityLevel.UNSUSPICIOUS,
            ''
        )

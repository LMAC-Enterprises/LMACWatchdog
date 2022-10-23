from abc import ABC
from typing import Tuple, Optional

from actionSystem.ActionHandling import PolicyAction
from services.Blacklisting import BlacklistHandler
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel
from services.HiveTools import HivePostIdentifier


class CuratablePostAgent(Agent, ABC):
    _blacklistHandler: BlacklistHandler

    def __init__(self):
        super().__init__(self.__class__.__name__)

    def onSetupRules(self, rules: dict):
        self._blacklistHandler = BlacklistHandler(rules['blacklistSourceUrl'])

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[Optional[SuspiciousActivityReport], Optional[PolicyAction]]:
        if self._blacklistHandler.isEmpty():
            return None, None

        if self._agentSupervisor.wasPostAlreadyObjectedDuringCurrentSession(post.authorperm):
            return None, None

        if not self._blacklistHandler.isBlacklisted(post.author) and 'lmac' not in post.cachedVotes.keys():
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.NEW_CURATABLE_CONTRIBUTION,
                'https://peakd.com/{authorperm}'.format(
                    authorperm=post.authorperm
                ),
                {'postType': HivePostIdentifier.getPostType(post)}
            ), None

        return None, None

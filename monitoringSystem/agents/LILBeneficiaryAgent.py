import re
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from actionSystem.actions.MuteHivePostAction import MuteHivePostAction
from services import HiveTools
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class LILBeneficiaryAgent(Agent, ABC):
    _lilBeneficiaryWeight: int

    def __init__(self):
        super().__init__('LIL Beneficiary Agent')
        self._lilBeneficiaryWeight = 200
        self._urlRegex = re.compile(r'https\:\/\/(?:www\.)?lmac\.gallery\/lil-gallery-image\/\d+', re.DOTALL)

    def onSetupRules(self, rules: dict):
        self._lilBeneficiaryWeight = rules['lilBeneficiaryWeight']

    def _getAllLILUrls(self, text: str):
        urlMatches = re.findall(self._urlRegex, text)
        urls = []
        for urlMatch in urlMatches:
            urls.append(urlMatch)
        return urls

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        if HiveTools.HivePostIdentifier.getPostType(post) != HiveTools.HivePostIdentifier.CONTEST_POST_TYPE:
            return None, None

        lilUrlsFound = self._getAllLILUrls(post.body)

        # OLD SOLUTION:
        # if len(lilUrlsFound) > 0 and self._lilBeneficiaryWeight not in post.cachedBeneficiaries.values():
        if len(lilUrlsFound) > 0 and len(post.cachedBeneficiaries.values()) < 2:  # temporary solution
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.VIOLATION,
                'The author did not set the 2% beneficiary per LIL image. Found {urlsCount} LIL urls in this post.\nUrls:\n{lilUrls}'.format(
                    urlsCount=len(lilUrlsFound),
                    lilUrls='\n'.join(lilUrlsFound)
                )
            ), None # MUTE ACTION REMOVED DUE TO EMERGENCY DECISION.

        return None, None

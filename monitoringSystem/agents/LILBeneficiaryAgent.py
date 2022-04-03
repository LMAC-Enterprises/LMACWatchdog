import re
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class LILBeneficiaryAgent(Agent, ABC):
    _lilBeneficiaryWeight: int

    def __init__(self):
        super().__init__('LIL Beneficiary Agent')
        self._lilBeneficiaryWeight = 200
        self._urlRegex = re.compile(r'https:\/\/lmac.gallery\/lil-gallery-image\/\d+', re.DOTALL)

    def onSetupRules(self, rules: dict):
        self._lilBeneficiaryWeight = rules['lilBeneficiaryWeight']

    def _getAllLILUrls(self, text: str):
        urlMatches = re.findall(self._urlRegex, text)
        urls = []
        for urlMatch in urlMatches:
            urls.append(urlMatch[0])
        return urls

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        lilUrlsFound = self._getAllLILUrls(post.body)

        if len(lilUrlsFound) > 0 and self._lilBeneficiaryWeight not in post.cachedBeneficiaries.values():
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.VIOLATION,
                'The author did not set the 2% beneficiary per LIL image. Found {urlsCount} LIL urls in this post.\nUrls:\n{lilUrls}'.format(
                    urlsCount=len(lilUrlsFound),
                    lilUrls='\n'.join(lilUrlsFound)
                )
            ),  None

        return None, None

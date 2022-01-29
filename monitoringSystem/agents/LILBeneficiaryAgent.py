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
        super().__init__(self.__class__.__name__)
        self._lilBeneficiaryWeight = 200
        self._urlRegex = re.compile(r'https:\/\/lmac.gallery\/lil-gallery-image\/\d+', re.DOTALL)

    def onSetupRules(self, rules: dict):
        self._lilBeneficiaryWeight = rules['lilBeneficiaryWeight']

    def _getAllUrls(self, text: str):
        urlMatches = re.findall(self._urlRegex, text)
        urls = []
        for urlMatch in urlMatches:
            urls.append(urlMatch[0])
        return urls

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        urls = self._getAllUrls(post.body)
        lilUrlsFound = []
        for url in urls:
            for blacklistRegex in self._blacklist:
                if not re.search(blacklistRegex, url):
                    continue

                lilUrlsFound.append(url)

        if len(lilUrlsFound) > 0 and self._lilBeneficiaryWeight not in self._post.cachedBeneficiaries:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.VIOLATION,
                'The author did not set the 2% beneficiary per LIL image. Found {urlsCount} LIL urls in this post.\nUrls:\n{lilUrls}'.format(
                    urlsCount=len(lilUrlsFound),
                    lilUrls='\n'.join(lilUrlsFound)
                )
            ),
            None

        return None, None

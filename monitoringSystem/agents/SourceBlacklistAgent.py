import re
from abc import ABC
from typing import Tuple, Optional

from actionSystem.ActionHandling import PolicyAction
from actionSystem.actions.MuteHivePostAction import MuteHivePostAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel
from services.HiveTools import HivePostIdentifier


class SourceBlacklistAgent(Agent, ABC):
    _blacklist: list

    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._blacklist = []
        self._urlRegex = re.compile(r'((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)', re.DOTALL)

    def onSetupRules(self, rules: dict):
        self._blacklist = rules['blacklist']

    def _getAllUrls(self, text: str):
        urlMatches = re.findall(self._urlRegex, text)
        urls = []
        for urlMatch in urlMatches:
            urls.append(urlMatch[0])
        return urls

    @staticmethod
    def _isContestPost(post: HiveComment):
        return HivePostIdentifier.getPostType(post) == HivePostIdentifier.CONTEST_POST_TYPE

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[Optional[SuspiciousActivityReport], Optional[PolicyAction]]:

        if not self._isContestPost(post):
            return None, None

        urls = self._getAllUrls(post.body)
        unwantedUrlsFound = []
        for url in urls:
            for blacklistRegex in self._blacklist:
                if not re.search(blacklistRegex, url):
                    continue

                unwantedUrlsFound.append(url)

        if len(unwantedUrlsFound) > 0:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.VIOLATION,
                'Found {urlsCount} blacklisted urls in this post.\nUrls:\n{unwantedUrls}'.format(
                    urlsCount=len(unwantedUrlsFound),
                    unwantedUrls=unwantedUrlsFound
                )
            ), None

        return None, None

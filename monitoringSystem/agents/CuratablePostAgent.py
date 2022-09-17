import re
import time
import urllib.request
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel
from services.Registry import RegistryHandler


class CuratablePostAgent(Agent, ABC):
    BLACKLIST_UPDATE_DELAY: int = 86400

    _blacklist: list
    _sourceUrl: str

    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._blacklist = []
        self._sourceUrl = ''

    def onSetupRules(self, rules: dict):
        self._sourceUrl = rules['blacklistSourceUrl']
        self._blacklist = self._loadBlacklist()

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:
        if len(self._blacklist) == 0:
            return None, None

        if post.author not in self._blacklist and 'lmac' not in post.cachedVotes.keys():
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.NEW_CURATABLE_CONTRIBUTION,
                'https://peakd.com/{authorperm}'.format(
                    authorperm=post.authorperm
                )
            ), None

        return None, None

    def _loadBlacklist(self) -> list:
        registry = RegistryHandler()
        currentTimestamp = int(time.time())
        blacklistInfo = registry.getProperty('UserBlacklistAgent', 'blacklistInfo', {'nextUpdate': 0, 'blacklist': []})
        if blacklistInfo['nextUpdate'] < currentTimestamp:
            newBlacklist = self._loadBlacklistFromSource()
            blacklistInfo['blacklist'] = newBlacklist
            blacklistInfo['nextUpdate'] = currentTimestamp + CuratablePostAgent.BLACKLIST_UPDATE_DELAY
            registry.setProperty('UserBlacklistAgent', 'blacklistInfo', blacklistInfo)
            print(newBlacklist
                  )
        return blacklistInfo['blacklist']

    def _loadBlacklistFromSource(self):
        blockPattern = r'<div id=\"doc\".*?>(.*?)</div>'
        startIndicator = '### Blacklist in alphabetic order\n\n'
        print(self._sourceUrl)
        r = urllib.request.urlopen(self._sourceUrl)
        text = r.read().decode('utf-8')
        matchesBlock = re.findall(blockPattern, text, re.DOTALL)
        if len(matchesBlock) == 0:
            return []
        listStart = matchesBlock[0].find(startIndicator) + len(startIndicator)
        return matchesBlock[0][listStart:].split('\n')

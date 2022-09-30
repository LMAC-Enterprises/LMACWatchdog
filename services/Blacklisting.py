import re
import time
import urllib.request
import urllib.error

from services.Registry import RegistryHandler


class BlacklistHandler:
    _blacklist: list
    _sourceUrl: str
    _registry: RegistryHandler

    def __init__(self, sourceUrl: str):
        self._registry = RegistryHandler()
        self._sourceUrl = sourceUrl
        self._blacklist = self._loadBlacklist()

    def _loadBlacklist(self) -> list:
        registry = RegistryHandler()
        currentTimestamp = int(time.time())
        blacklistInfo = registry.getProperty('UserBlacklistAgent', 'blacklistInfo', {'blacklist': []})
        newBlacklist = self._loadBlacklistFromSource()
        if len(blacklistInfo['blacklist']) > 0  and not newBlacklist:
            return blacklistInfo['blacklist']
        elif len(blacklistInfo['blacklist']) == 0 and not newBlacklist:
            return []

        blacklistInfo['blacklist'] = newBlacklist
        registry.setProperty('UserBlacklistAgent', 'blacklistInfo', blacklistInfo)

        return blacklistInfo['blacklist']

    def _loadBlacklistFromSource(self):
        blockPattern = r'<div id=\"doc\".*?>(.*?)</div>'
        startIndicator = '### Blacklist in alphabetic order\n\n'

        try:
            with urllib.request.urlopen(self._sourceUrl) as r:
                text = r.read().decode('utf-8')
                matchesBlock = re.findall(blockPattern, text, re.DOTALL)
                if len(matchesBlock) == 0:
                    return None
                listStart = matchesBlock[0].find(startIndicator) + len(startIndicator)
                return matchesBlock[0][listStart:].split('\n')

        except urllib.error.HTTPError:
            return None

    def isBlacklisted(self, name: str):
        return name in self._blacklist


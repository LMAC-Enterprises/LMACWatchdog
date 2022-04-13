import re

import nltk
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from actionSystem.actions.MuteHivePostAction import MuteHivePostAction
from services.AspectLogging import LogAspect
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class ContestLinkAgent(Agent, ABC):
    _contestLinkRegex = r''
    _mandatoryContestHashtag: str = ''

    def __init__(self):
        super().__init__('Contest Link Agent')
        self._contestLinkRegex = r''
        self._mandatoryContestHashtag = ''
        self._logger = LogAspect('cla')

    def onSetupRules(self, rules: dict):
        self._contestLinkRegex = re.compile(
            r'(https:\/\/[a-zA-Z0-9_\-\.]+)?\/[a-zA-Z0-9_\-\.\/]*@({moderators})[a-zA-Z0-9_\-\.\/]*contest[a-zA-Z0-9_\-\.\/]*round[a-zA-Z0-9_\-\.\/]*'.format(
                moderators=rules['moderators']
            )
        )
        self._mandatoryContestHashtag = rules['mandatoryContestHashtag']

    def _hasContestLink(self, text: str):
        urlMatches = re.findall(self._contestLinkRegex, text)
        for urlMatch in urlMatches:
            return True

        return False

    def _isContestPost(self, post: HiveComment):
        if post.title.startswith('lil'):
            return False
        if '<table class="lil">' in post.body:
            return False
        if self._mandatoryContestHashtag not in post.cachedTags:
            return False

        return True

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        if self._isContestPost(post):
            if not self._hasContestLink(post.body):
                return SuspiciousActivityReport(
                    post.author,
                    post.permlink,
                    self._agentId,
                    SuspiciousActivityLevel.WARNING,
                    'Contest link not found.'
                ), MuteHivePostAction(post, 'LMAC rule violation: Missing contest link.')

        return None, None

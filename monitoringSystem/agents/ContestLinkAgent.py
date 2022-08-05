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
from services.HiveTools import HivePostIdentifier


class ContestLinkAgent(Agent, ABC):
    _contestLinkRegex = r''
    _mandatoryContestHashtag: str = ''

    def __init__(self):
        super().__init__('Contest Link Agent')
        self._contestLinkRegex = r''
        self._mandatoryContestHashtag = ''
        self._logger = LogAspect('cla')

    def onSetupRules(self, rules: dict):
        regexStr = r'(https:\/\/[a-zA-Z0-9_\-\.]+)?\/[a-zA-Z0-9_\-\.\/]*@({moderators})\/[a-zA-Z0-9_\-\.\/]*'.format(
                moderators='|'.join(rules['moderators']))
        self._contestLinkRegex = re.compile(
                regexStr
        )
        self._mandatoryContestHashtag = rules['mandatoryContestHashtag']

    def _hasContestLink(self, text: str):
        urlMatches = re.findall(self._contestLinkRegex, text)
        for urlMatch in urlMatches:
            return True

        return False

    def _isContestPost(self, post: HiveComment):

        return HivePostIdentifier.getPostType(post) == HivePostIdentifier.CONTEST_POST_TYPE

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        if self._isContestPost(post):
            if not self._hasContestLink(post.body):
                print(post.title)
                return SuspiciousActivityReport(
                    post.author,
                    post.permlink,
                    self._agentId,
                    SuspiciousActivityLevel.WARNING,
                    'Contest link not found.'
                ), # MUTE ACTION REMOVED DUE TO EMERGENCY DECISION.

        return None, None

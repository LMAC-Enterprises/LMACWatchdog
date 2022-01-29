import re
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class BadWordsAgent(Agent, ABC):
    _lilBeneficiaryWeight: int

    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._badWords = []

    def onSetupRules(self, rules: dict):
        self._badWords = rules['badWords']

    def _findBadWords(self, text: str):
        text = text.lower()
        foundBadWords = []
        for badWord in self._badWords:
            if badWord not in text:
                continue
            foundBadWords.append(badWord)

        return foundBadWords

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        badWordsFound = self._findBadWords(post.body)

        if len(badWordsFound) > 0:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.ALERT,
                'Found {badWordsCount} bad words in this post. Bad words found:\n{badWords}'.format(
                    badWordsCount=len(badWordsFound),
                    badWords='\n'.join(badWordsFound)
                )
            ),
            None

        return None, None

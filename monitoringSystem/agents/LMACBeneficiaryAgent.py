from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class LMACBeneficiaryAgent(Agent, ABC):
    _minimumBenefication: int
    _requiredBeneficiary: str

    def __init__(self):
        super().__init__(self.__class__.__name__)
        self._minimumBenefication = 0
        self._requiredBeneficiary = ''

    def onSetupRules(self, rules: dict):
        self._minimumBenefication = rules['minimumBenefication']
        self._requiredBeneficiary = rules['requiredBeneficiary']

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        if post.author == 'shaka':
            return None, None

        if 'imac' in post.cachedBeneficiaries:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.WARNING,
                'iMac typo in "@{requiredBeneficiary}" beneficiary.'.format(
                    requiredBeneficiary=self._requiredBeneficiary)
            ), None

        if self._requiredBeneficiary in post.cachedBeneficiaries.keys():
            if post.cachedBeneficiaries[self._requiredBeneficiary] < self._minimumBenefication:
                return SuspiciousActivityReport(
                    post.author,
                    post.permlink,
                    self._agentId,
                    SuspiciousActivityLevel.WARNING,
                    'Insufficient beneficiary weight set for @{requiredBeneficiary}.'.format(requiredBeneficiary=self._requiredBeneficiary)
                ), None
        else:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.WARNING,
                'Beneficiary not set for @{requiredBeneficiary}.'.format(requiredBeneficiary=self._requiredBeneficiary)
            ), None

        return None, None

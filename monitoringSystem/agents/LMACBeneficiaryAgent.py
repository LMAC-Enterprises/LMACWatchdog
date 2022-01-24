from abc import ABC

from inputOutput.HiveNetwork import HiveComment
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

    def onSuspicionQuery(self, post: HiveComment) -> SuspiciousActivityReport:

        if post.author != 'shaka':
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.UNSUSPICIOUS,
                'Unknown type of post.'
            )

        if self._requiredBeneficiary in post.beneficiaries.keys():
            if post.beneficiaries[self._requiredBeneficiary] < self._minimumBenefication:
                return SuspiciousActivityReport(
                    post.author,
                    post.permlink,
                    self._agentId,
                    SuspiciousActivityLevel.WARNING,
                    'Insufficient beneficiary weight set for @' + self._requiredBeneficiary
                )

        return SuspiciousActivityReport(
            post.author,
            post.permlink,
            self._agentId,
            SuspiciousActivityLevel.UNSUSPICIOUS,
            ''
        )

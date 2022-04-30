from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from actionSystem.actions.MuteHivePostAction import MuteHivePostAction
from services import HiveTools
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class LMACBeneficiaryAgent(Agent, ABC):
    _minimumBenefication: int
    _requiredBeneficiary: str

    def __init__(self):
        super().__init__('LMAC Beneficiary Agent')
        self._minimumBenefication = 0
        self._requiredBeneficiary = ''

    def onSetupRules(self, rules: dict):
        self._minimumBenefication = rules['minimumBenefication']
        self._requiredBeneficiary = rules['requiredBeneficiary']

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:
        if HiveTools.HivePostIdentifier.getPostType(post) != HiveTools.HivePostIdentifier.CONTEST_POST_TYPE and \
                HiveTools.HivePostIdentifier.getPostType(post) != HiveTools.HivePostIdentifier.LIL_POST_TYPE:
            return None, None

        if post.author == 'shaka':
            return None, None

        postType = HiveTools.HivePostIdentifier.getPostType(post)

        if 'imac' in post.cachedBeneficiaries:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.WARNING,
                'iMac typo in "@{requiredBeneficiary}" beneficiary.'.format(
                    requiredBeneficiary=self._requiredBeneficiary),
                {'postType': postType}
            ), MuteHivePostAction(post, 'lmac beneficiary not set.')

        if self._requiredBeneficiary in post.cachedBeneficiaries.keys():
            if post.cachedBeneficiaries[self._requiredBeneficiary] < self._minimumBenefication:
                return SuspiciousActivityReport(
                    post.author,
                    post.permlink,
                    self._agentId,
                    SuspiciousActivityLevel.WARNING,
                    'Insufficient beneficiary weight set for @{requiredBeneficiary}.'.format(
                        requiredBeneficiary=self._requiredBeneficiary),
                    {'postType': postType}
                ), MuteHivePostAction(post, 'lmac beneficiary set to low.')
        else:
            return SuspiciousActivityReport(
                post.author,
                post.permlink,
                self._agentId,
                SuspiciousActivityLevel.WARNING,
                'Beneficiary not set for @{requiredBeneficiary}.'.format(requiredBeneficiary=self._requiredBeneficiary),
                {'postType': postType}
            ), MuteHivePostAction(post, 'lmac beneficiary not set.')

        return None, None

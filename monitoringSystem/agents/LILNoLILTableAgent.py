import re
from abc import ABC
from typing import Tuple

from actionSystem.ActionHandling import PolicyAction
from actionSystem.actions.MuteHivePostAction import MuteHivePostAction
from services import HiveTools
from services.HiveNetwork import HiveComment
from monitoringSystem.MonitoringAgency import Agent
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class LILNoLILTableAgent(Agent, ABC):
    _lilBeneficiaryWeight: int

    def __init__(self):
        super().__init__('LIL No LIL table Agent')

    def onSetupRules(self, rules: dict):
        pass

    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:

        if HiveTools.HivePostIdentifier.getPostType(post) != HiveTools.HivePostIdentifier.NO_LIL_TABLE_LIL_POST_TYPE:
            return None, None

        return SuspiciousActivityReport(
            post.author,
            post.permlink,
            self._agentId,
            SuspiciousActivityLevel.MISTAKE,
            'This post is probably a LIL contribution. But couldn\'t find any LIL tables.'
        ), None
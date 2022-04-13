from abc import ABC, abstractmethod
from typing import Tuple, Callable

from actionSystem.ActionHandling import PolicyAction, PolicyActionSupervisor
from services.HiveNetwork import HiveHandler, HiveComment
from reportingSystem.Reporting import SuspiciousActivityReport, ReportDispatcher


class Agent(ABC):
    _agentId: str

    def __init__(self, agentId):
        self._agentId = agentId

    @abstractmethod
    def onSetupRules(self, rules: dict):
        pass

    @abstractmethod
    def onSuspicionQuery(self, post: HiveComment) -> Tuple[SuspiciousActivityReport, PolicyAction]:
        pass


class AgentSupervisor:
    _agents: list
    _hiveCommunityId: str
    _hiveCommunityTag: str
    _hiveHandler: HiveHandler
    _exceptAuthors: list

    def __init__(self, hiveCommunityId: str, hiveCommunityTag, agentsInfo: dict,
                 policyActionSupervisor: PolicyActionSupervisor, reportDispatcher: ReportDispatcher,
                 progressCallback: Callable[[str], None]):
        self._agents = []

        for agentClass in agentsInfo.keys():
            agent: Agent = agentClass()
            agent.onSetupRules(agentsInfo[agentClass])
            self._agents.append(agent)

        self._hiveCommunityId = hiveCommunityId
        self._hiveCommunityTag = hiveCommunityTag
        self._hiveHandler = HiveHandler()
        self._hiveHandler.addOnPostLoadedHandler(self.onHivePostLoaded)
        self._reports = []
        self._policyActionSupervisor = policyActionSupervisor
        self._reportDispatcher = reportDispatcher
        self._progressCallback = progressCallback
        self._exceptAuthors = []

    @property
    def exceptAuthors(self) -> list:
        return self._exceptAuthors

    @exceptAuthors.setter
    def exceptAuthors(self, authors: list):
        self._exceptAuthors = authors

    def onHivePostLoaded(self, post: HiveComment):
        if post.author in self.exceptAuthors:
            return

        for agent in self._agents:
            suspiciousActivityReport, action = agent.onSuspicionQuery(post)

            if suspiciousActivityReport is not None:
                self._reportDispatcher.handOverReport(suspiciousActivityReport)
            if action is not None:
                self._policyActionSupervisor.suggestAction(action)

    def startSearching(self):
        self._reportProgress('Monitoring new Hive posts...')
        if not self._hiveHandler.loadNewestCommunityPosts(self._hiveCommunityId, self._hiveCommunityTag):
            raise IOError('Hive connection error.')

    def finishMonitoringCycle(self):
        self._reportProgress('Promoting reports...')
        self._reportDispatcher.promoteReports()
        self._reportProgress('Processing actions...')
        self._policyActionSupervisor.processActions()
        self._reportProgress('Finished monitoring!')

    def _reportProgress(self, reachedTheTask: str):
        self._progressCallback(reachedTheTask)

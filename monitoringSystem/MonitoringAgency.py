from abc import ABC, abstractmethod

from inputOutput.HiveNetwork import HiveHandler, HiveComment
from reportingSystem.Reporting import SuspiciousActivityReport, SuspiciousActivityLevel


class Agent(ABC):
    _agentId: str

    def __init__(self, agentId):
        self._agentId = agentId

    @abstractmethod
    def onSetupRules(self, rules: dict):
        pass

    @abstractmethod
    def onSuspicionQuery(self, post: HiveComment) -> SuspiciousActivityReport:
        pass


class AgentSupervisor:
    _agents: list
    _hiveCommunityId: str
    _hiveCommunityTag: str
    _hiveHandler: HiveHandler

    def __init__(self, hiveCommunityId: str, hiveCommunityTag, agentsInfo: dict):
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

    def onHivePostLoaded(self, post: HiveComment):
        for agent in self._agents:
            suspiciousActivityReport = agent.onSuspicionQuery(post)
            if suspiciousActivityReport.activityLevel == SuspiciousActivityLevel.UNSUSPICIOUS:
                continue

            self._reports.append(suspiciousActivityReport)

    def startSearching(self):
        if not self._hiveHandler.loadNewestCommunityPosts(self._hiveCommunityId, self._hiveCommunityTag):
            raise IOError('Hive connection error.')

    def getReports(self) -> list:
        return self._reports

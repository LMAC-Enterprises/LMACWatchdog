from abc import ABC, abstractmethod
from typing import Tuple, Callable

from actionSystem.ActionHandling import PolicyAction, PolicyActionSupervisor
from services.HiveNetwork import HiveHandler, HiveComment
from reportingSystem.Reporting import SuspiciousActivityReport, ReportDispatcher
from services.Registry import RegistryHandler


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
    MAX_SAVED_ALREADY_PROCESSED_REPLIES: int = 150

    _agents: list
    _hiveCommunityId: str
    _hiveCommunityTag: str
    _hiveHandler: HiveHandler
    _exceptAuthors: list
    _monitoredPostsCount: int

    def __init__(self, hiveCommunityId: str, hiveCommunityTag, agentsInfo: dict,
                 policyActionSupervisor: PolicyActionSupervisor, reportDispatcher: ReportDispatcher,
                 progressCallback: Callable[[str], None]):
        self._agents = []

        for agentClass in agentsInfo.keys():
            agent: Agent = agentClass()
            agent.onSetupRules(agentsInfo[agentClass])
            self._agents.append(agent)

        self._monitoredPostsCount = 0
        self._hiveCommunityId = hiveCommunityId
        self._hiveCommunityTag = hiveCommunityTag
        self._hiveHandler = HiveHandler()
        self._hiveHandler.addOnPostLoadedHandler(self.onHivePostLoaded)
        self._hiveHandler.addOnReplyLoadedHandler(self.onHiveReplyLoaded)
        self._registryHandler = RegistryHandler()
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

    def onHiveReplyLoaded(self, reply: HiveComment):
        if reply.author in self.exceptAuthors:
            return

        alreadyProcessedReplies = self._registryHandler.getProperty('MonitoringAgency', 'alreadyProcessedReplies', [])
        if reply.authorperm in alreadyProcessedReplies:
            return

        if reply.time_elapsed().days > 7:
            return

        self._reportDispatcher.sendNotification(
            '{replyAuthor} replied to a comment by {hiveNotificatorAccount}.\n@Moderator please review.\n{replyUrl}'.format(
                replyAuthor=reply.author,
                hiveNotificatorAccount=self._hiveHandler.getHiveWallet().username,
                replyUrl='https://peakd.com/{authorPerm}'.format(authorPerm=reply.authorperm)
            ))

        alreadyProcessedReplies.append(reply.authorperm)
        while len(alreadyProcessedReplies) > AgentSupervisor.MAX_SAVED_ALREADY_PROCESSED_REPLIES:
            alreadyProcessedReplies.pop(0)

        self._registryHandler.setProperty('MonitoringAgency', 'alreadyProcessedReplies', alreadyProcessedReplies)

    def onHivePostLoaded(self, post: HiveComment):
        if post.author in self.exceptAuthors:
            return

        self._monitoredPostsCount += 1

        for agent in self._agents:
            suspiciousActivityReport, action = agent.onSuspicionQuery(post)

            if suspiciousActivityReport is not None:
                self._reportDispatcher.handOverReport(suspiciousActivityReport)
            if action is not None:
                self._policyActionSupervisor.suggestAction(action)

    def startSearching(self):
        self._reportProgress('Monitoring new Hive replies...')
        if not self._hiveHandler.loadNewestAccountReplies(self._hiveHandler.getHiveWallet().username):
            raise IOError('Hive connection error while trying to load latest replies.')
        self._reportProgress('Monitoring new Hive posts...')
        if not self._hiveHandler.loadNewestCommunityPosts(self._hiveCommunityId, self._hiveCommunityTag):
            raise IOError('Hive connection error while trying to load latest posts.')
        self._reportProgress('Monitored {monitoredPosts} posts.'.format(monitoredPosts=self._monitoredPostsCount))

    def finishMonitoringCycle(self):
        self._reportProgress('Promoting reports...')
        self._reportDispatcher.promoteReports()
        self._reportProgress('Processing actions...')
        self._policyActionSupervisor.processActions()
        self._reportProgress('Finished monitoring!')

    def _reportProgress(self, reachedTheTask: str):
        self._progressCallback(reachedTheTask)

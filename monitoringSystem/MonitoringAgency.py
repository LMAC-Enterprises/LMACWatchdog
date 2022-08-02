from abc import ABC, abstractmethod
from typing import Tuple, Callable

from actionSystem.ActionHandling import PolicyAction, PolicyActionSupervisor
from services.Discord import DiscordDispatcher
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
    _voterToCheck: str
    _maxVoteTimeToCheck: int
    _generalNotificationsDiscordChannelId: int
    _botName: str

    def __init__(self, hiveCommunityId: str, hiveCommunityTag, agentsInfo: dict,
                 policyActionSupervisor: PolicyActionSupervisor, reportDispatcher: ReportDispatcher,
                 progressCallback: Callable[[str], None], voterToCheck: str, maxVoteTimeToCheck: int,
                 generalNotificationsDiscordChannelId: int, botName: str):
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
        self._hiveHandler.addOnPostLoadedEarlyHandler(self.onHivePostLoadedEarly)
        self._registryHandler = RegistryHandler()
        self._reports = []
        self._policyActionSupervisor = policyActionSupervisor
        self._reportDispatcher = reportDispatcher
        self._progressCallback = progressCallback
        self._exceptAuthors = []
        self._voterToCheck = voterToCheck
        self._maxVoteTimeToCheck = maxVoteTimeToCheck
        self._generalNotificationsDiscordChannelId = generalNotificationsDiscordChannelId
        self._botName = botName

    @property
    def exceptAuthors(self) -> list:
        return self._exceptAuthors

    @exceptAuthors.setter
    def exceptAuthors(self, authors: list):
        self._exceptAuthors = authors

    def _wasCommentedByBot(self, post) -> bool:
        comments: list = post.get_all_replies(post)
        for comment in comments:
            if comment.author == self._botName:
                return True

        return False

    def _checkPostNotVotedInTime(self, post: HiveComment):
        return not self._wasMissingVoteInTimeAlreadyNotified(post) and self._voterToCheck not in post.cachedVotes.keys() \
               and post.ageInSeconds > self._maxVoteTimeToCheck and not self._wasCommentedByBot(post)

    def _wasMissingVoteInTimeAlreadyNotified(self, post: HiveComment):
        return post.authorperm in self._registryHandler.getProperty(
            'MonitoringAgency', 'alreadyNotifiedMissingVotes', [])

    def _notifyAboutMissingVoteInTime(self, post: HiveComment):
        missingVotes = self._registryHandler.getProperty(
            'MonitoringAgency', 'alreadyNotifiedMissingVotes', [])
        missingVotes.append(post.authorperm)
        if len(missingVotes) > AgentSupervisor.MAX_SAVED_ALREADY_PROCESSED_REPLIES:
            missingVotes.pop(0)

        self._registryHandler.setProperty(
            'MonitoringAgency', 'alreadyNotifiedMissingVotes', missingVotes)

        discordDispatcher = DiscordDispatcher()
        discordDispatcher.enterChatroom(self._generalNotificationsDiscordChannelId)
        discordDispatcher.enqueueMessage('http://peakd.com/{authorPerm} has not yet been voted and is older than {maxAge} hours.'.format(
            authorPerm=post.authorperm, postTime=post.time_elapsed(), maxAge=(self._maxVoteTimeToCheck / 60) / 60))

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

    def onHivePostLoadedEarly(self, post: HiveComment):
        if self._checkPostNotVotedInTime(post):
            self._notifyAboutMissingVoteInTime(post)

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

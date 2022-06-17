from abc import ABC, abstractmethod

from services.Discord import DiscordDispatcher, DiscordMessage


class SuspiciousActivityLevel:
    WARNING: int = 1
    VIOLATION: int = 2
    ALERT: int = 3
    CONVICTION_DETECTED: int = 4
    SPAMMING: int = 5


class SuspiciousActivityReport:
    _author: str
    _permlink: str
    _agentId: str
    _activityLevel: int
    _description: str
    _meta: dict

    def __init__(self, author: str, permlink: str, agentId: str, activityLevel: int,
                 description: str, meta: dict = {}):
        self._author = author
        self._permlink = permlink
        self._agentId = agentId
        self._activityLevel = activityLevel
        self._description = description.format(author=author, permlink=permlink, agentId=agentId)
        self._meta = meta

    @property
    def author(self) -> str:
        return self._author

    @property
    def permlink(self) -> str:
        return self._permlink

    @property
    def agentId(self) -> str:
        return self._agentId

    @agentId.setter
    def agentId(self, agent):
        self._agentId = agent

    @property
    def activityLevel(self) -> int:
        return self._activityLevel

    @activityLevel.setter
    def activityLevel(self, level: int):
        self._activityLevel = level

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, text):
        self._description = text

    @property
    def meta(self) -> dict:
        return self._meta

    @meta.setter
    def meta(self, data: dict):
        self._meta = data


class Reporter(ABC):
    @abstractmethod
    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        pass

    @abstractmethod
    def onStart(self, arguments: dict):
        pass


class ReportDispatcher:
    _reporters: list
    _reports: list
    _discordNotificationChannel: int

    MERGED_AGENT_ID = 'Multiple agents'

    def __init__(self, reportersInfo: dict, discordNotificationChannel: int):
        self._reporters = []
        self._reports = []
        self._discordNotificationChannel = discordNotificationChannel

        for reporterClass in reportersInfo.keys():
            reporter: Reporter = reporterClass()
            reporter.onStart(reportersInfo[reporterClass])
            self._reporters.append(reporter)

    def sendNotification(self, message: str):
        discordDispatcher = DiscordDispatcher()
        discordDispatcher.enterChatroom(self._discordNotificationChannel)
        discordDispatcher.enqueueMessage(
            message
        )

    def handOverReport(self, report: SuspiciousActivityReport):
        self._reports.append(report)

    def _unifyReports(self):
        unifiedReports = []
        hiveLinkKeyedReports = {}

        for report in self._reports:
            hiveLink = '@{author}/{permlink}'.format(author=report.author, permlink=report.permlink)
            if hiveLink not in hiveLinkKeyedReports.keys():
                hiveLinkKeyedReports[hiveLink] = report
                continue

            baseReport = hiveLinkKeyedReports[hiveLink]

            if baseReport.activityLevel < report.activityLevel:
                baseReport.activityLevel = report.activityLevel

            baseReport.description = '{baseReport}\n{additionalReport}'.format(
                baseReport=baseReport.description,
                additionalReport=report.description
            )
            baseReport.agentId = '{baseReportAgentIds}, {additionalReportAgentIds}'.format(
                baseReportAgentIds=baseReport.agentId,
                additionalReportAgentIds=report.agentId
            )

        for hiveLink in hiveLinkKeyedReports.keys():
            report = hiveLinkKeyedReports[hiveLink]
            if ',' in report.agentId:
                report.agentId = 'Collaborated:' + report.agentId

        return hiveLinkKeyedReports.values()

    def promoteReports(self):
        # self._unifyReports()
        for report in self._reports:
            for reporter in self._reporters:
                reporter.onNewReportAvailable(report)

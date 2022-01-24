from abc import ABC, abstractmethod
from enum import Enum


class SuspiciousActivityLevel(Enum):
    UNSUSPICIOUS: int = 1
    WARNING: int = 2
    RULE_BREAKER: int = 3


class SuspiciousActivityReport:
    _author: str
    _permlink: str
    _agentId: str
    _activityLevel: SuspiciousActivityLevel
    _description: str

    def __init__(self, author: str, permlink: str, agentId: str, activityLevel: SuspiciousActivityLevel,
                 description: str):
        self._author = author
        self._permlink = permlink
        self._agentId = agentId
        self._activityLevel = activityLevel
        self._description = description.format(author=author, permlink=permlink, agentId=agentId)

    @property
    def author(self) -> str:
        return self._author

    @property
    def permlink(self) -> str:
        return self._permlink

    @property
    def agentId(self) -> str:
        return self._agentId

    @property
    def activityLevel(self) -> SuspiciousActivityLevel:
        return self._activityLevel

    @property
    def description(self) -> str:
        return self._description


class Reporter(ABC):
    @abstractmethod
    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        pass

    @abstractmethod
    def onStart(self, arguments: dict):
        pass


class ReportDispatcher:
    _reporters: list

    def __init__(self, reportersInfo: dict):
        self._reporters = []

        for reporterClass in reportersInfo.keys():
            reporter: Reporter = reporterClass()
            reporter.onStart(reportersInfo[reporterClass])
            self._reporters.append(reporter)

    def sendReports(self, reports: list):
        for report in reports:
            self.sendReport(report)

    def sendReport(self, report: SuspiciousActivityReport):
        for reporter in self._reporters:
            reporter.onNewReportAvailable(report)

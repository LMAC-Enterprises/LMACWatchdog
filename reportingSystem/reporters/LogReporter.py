import logging
from abc import ABC

from reportingSystem.Reporting import Reporter, SuspiciousActivityReport, SuspiciousActivityLevel
from services.AspectLogging import LogAspect


class LogReporter(Reporter, ABC):
    _logAspect: LogAspect

    def __init__(self):
        self._logAspect = LogAspect('Watchdog', '%(asctime)s ->  %(message)s', logging.INFO)

    def onStart(self, arguments: dict):
        self._logAspect.logger().info('Started watching...')

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.activityLevel == SuspiciousActivityLevel.UNSUSPICIOUS:
            return

        if report.activityLevel == SuspiciousActivityLevel.WARNING:
            message = 'Violation report for post: @{author}/{permlink}; Message: {message}; Agent: {agentId}'.format(
                message=report.description,
                author=report.author,
                permlink=report.permlink,
                agentId=report.agentId
            )
        else:
            message = 'Warning report for post: @{author}/{permlink}; Message: {message}; Agent: {agentId}'.format(
                message=report.description,
                author=report.author,
                permlink=report.permlink,
                agentId=report.agentId
            )

        self._logAspect.logger().info(message)

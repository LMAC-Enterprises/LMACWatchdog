from reportingSystem.Reporting import Reporter, SuspiciousActivityReport
from services.Discord import DiscordDispatcher


class ViolationReporter(Reporter):
    _discordDispatcher: DiscordDispatcher
    _settingsByLevel: dict

    def __init__(self):
        self._discordDispatcher = DiscordDispatcher()
        self._settingsByLevel = {}

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.activityLevel not in self._settingsByLevel:
            return

        self._discordDispatcher.enterChatroom(self._settingsByLevel[report.activityLevel]['discordTargetChatroom'])
        self._discordDispatcher.enqueueMessage(
            '{report}\nhttps://peakd.com/@{author}/{permlink}'.format(
                report=report.description,
                permlink=report.permlink,
                author=report.author
            )
        )

    def onStart(self, arguments: dict):
        self._settingsByLevel = arguments['settingsByLevel']

from reportingSystem.Reporting import Reporter, SuspiciousActivityReport, SuspiciousActivityLevel
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


class BlacklistedUserReporter(Reporter):
    _discordDispatcher: DiscordDispatcher

    def __init__(self):
        self._discordDispatcher = DiscordDispatcher()
        self._reportInDiscordChannelId = 0

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.activityLevel != SuspiciousActivityLevel.BLACKLISTED_USER:
            return

        self._discordDispatcher.enterChatroom(self._reportInDiscordChannelId)
        self._discordDispatcher.enqueueMessage(
            '{report}\nhttps://peakd.com/@{author}/{permlink}'.format(
                report=report.description,
                permlink=report.permlink,
                author=report.author
            )
        )

    def onStart(self, arguments: dict):
        self._reportInDiscordChannelId = arguments['reportInDiscordChannelId']


class CuratablePostReporter(Reporter):
    _discordDispatcher: DiscordDispatcher

    def __init__(self):
        self._discordDispatcher = DiscordDispatcher()
        self._reportInDiscordChannelId = 0

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.activityLevel != SuspiciousActivityLevel.NEW_CURATABLE_CONTRIBUTION:
            return

        self._discordDispatcher.enterChatroom(self._reportInDiscordChannelId)
        self._discordDispatcher.enqueueMessage(
            'https://peakd.com/@{author}/{permlink}'.format(
                permlink=report.permlink,
                author=report.author
            )
        )

    def onStart(self, arguments: dict):
        self._reportInDiscordChannelId = arguments['reportInDiscordChannelId']

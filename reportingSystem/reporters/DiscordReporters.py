from reportingSystem.Reporting import Reporter, SuspiciousActivityReport, SuspiciousActivityLevel
from services.Discord import DiscordDispatcher
from services.HiveTools import HivePostIdentifier


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
        if not (report.activityLevel == SuspiciousActivityLevel.NEW_CURATABLE_CONTRIBUTION
                or report.activityLevel == SuspiciousActivityLevel.NEW_MAYBE_NOT_CURATABLE_CONTRIBUTION):
            return

        additionalInfo: str = ''

        if report.activityLevel == SuspiciousActivityLevel.NEW_MAYBE_NOT_CURATABLE_CONTRIBUTION:
            additionalInfo = ':warning: This post is suspected of violating the rules. See #no-vote-list.\n'

        if 'postType' not in report.meta or report.meta['postType'] == HivePostIdentifier.UNKOWN_POST_TYPE:
            postTypeText = 'Unknown post type.'
        else:
            if report.meta['postType'] == HivePostIdentifier.CONTEST_POST_TYPE:
                postTypeText = 'Contest entry.'
            elif report.meta['postType'] == HivePostIdentifier.LIL_POST_TYPE:
                postTypeText = 'LIL contribution.'
            elif report.meta['postType'] == HivePostIdentifier.TUTORIAL_POST_TYPE:
                postTypeText = 'Tutorial.'
            elif report.meta['postType'] == HivePostIdentifier.NO_LIL_TABLE_LIL_POST_TYPE:
                postTypeText = 'Could be a LIL contribution. But the LIL table is missing.'
            else:
                postTypeText = 'Unknown post type.'

        self._discordDispatcher.enterChatroom(self._reportInDiscordChannelId)
        self._discordDispatcher.enqueueMessage(
            '{info}{postType}\nhttps://peakd.com/@{author}/{permlink}'.format(
                postType=postTypeText,
                permlink=report.permlink,
                author=report.author,
                info=additionalInfo
            )
        )

    def onStart(self, arguments: dict):
        self._reportInDiscordChannelId = arguments['reportInDiscordChannelId']

import argparse
import time

from Configuration import Configuration
from actionSystem.ActionHandling import PolicyActionSupervisor
from monitoringSystem.agents import LMACBeneficiaryAgent, SourceBlacklistAgent, SuspectHunterAgent, \
    LILBeneficiaryAgent, BadWordsAgent, ContestLinkAgent
from monitoringSystem.MonitoringAgency import AgentSupervisor
from reportingSystem.Reporting import ReportDispatcher
from reportingSystem.reporters import LogReporter, DiscordReporters, HiveReporters
from services.AspectLogging import LogAspect
from services.Discord import DiscordDispatcher
from services.HiveNetwork import HiveWallet, HiveHandler
from services.Registry import RegistryHandler

EXITCODE_OK: int = 0
EXITCODE_ERROR: int = 1

verboseMode: bool = False
mainLogger: LogAspect = LogAspect('WatchdogMain')


# LAST RUNTIME TIME_CODE: 1643454930
def logInfo(message: str):
    if verboseMode:
        print(message)
    mainLogger.logger().info(message)


def _onAgentSupervisorProgress(reachedTask: str):
    if verboseMode:
        logInfo('Processing: {task}'.format(task=reachedTask))


def main(arguments: dict) -> int:
    simulate: bool = arguments['simulate']

    # Unlock Hive wallet.
    hiveWallet = HiveWallet.unlock(
        Configuration.hiveWalletPassword, Configuration.hiveUser, Configuration.hiveCommunityId
    )
    if not hiveWallet:
        logInfo('Error. Wrong wallet password.')
        return EXITCODE_ERROR

    # Initialize HiveHandler singleton.
    hiveHandler = HiveHandler()
    hiveHandler.setup(hiveWallet, simulate)

    # Initialize RegistryHandler.
    registryHandler = RegistryHandler()
    registryHandler.setSimulationMode(simulate)

    # Initialize ReportDispatcher.
    reportDispatcher = ReportDispatcher({
            DiscordReporters.ViolationReporter: Configuration.violationReporterSettings,
            LogReporter.LogReporter: {},
            HiveReporters.ContestLinkHiveReporter: {},
            HiveReporters.LILBeneficiaryHiveReporter: {},
            HiveReporters.LMACBeneficiaryHiveReporter: {}
        }
    )

    # Initialize PolicyActionSupervisor.
    policyActionSupervisor = PolicyActionSupervisor()

    # Initialize AgentSupervisor
    agentSupervisor = AgentSupervisor(
        Configuration.agentSupervisorSettings['hiveCommunityId'],
        Configuration.agentSupervisorSettings['hiveCommunityTags'], {
            LMACBeneficiaryAgent.LMACBeneficiaryAgent: Configuration.lmacBeneficiaryAgentRules,
            LILBeneficiaryAgent.LILBeneficiaryAgent: Configuration.lilBeneficiaryAgentRules,
            SourceBlacklistAgent.SourceBlacklistAgent: Configuration.sourceBlacklistAgentRules,
            SuspectHunterAgent.SuspectHunterAgent: Configuration.suspectHunterAgentRules,
            BadWordsAgent.BadWordsAgent: Configuration.badWordsAgentRules,
            ContestLinkAgent.ContestLinkAgent: Configuration.contestLinkAgentRules
        },
        policyActionSupervisor,
        reportDispatcher,
        _onAgentSupervisorProgress
    )

    agentSupervisor.exceptAuthors = Configuration.exceptAuthors

    # Start supervising
    try:
        agentSupervisor.startSearching()
    except IOError:
        logInfo('Could not load Hive posts.')
        return EXITCODE_ERROR

    agentSupervisor.finishMonitoringCycle()

    discordDispatcher = DiscordDispatcher()
    discordDispatcher.setSimulationMode(simulate)
    discordDispatcher.runDiscordTasks(Configuration.discordToken)

    while hiveHandler.processNextQueuedMessages():
        if not simulate:
            time.sleep(Configuration.delayBetweenSendingHiveComments)

    while hiveHandler.muteNextQueuedPosts():
        if not simulate:
            time.sleep(Configuration.delayBetweenMutingHiveComments)

    registryHandler.saveAll()

    return EXITCODE_OK


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'Monitors a community for contributions that do not comply with the rules.'
    parser.add_argument(
        '-verbose',
        type=bool,
        help='True for enabled verbose mode.',
        required=False
    )
    parser.add_argument(
        '-simulate',
        type=bool,
        help='True for enabling the simulation mode. No messages will be sent, no action will be done.',
        required=False
    )
    args = parser.parse_args()
    verboseMode = args.verbose

    exit(
        main(
            vars(
                args
            )
        )
    )

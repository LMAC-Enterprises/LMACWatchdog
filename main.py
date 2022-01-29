import argparse

from Configuration import Configuration
from actionSystem.ActionHandling import PolicyActionSupervisor
from monitoringSystem.agents import LMACBeneficiaryAgent, SourceBlacklistAgent, SuspectHunterAgent, \
    LILBeneficiaryAgent, BadWordsAgent
from monitoringSystem.MonitoringAgency import AgentSupervisor
from reportingSystem.Reporting import ReportDispatcher
from reportingSystem.reporters import LogReporter, DiscordReporters
from services.Discord import DiscordDispatcher
from services.HiveNetwork import HiveWallet
from services.Registry import RegistryHandler

EXITCODE_OK: int = 0
EXITCODE_ERROR: int = 1


# LAST RUNTIME TIMECODE: 1643454930

def _onAgentSupervisorProgress(reachedTask: str):
    print(reachedTask)


def _initialize() -> int:
    print('Create a new local wallet first.')
    hiveWalletPassword = input('Password:')
    hivePostingKey = input('Posting key:')
    print('Initialisation finished!')


def main(arguments: dict) -> int:
    if not arguments['initialize'] and not (
            'discordToken' in arguments.keys() and 'walletPassword' in arguments.keys()):
        return EXITCODE_ERROR

    if arguments['initialize']:
        return _initialize()

    if not HiveWallet.unlock(arguments['walletPassword']):
        print('Error. Wrong wallet password.')
        return EXITCODE_ERROR

    registryHandler = RegistryHandler()

    reportDispatcher = ReportDispatcher({
        DiscordReporters.ViolationReporter: Configuration.violationReporterSettings,
        LogReporter.LogReporter: {}
    }
    )

    policyActionSupervisor = PolicyActionSupervisor({})

    agentSupervisor = AgentSupervisor(
        Configuration.agentSupervisorSettings['hiveCommunityId'],
        Configuration.agentSupervisorSettings['hiveCommunityTag'], {
            LMACBeneficiaryAgent.LMACBeneficiaryAgent: Configuration.lmacBeneficiaryAgentRules,
            LILBeneficiaryAgent.LILBeneficiaryAgent: Configuration.lilBeneficiaryAgentRules,
            SourceBlacklistAgent.SourceBlacklistAgent: Configuration.sourceBlacklistAgentRules,
            SuspectHunterAgent.SuspectHunterAgent: Configuration.suspectHunterAgentRules,
            BadWordsAgent.BadWordsAgent: Configuration.badWordsAgentRules,
        },
        policyActionSupervisor,
        reportDispatcher,
        _onAgentSupervisorProgress
    )

    try:
        agentSupervisor.startSearching()
    except IOError:
        print('Could not load Hive posts.')
        return EXITCODE_ERROR

    agentSupervisor.finishMonitoringCycle()

    registryHandler.saveAll()

    discordDispatcher = DiscordDispatcher()
    discordDispatcher.runDiscordTasks(arguments['discordToken'])

    return EXITCODE_OK


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'Monitors a community for contributions that do not comply with the rules.'
    parser.add_argument(
        '-discordToken',
        type=str,
        help='Discord token. -discordToken [TOKEN]',
        required=False
    )
    parser.add_argument(
        '-walletPassword',
        type=str,
        help='Local wallet password. -discordToken [TOKEN]',
        required=False
    )
    parser.add_argument(
        '-initialize',
        help='Discord access token. -discordToken [TOKEN]',
        required=False
    )

    exit(
        main(
            vars(
                parser.parse_args()
            )
        )
    )

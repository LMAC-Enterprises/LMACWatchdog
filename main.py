import argparse

from Configuration import Configuration
from monitoringSystem.agents import LMACBeneficiaryAgent, SourceBlacklistAgent, SuspectHunterAgent
from monitoringSystem.MonitoringAgency import AgentSupervisor
from reportingSystem.Reporting import ReportDispatcher
from reportingSystem.reporters import LogReporter

EXITCODE_OK: int = 0
EXITCODE_ERROR: int = 1


def main(arguments: dict) -> int:
    agentSupervisor = AgentSupervisor(
        Configuration.agentSupervisor['hiveCommunityId'],
        Configuration.agentSupervisor['hiveCommunityTag'], {
            LMACBeneficiaryAgent.LMACBeneficiaryAgent: Configuration.lmacBeneficiaryAgent,
            SourceBlacklistAgent.SourceBlacklistAgent: Configuration.sourceBlacklistAgentRules,
            SuspectHunterAgent.SuspectHunterAgent: Configuration.suspectHunterAgent
        })

    try:
        agentSupervisor.startSearching()
    except IOError:
        return EXITCODE_ERROR

    reportDispatcher = ReportDispatcher({
        # PostCommentReporter.PostCommentReporter: {'hiveWalletPassword': 'xyz'},
        # DiscordReporter.DiscordReporter: {'discordToken': ''},
        LogReporter.LogReporter: {}
    }
    )

    reports = agentSupervisor.getReports()
    if len(reports) == 0:
        return EXITCODE_OK

    reportDispatcher.sendReports(reports)

    return EXITCODE_OK


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.description = 'Monitors a community for contributions that do not comply with the rules.'
    """parser.add_argument(
        '-a',
        type=str,
        help='Hive url of a post. Syntax: \'contestthumbnailer.py -a "@user/permlink"\'.',
        required=True
    )"""

    exit(
        main(
            vars(
                parser.parse_args()
            )
        )
    )

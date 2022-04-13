from reportingSystem.Reporting import Reporter, SuspiciousActivityReport
from services.HiveNetwork import HiveHandler
from services.TemplateHandling import TemplateEngine


class LMACBeneficiaryHiveReporter(Reporter):
    _hiveHandler: HiveHandler
    _templateEngine: TemplateEngine

    def __init__(self):
        self._hiveHandler = HiveHandler()
        self._templateEngine = TemplateEngine()

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.agentId != 'LMAC Beneficiary Agent':
            return

        self._hiveHandler.enqueueMessage(
            report.author,
            report.permlink,
            self._templateEngine.createContent(
                'lmacSubmissionBeneficiary',
                author=report.author,
                postSubject='LMAC contest'
            )
        )

    def onStart(self, arguments: dict):
        pass


class LILBeneficiaryHiveReporter(Reporter):
    _hiveHandler: HiveHandler
    _templateEngine: TemplateEngine

    def __init__(self):
        self._hiveHandler = HiveHandler()
        self._templateEngine = TemplateEngine()

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.agentId != 'LIL Beneficiary Agent':
            return

        self._hiveHandler.enqueueMessage(
            report.author,
            report.permlink,
            self._templateEngine.createContent(
                'lilSubmissionBeneficiary',
                author=report.author,
                postSubject='#LIL'
            )
        )

    def onStart(self, arguments: dict):
        pass


class ContestLinkHiveReporter(Reporter):
    _hiveHandler: HiveHandler
    _templateEngine: TemplateEngine

    def __init__(self):
        self._hiveHandler = HiveHandler()
        self._templateEngine = TemplateEngine()

    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        if report.agentId != 'Contest Link Agent':
            return

        self._hiveHandler.enqueueMessage(
            report.author,
            report.permlink,
            self._templateEngine.createContent(
                'contestLinkMissing',
                author=report.author,
                postSubject='LMAC contest'
            )
        )

    def onStart(self, arguments: dict):
        pass


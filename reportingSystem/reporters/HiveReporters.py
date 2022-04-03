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
        if report.agentId not in ['LMAC Beneficiary Agent', 'LIL Beneficiary Agent']:
            return

        self._hiveHandler.enqueueMessage(
            report.author,
            report.permlink,
            self._templateEngine.createContent()
        )

    def onStart(self, arguments: dict):
        pass


from reportingSystem.Reporting import Reporter, SuspiciousActivityReport


class LMACBeneficiaryReporter(Reporter):
    def onNewReportAvailable(self, report: SuspiciousActivityReport):
        pass

    def onStart(self, arguments: dict):
        pass

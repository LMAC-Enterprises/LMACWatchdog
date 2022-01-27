import logging


class LogAspect:
    _logger: logging.Logger

    def __init__(self, aspect: str, logFormat: str, logLevel: int):
        self._logger = logging.getLogger(aspect)

        self._logger.setLevel(logLevel)
        logFileHandler = logging.FileHandler(aspect + '.log')
        logFileHandler.setLevel(logLevel)
        logFileHandler.setFormatter(logging.Formatter(logFormat))
        self._logger.addHandler(logFileHandler)

    def logger(self):
        return self._logger
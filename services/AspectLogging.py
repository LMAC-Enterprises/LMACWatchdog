import logging


class LogAspect:
    _logger: logging.Logger

    def __init__(self, aspect: str, logFormat: str = ' %(name)s :: %(levelname)-8s :: %(message)s', logLevel: int = logging.INFO):
        self._logger = logging.getLogger(aspect)

        self._logger.setLevel(logLevel)
        logFileHandler = logging.FileHandler(aspect + '.log')
        logFileHandler.setLevel(logLevel)
        logFileHandler.setFormatter(logging.Formatter(fmt=logFormat, datefmt='%a %d %b %Y %H:%M:%S'))
        self._logger.addHandler(logFileHandler)

    def logger(self):
        return self._logger

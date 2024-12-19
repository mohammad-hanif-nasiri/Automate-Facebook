import sys

from loguru import logger
from chrome import Chrome

format = (
    "<b>[<cyan>{time:YYYY-MM-DD HH:MM:SS A}</cyan>]</b> "
    "<b><level>[<b>{level: ^8}</b>]</level></b> "
    "[<green><b>{module}<w>:</w>{name}<w>:</w>{line:06}</b></green>] {message}"
)

logger.remove()
logger.add(".log", format=format, mode="w")
logger.add(sys.stdout, format=format)

logger = logger.opt(colors=True)


class MyLogger:
    def __init__(self, logger) -> None:
        self._logger = logger

    def error(self, message, **kwargs):
        Chrome.report(message)
        self._logger.error(message, **kwargs)

    def warning(self, message, *args, **kwargs) -> None:
        Chrome.report(message)
        self._logger.warning(message, *args, **kwargs)

    # Optional: Pass through all other methods
    def __getattr__(self, item):
        return getattr(self._logger, item)


logger = MyLogger(logger)

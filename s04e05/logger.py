import contextvars
import logging
import os
import sys

LOG_FILE = os.path.join(os.path.dirname(__file__), "run.log")

_current_agent: contextvars.ContextVar[str] = contextvars.ContextVar("_current_agent", default="")


class AgentFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        agent = _current_agent.get()
        record.name_display = f"{agent} | {record.name}" if agent else record.name
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(name_display)s] %(message)s", datefmt="%H:%M:%S")
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        sh.addFilter(AgentFilter())
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.addFilter(AgentFilter())
        logger.addHandler(sh)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

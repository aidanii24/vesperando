import datetime
import logging
import os
from rich.logging import RichHandler

from vesperando_core.conf.settings import Paths


class VesperandoLogFormatter(logging.Formatter):
    def __init__(self, fmt=None, markup=False,  **kwargs):
        super().__init__()

        self.markup = markup

        self.styles = {
            logging.NOTSET: None,
            logging.DEBUG: "blue",
            logging.INFO: None,
            logging.WARNING: "yellow",
            logging.ERROR: "red",
            logging.CRITICAL: "bold red"
        }

        self.fmts = {
            logging.NOTSET: "{f_name:<10}%(message)s",
            logging.DEBUG: f"{"[DEBUG]":<10}(%(asctime)s) %(name)s:  %(message)s",
            logging.INFO: "%(message)s",
            logging.WARNING: f"{"[WARNING]":<10} %(name)s:  %(message)s",
            logging.ERROR: f"{"[ERROR]":<10} %(name)s:  %(message)s",
            logging.CRITICAL: f"{"[CRITICAL]":<10} %(name)s:  %(message)s",
        }

    def format(self, record):
        fmt = self.fmts.get(record.levelno, self.fmts.get(0))
        if self.markup and self.styles.get(record.levelno, None):
            style = self.styles.get(record.levelno)
            fmt = f"[{style}]{fmt}[/{style}]"

        formatter = logging.Formatter(fmt)
        return formatter.format(record)

def setup_logging(name: str = __name__):
    # Create Console Output Handling
    out = RichHandler(show_time=False, show_level=False, show_path=False, markup=True)
    out.setFormatter(VesperandoLogFormatter(markup=True))

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(out)

def set_file_handler(filename: str, logger: logging.Logger):
    if not os.path.isdir(Paths.LOG_DIR):
        os.makedirs(Paths.LOG_DIR)

    # Create File Handling
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(VesperandoLogFormatter())

    logger.addHandler(file_handler)
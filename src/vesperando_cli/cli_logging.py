import logging

from rich.logging import RichHandler


class VesperandoLogFormatter(logging.Formatter):
    def __init__(self, fmt=None, **kwargs):
        super().__init__()

        self.fmts = {
            logging.NOTSET: "{f_name:<12}%(message)s",
            logging.DEBUG: f"[blue]{"[DEBUG]":<12}(%(asctime)s) %(name)s:  %(message)s[/blue]",
            logging.INFO: "%(message)s",
            logging.WARNING: f"[yellow]{"[WARNING]":<12} %(name)s:  %(message)s[/yellow]",
            logging.ERROR: f"[red]{"[ERROR]":<12} %(name)s:  %(message)s[/red]",
            logging.CRITICAL: f"[bold red]{"[CRITICAL]":<12} %(name)s:  %(message)s[/bold red]",
        }

    def format(self, record):
        fmt = self.fmts.get(record.levelno, self.fmts.get(0))
        formatter = logging.Formatter(fmt)
        return formatter.format(record)

def setup_logging(name: str = __name__):
    handler = RichHandler(show_time=False, show_level=False, show_path=False, markup=True)
    handler.setFormatter(VesperandoLogFormatter())

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

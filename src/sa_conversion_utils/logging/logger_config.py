import logging
import os
from rich.console import Console

class RichHandler(logging.Handler):
    """Logs messages safely to a Rich console (works with progress bars)."""
    def __init__(self, console: Console, level=logging.NOTSET):
        super().__init__(level)
        self.console = console

    def emit(self, record):
        msg = self.format(record)
        self.console.print(msg)  # Progress-safe

def logger_config(name=__name__, log_file=None, level=logging.INFO, rich_console: Console = None):
    """Setup logger with file logging always, and optional Rich console logging."""
    logs_dir = "workspace\\logs"
    os.makedirs(logs_dir, exist_ok=True)

    if log_file is None:
        log_file = f"{name}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # logger.propagate = False

    if not logger.handlers:
        # File handler (always)
        file_handler = logging.FileHandler(os.path.join(logs_dir, log_file), encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(levelname)s | %(name)s.%(funcName)s:%(lineno)s | %(asctime)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Rich console handler (optional)
        if rich_console:
            rich_handler = RichHandler(rich_console, level=logging.ERROR)
            rich_formatter = logging.Formatter("[red]%(levelname)s[/red] | %(message)s")
            rich_handler.setFormatter(rich_formatter)
            logger.addHandler(rich_handler)

    return logger

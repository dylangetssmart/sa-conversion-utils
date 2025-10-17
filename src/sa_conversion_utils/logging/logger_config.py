import logging
import os
from logging.handlers import RotatingFileHandler
from rich.console import Console

class RichConsoleStatusHandler(logging.Handler):
    """
    Logs only specific 'PASS' or 'FAIL' messages to the Rich console,
    ignoring detailed log messages.
    """
    def __init__(self, console: Console, level=logging.NOTSET):
        super().__init__(level)
        self.console = console

    def emit(self, record):
        # Only process logs that are INFO or ERROR for console status
        if record.levelno == logging.INFO:
            # Check if it's the specific 'PASS' status message
            if record.getMessage().startswith("PASS:"):
                script_name = record.getMessage().split(':', 1)[1].strip().split(' ', 1)[0]
                self.console.print(f"[green]PASS: {script_name}[/green]")
        elif record.levelno == logging.ERROR:
            # Check if it's the specific 'FAIL' status message
            if record.getMessage().startswith("FAIL:"):
                script_name = record.getMessage().split(':', 1)[1].strip()
                self.console.print(f"[red]FAIL: {script_name}[/red]")
        

def logger_config(name=__name__, log_file=None, level=logging.DEBUG, rich_console: Console = None):
    """Setup logger with file logging always (DEBUG level), and minimal Rich console logging."""

    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    if log_file is None:
        log_file = f"{name}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # --- File Handler (Full Detail) ---
        # file_handler = logging.FileHandler(os.path.join(logs_dir, log_file), encoding='utf-8')
        file_handler = RotatingFileHandler(
            filename=os.path.join(logs_dir, log_file),
            mode='a',
            maxBytes=25*1024*1024,  # 25 MB
            backupCount=2,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            # "%(name)s.%(funcName)s:%(lineno)s | %(levelname)s | %(asctime)s | %(message)s",
            "%(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %I:%M%p"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # --- Rich Console Status Handler (Pass/Fail Only) ---
        if rich_console:
            rich_handler = RichConsoleStatusHandler(rich_console, level=logging.INFO)
            # rich_formatter = logging.Formatter("[red]%(levelname)s[/red] | %(message).40s")
            # rich_handler.setFormatter(rich_formatter)
            logger.addHandler(rich_handler)

    return logger

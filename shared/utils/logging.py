import logging

class Color:
    """This class contains ANSI escape sequences for colored output."""

    ENDC = "\033[0m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

class LogFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Color.BLUE,
        logging.INFO: Color.WHITE,
        logging.WARNING: Color.BRIGHT_YELLOW,
        logging.ERROR: Color.YELLOW,
        logging.CRITICAL: Color.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the string and set its color based on the log level"""
        return (
            self.FORMATS.get(record.levelno, Color.WHITE)
            + super().format(record)
            + Color.ENDC
        )


def init_logger() -> None:
    """Set the LogFormatter as a formatter for the global logger"""
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    console = logging.StreamHandler()
    formatter = LogFormatter(
        "[%(asctime)s %(name)s:%(lineno)d] %(levelname)s %(message)s"
    )
    console.setFormatter(formatter)
    assert len(logging.getLogger("").handlers) == 1
    logging.getLogger("").handlers = [console]

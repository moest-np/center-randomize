"""Custom logging module with some formatting."""

import sys
import logging.config
from os.path import abspath, dirname, join


MAX_LOGS_SIZE: int = 500000
ROOT_DIR: str = abspath(dirname(dirname(__file__)))
LOGS_TARGET: str = join(ROOT_DIR, "logs", "custom_logs.log")
CUSTOM_FILE_HANDLER_PATH = "utils.custom_file_handler.CustomFileHandler"


LOGGING_CONFIG: dict = {
    "version": 1,
    "formatters": {
        "standard": {
            "datefmt": "%y-%m-%d %H:%M:%S",
            "format": "🚀 %(asctime)s - %(name)s - %(levelname)s - %(message)s \n",
        },
        "error": {
            "datefmt": "%y-%m-%d %H:%M:%S",
            "format": "❌ %(asctime)s - %(name)s - %(levelname)s - %(message)s \n",
        },
    },
    "handlers": {
        "file_error": {
            "mode": "a",
            "level": "ERROR",
            "encoding": "utf-8",
            "formatter": "error",
            "filename": LOGS_TARGET,
            "class": CUSTOM_FILE_HANDLER_PATH,
        },
        "console_info": {
            "level": "INFO",
            "stream": sys.stdout,
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "console_error": {
            "level": "ERROR",
            "stream": sys.stderr,
            "formatter": "error",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "propagate": True,
            "handlers": ["file_error", "console_info", "console_error"],
        }
    },
}


# Call this once to initialize logger
def configure_logging() -> None:
    """Pass the logging configuration to logger."""
    logging.config.dictConfig(LOGGING_CONFIG)

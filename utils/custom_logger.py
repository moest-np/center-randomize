"""Custom logging module with some formatting."""

import os
import sys
import logging.config
from os.path import abspath, dirname, join, exists


ROOT_DIR: str = abspath(dirname(dirname(__file__)))
LOGS_DIR: str = join(ROOT_DIR, "logs")
LOGS_TARGET: str = os.path.join(LOGS_DIR, "custom_logs.log")
CUSTOM_FILE_HANDLER_PATH = "utils.custom_file_handler.CustomFileHandler"

if not exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

if not exists(LOGS_TARGET):
    with open(LOGS_TARGET, "a", encoding="utf-8") as file:
        os.utime(LOGS_TARGET, None)


LOGGING_CONFIG: dict = {
    "version": 1,
    "formatters": {
        "standard": {
            "datefmt": "%y-%m-%d %H:%M:%S",
            "format": "🚀 %(asctime)s - %(name)s - %(levelname)s - %(message)s \n",
        },
        "warn": {
            "datefmt": "%y-%m-%d %H:%M:%S",
            "format": "🔔 %(asctime)s - %(name)s - %(levelname)s - %(message)s \n",
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
        "console_warn": {
            "level": "WARN",
            "formatter": "warn",
            "stream": sys.stdout,
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
            "handlers": ["file_error", "console_info", "console_warn", "console_error"],
        }
    },
}


# Call this once to initialize logger
def configure_logging() -> None:
    """Pass the logging configuration to logger."""
    logging.config.dictConfig(LOGGING_CONFIG)

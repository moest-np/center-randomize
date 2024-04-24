"""Custom logging module with some formatting."""

"""
Use the CRITICAL level sparingly.
The logger.critical() invokes a blinking text in the console.
Limit usage for critical points where the program would not run 
"""

import os
import sys
import logging.config
from os.path import abspath, dirname, join, exists

ROOT_DIR: str = abspath(dirname(dirname(__file__)))
LOGS_DIR: str = join(ROOT_DIR, "logs")
LOGS_TARGET: str = join(ROOT_DIR, "logs", "custom_logs.log")
CUSTOM_FILE_HANDLER_PATH = "utils.custom_file_handler.CustomFileHandler"

if not exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

if not exists(LOGS_TARGET):
    with open(LOGS_TARGET, "a", encoding="utf-8") as file:
        os.utime(LOGS_TARGET, None)
        
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Colors
        start_yellow = "\x1b[33;20m"
        start_red = "\x1b[31;21m"
        start_bold_red = "\x1b[31;5m"   # This blinks in console for importance. USE CRITICAL SPARINGLY.
        start_purple = "\x1b[1;35m" # fun fact: my sister's fav color :)
        reset_colors = "\x1b[0m"
        
        original_format = self._style._fmt
        if record.levelno == logging.ERROR:
            self._style._fmt = "❌ "+ start_red + original_format + reset_colors  
            #DEBUG001 - uncomment the following line and COMMENT the above line to use the \n feature. If needed, add \n to other levels in a similar manner
            # self._style._fmt = "\n❌ "+ start_red + original_format + reset_colors  
        elif record.levelno == logging.WARN:
            self._style._fmt = "🔔 " + start_yellow + original_format + reset_colors  
        elif record.levelno == logging.INFO:
            self._style._fmt = "🚀 " + original_format 
        elif record.levelno == logging.CRITICAL:
            self._style._fmt = "❌ "+ start_bold_red + original_format + reset_colors +" ❌"
        elif record.levelno == logging.DEBUG:
            self._style._fmt = "\n---- " + start_purple + original_format + reset_colors + "----\n"
        formatted_message = super().format(record)
        self._style._fmt = original_format
        return formatted_message

# One formatter for console, another for file log
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "custom": {
            "()": CustomFormatter,
            "format": "%(levelname)-7s [%(asctime)s] in %(name)s :: %(message)s",
            "datefmt": "%y-%m-%d %H:%M:%S",
        },
        "standard": {
            "format": "%(levelname)-7s [%(asctime)s] in %(name)s :: %(message)s",
            "datefmt": "%y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "level": "WARNING",  # only log the WARNING level and above i.e. no INFO level logs on the file
            "formatter": "standard",
            "filename": LOGS_TARGET,
            "encoding": "utf-8",
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "custom",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
            "propagate": False,
        },
    },
}

# Call this once to initialize logger
def configure_logging() -> None:
    """Pass the logging configuration to logger."""
    logging.config.dictConfig(LOGGING_CONFIG)

"""Custom logging module with some formatting."""

import sys
import logging


def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create console handler and set level to info
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "🚀 %(asctime)s - %(name)s - %(levelname)s - %(message)s", "%y-%m-%d %H:%M:%S"
    )

    ch.setFormatter(formatter)

    logger.addHandler(ch)

    return logger

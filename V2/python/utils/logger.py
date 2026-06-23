"""Shared logging setup for TESSERACT Python scripts.

Logging is console-only and uses a consistent timestamped format across the
ingestion and exploration entry points.
"""

import logging
import sys


LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a standard console logger configured at INFO level."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)

    logger.propagate = False
    return logger

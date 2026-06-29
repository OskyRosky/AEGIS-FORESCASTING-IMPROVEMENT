"""Connectivity smoke test for TesseractEarthDW.

This script verifies that pyodbc can connect to the warehouse and execute a
minimal SELECT 1 query. It does not run automatically on import.
"""

from __future__ import annotations

import pyodbc

from config import build_connection_string
from utils.logger import get_logger


logger = get_logger("test_connection")


def test_connection() -> bool:
    """Connect to TesseractEarthDW and run SELECT 1."""

    try:
        logger.info("Testing database connectivity")
        with pyodbc.connect(build_connection_string()) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        if result and result[0] == 1:
            logger.info("Connection succeeded: SELECT 1 returned 1")
            return True

        logger.error("Connection failed: SELECT 1 returned an unexpected result")
        return False
    except pyodbc.Error as exc:
        logger.error("Connection failed with pyodbc error: %s", exc)
        return False
    except Exception as exc:
        logger.error("Connection failed with unexpected error: %s", exc)
        return False


if __name__ == "__main__":
    test_connection()

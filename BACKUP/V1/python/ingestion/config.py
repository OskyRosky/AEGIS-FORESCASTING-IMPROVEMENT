"""Database configuration for TESSERACT Stage 3 data ingestion.

The connection string uses Microsoft Entra ID authentication only. No passwords,
secrets, or user credentials are stored in code.
"""

from __future__ import annotations


SERVER_NAME = "tesseractearth.database.windows.net"
DATABASE_NAME = "TesseractEarthDW"
ODBC_DRIVER = "ODBC Driver 18 for SQL Server"

AUTH_ACTIVE_DIRECTORY_INTERACTIVE = "ActiveDirectoryInteractive"
AUTH_ACTIVE_DIRECTORY_INTEGRATED = "ActiveDirectoryIntegrated"
DEFAULT_AUTHENTICATION = AUTH_ACTIVE_DIRECTORY_INTERACTIVE


def build_connection_string(authentication: str = DEFAULT_AUTHENTICATION) -> str:
    """Build a pyodbc connection string for Azure SQL via Microsoft Entra ID."""

    return (
        f"Driver={{{ODBC_DRIVER}}};"
        f"Server=tcp:{SERVER_NAME},1433;"
        f"Database={DATABASE_NAME};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
        f"Authentication={authentication};"
    )

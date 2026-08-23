"""V6.24-P1 | SQL/Tesseract metadata read-only helper.

Single connection helper plus a query ledger. Every query executed by this stage
is recorded with its purpose, duration and row count.

READ-ONLY. No DDL, no DML, no bulk extraction.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pyodbc

SERVER = "tesseractearth.database.windows.net"
DATABASE = "TesseractEarthDW"
UID = "oscarau@microsoft.com"

OUT = Path(__file__).resolve().parent
LEDGER = OUT / "v6_24_p1_query_ledger.csv"

LEDGER_FIELDS = [
    "query_id", "metric", "object_name", "purpose", "query_type",
    "started_at", "status", "row_count_returned", "duration_seconds", "notes",
]

_conn = None
_ledger: list[dict] = []
_counter = 0


def connect():
    """Open the read-only connection.

    ActiveDirectoryInteractive works but its token cache expires within the
    session and then blocks indefinitely without surfacing a prompt.
    ActiveDirectoryIntegrated reuses the existing Windows/Entra session and is
    tried first; Interactive stays as the fallback.
    """
    global _conn
    if _conn is None:
        base = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{SERVER},1433;Database={DATABASE};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        attempts = [
            base + "Authentication=ActiveDirectoryIntegrated;",
            base + f"Authentication=ActiveDirectoryInteractive;UID={UID};",
        ]
        last = None
        for cs in attempts:
            try:
                _conn = pyodbc.connect(cs, timeout=30, readonly=True)
                return _conn
            except Exception as exc:
                last = exc
        raise RuntimeError(f"All auth modes failed: {last}")
    return _conn


def run(sql, *, metric, obj, purpose, qtype="metadata", params=(), notes=""):
    """Execute a read-only query and record it in the ledger."""
    global _counter
    _counter += 1
    qid = f"Q{_counter:03d}"
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    t0 = time.time()
    try:
        cur = connect().cursor()
        cur.execute(sql, params) if params else cur.execute(sql)
        rows = cur.fetchall()
        status, count = "OK", len(rows)
    except Exception as exc:
        rows, status, count = [], "FAILED", 0
        notes = (notes + " | " if notes else "") + str(exc)[:250]
    duration = round(time.time() - t0, 2)
    _ledger.append({
        "query_id": qid, "metric": metric, "object_name": obj,
        "purpose": purpose, "query_type": qtype, "started_at": started,
        "status": status, "row_count_returned": count,
        "duration_seconds": duration, "notes": notes,
    })
    print(f"{qid}|{status}|{duration}s|{count} rows|{obj}|{purpose}")
    return rows


def append_ledger_from(path):
    """Load a previously saved ledger so later scripts keep appending to it."""
    global _counter
    if not Path(path).exists():
        return
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            _ledger.append(row)
    _counter = len(_ledger)


def save_ledger():
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(_ledger)
    print(f"ledger_rows={len(_ledger)}")


def write_csv(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}|rows={len(rows)}")

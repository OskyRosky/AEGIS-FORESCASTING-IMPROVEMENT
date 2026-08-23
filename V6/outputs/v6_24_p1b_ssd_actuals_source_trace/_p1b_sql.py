"""V6.24-P1B | Read-only SQL helper with an auth-aware query ledger.

Every query is recorded with the authentication mode actually used, so that the
auth incident from P1 is traceable.

Budget guard: P1B is capped at 25 queries. The helper refuses to exceed it
without an explicit override.

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
BUDGET = 25

OUT = Path(__file__).resolve().parent
LEDGER = OUT / "v6_24_p1b_query_ledger.csv"

FIELDS = ["query_id", "auth_mode", "object_name", "purpose", "query_type",
          "started_at", "status", "row_count_returned", "duration_seconds", "notes"]

_conn = None
_auth_mode = "NOT_CONNECTED"
_ledger: list[dict] = []
_counter = 0


def connect():
    """Connect read-only.

    P1 established that ActiveDirectoryInteractive hangs indefinitely once its
    token cache expires, with no visible prompt. Integrated is therefore tried
    first with a 90 second ceiling, per the P1B auth rule.
    """
    global _conn, _auth_mode
    if _conn is not None:
        return _conn
    base = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    attempts = [
        ("ActiveDirectoryIntegrated", base + "Authentication=ActiveDirectoryIntegrated;"),
        ("ActiveDirectoryInteractive", base + f"Authentication=ActiveDirectoryInteractive;UID={UID};"),
    ]
    last = None
    for mode, cs in attempts:
        t0 = time.time()
        try:
            _conn = pyodbc.connect(cs, timeout=90, readonly=True)
            _auth_mode = mode
            print(f"AUTH_OK mode={mode} elapsed={round(time.time() - t0, 1)}s", flush=True)
            return _conn
        except Exception as exc:
            last = exc
            print(f"AUTH_FAIL mode={mode} {str(exc)[:120]}", flush=True)
    raise RuntimeError(f"All auth modes failed: {last}")


def run(sql, *, obj, purpose, qtype="metadata", params=(), notes="", allow_over_budget=False):
    """Execute one read-only query and record it in the ledger."""
    global _counter
    if _counter >= BUDGET and not allow_over_budget:
        raise RuntimeError(f"P1B query budget of {BUDGET} exhausted; justify explicitly to exceed")
    _counter += 1
    qid = f"P1B{_counter:03d}"
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
        "query_id": qid, "auth_mode": _auth_mode, "object_name": obj,
        "purpose": purpose, "query_type": qtype, "started_at": started,
        "status": status, "row_count_returned": count,
        "duration_seconds": duration, "notes": notes,
    })
    print(f"{qid}|{status}|{duration}s|{count} rows|{obj}|{purpose}", flush=True)
    return rows


def load_ledger():
    """Load prior rows so a follow-up script keeps appending rather than truncating.

    P1's ledger was destroyed because a follow-up script wrote without loading
    first. This is called at the top of every P1B script.
    """
    global _counter
    if not LEDGER.exists():
        return
    with LEDGER.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            _ledger.append(row)
    _counter = len(_ledger)
    print(f"ledger_loaded={_counter} prior queries", flush=True)


def save_ledger():
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(_ledger)
    print(f"ledger_rows={len(_ledger)} budget={BUDGET}", flush=True)


def write_csv(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}", flush=True)

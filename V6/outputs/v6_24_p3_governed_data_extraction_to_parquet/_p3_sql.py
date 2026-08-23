"""V6.24-P3 | Read-only SQL helper with an extraction-grade query ledger.

Ledger schema is the one required by the P3 brief:
query_id, source_object, purpose, selected_filter_summary, started_at, ended_at,
duration_seconds, rows_returned, status, notes.

Unlike P1/P2 this stage legitimately returns time-series rows, but every query
must still be filtered to the approved keys. No unbounded scans.
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
LEDGER = OUT / "v6_24_p3_query_ledger.csv"

FIELDS = ["query_id", "source_object", "purpose", "selected_filter_summary",
          "started_at", "ended_at", "duration_seconds", "rows_returned",
          "status", "notes"]

_conn = None
_auth = "NOT_CONNECTED"
_ledger: list[dict] = []
_n = 0


def connect():
    """Integrated first: Interactive hangs once its token cache expires."""
    global _conn, _auth
    if _conn is not None:
        return _conn
    base = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    for mode, cs in [
        ("ActiveDirectoryIntegrated", base + "Authentication=ActiveDirectoryIntegrated;"),
        ("ActiveDirectoryInteractive", base + f"Authentication=ActiveDirectoryInteractive;UID={UID};"),
    ]:
        t0 = time.time()
        try:
            _conn = pyodbc.connect(cs, timeout=90, readonly=True)
            _auth = mode
            print(f"AUTH_OK mode={mode} elapsed={round(time.time() - t0, 1)}s", flush=True)
            return _conn
        except Exception as exc:
            print(f"AUTH_FAIL mode={mode} {str(exc)[:120]}", flush=True)
    raise RuntimeError("All auth modes failed")


def fetch(sql, *, obj, purpose, filter_summary, params=()):
    """Run one filtered SELECT and return (columns, rows). Records the ledger row."""
    global _n
    _n += 1
    qid = f"P3Q{_n:03d}"
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    t0 = time.time()
    cols, rows, status, notes = [], [], "OK", f"auth_mode={_auth}"
    try:
        cur = connect().cursor()
        cur.execute(sql, params) if params else cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    except Exception as exc:
        status = "FAILED"
        notes = f"auth_mode={_auth} | {str(exc)[:250]}"
    dur = round(time.time() - t0, 2)
    _ledger.append({
        "query_id": qid, "source_object": obj, "purpose": purpose,
        "selected_filter_summary": filter_summary, "started_at": started,
        "ended_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "duration_seconds": dur,
        "rows_returned": len(rows), "status": status, "notes": notes,
    })
    print(f"{qid}|{status}|{dur}s|{len(rows)} rows|{obj}", flush=True)
    if status == "FAILED":
        raise RuntimeError(f"{qid} failed: {notes}")
    return cols, rows


def load_ledger():
    global _n
    if not LEDGER.exists():
        return
    with LEDGER.open(encoding="utf-8") as fh:
        _ledger.extend(csv.DictReader(fh))
    _n = len(_ledger)
    print(f"ledger_loaded={_n}", flush=True)


def save_ledger():
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(_ledger)
    print(f"ledger_rows={len(_ledger)}", flush=True)


def auth_mode():
    return _auth

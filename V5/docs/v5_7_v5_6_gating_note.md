# AEGIS V5.6 — Gating Note (from V5.7)

## Status: V5.6 is DEFERRED / GATED (not executed)

1. **V5.6 was not run.** No real refresh was executed in the container.
2. **V5.6 remains deferred/gated** until a future, explicit authorization.

## Reason
3. Real refresh requires **live SQL** ingestion, which uses
   `pyodbc` + ODBC Driver 18 against `TesseractEarthDW`, authenticated with
   **`ActiveDirectoryInteractive` (Entra + MFA)**. Interactive/MFA auth pops a
   browser/prompt and is **not compatible with a headless container**.

## Future options (a decision is required)
4. Pick one approved **non-interactive** auth strategy:
   - **device-code** flow,
   - **service principal** (secret/cert in a secret store, not in image/compose),
   - **managed identity** (only when hosted in Azure),
   - or another approved strategy.

## Scope guarantees
5. **V5.6 does NOT block V5.8.** The local Docker MVP can be closed without real
   refresh.
6. **V5.8 closes the local Docker MVP**, not real end-to-end refresh.
7. **Do NOT sell V5.8** as a system that ingests SQL and recalibrates models
   automatically. In V5, refresh is **validate-only**; real refresh is gated.

## If/when V5.6 is authorized
Real refresh must still follow the governed pipeline:
**staging → validate gates (32) → controlled promote → rollback**, with the
champion frozen and **no Shiny mutation**. The dashboard will keep consuming the
mounts read-only; there is never a refresh button in the dashboard.

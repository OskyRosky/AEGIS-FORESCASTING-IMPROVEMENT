# AEGIS V5.5 — Refresh Real Gating

## Status: real refresh remains GATED (deferred to V5.6+)

V5.5 validated the **architecture** of a separated refresh service. It did NOT
perform a real refresh. Real refresh stays gated for the reasons below.

## Why real refresh is not enabled

1. **Depends on SQL / Azure DB.** The real pipeline (`stage_ingestion` →
   `export_hdd_region`) queries `TesseractEarthDW` via `pyodbc` + ODBC Driver 18.
2. **Depends on Entra Interactive / MFA.** The connection uses
   `ActiveDirectoryInteractive`, which pops an interactive browser/MFA prompt —
   **incompatible with a headless container**.
3. **V5.5 validates architecture, not operation.** The refresh image has **no
   pyodbc**, so SQL is impossible by construction in this stage.
4. **V5.6 is deferred/gated.** Real refresh (SQL + models + controlled promote)
   is a separate, explicitly authorized future stage.

## What a future real refresh requires (decision needed)

- **Auth strategy** (pick one, approved): device-code flow, service principal
  (client secret/cert in a secret store, not in image/compose), or managed
  identity (only when hosted in Azure).
- The real refresh must still follow the governed pipeline:
  **staging → validate gates (32) → controlled promote → rollback**, with
  **no Shiny mutation** and the champion frozen.

## Hard constraints (unchanged)

- **No scheduler** yet (no cron, no Task Scheduler, no GitHub Actions).
- **No refresh button** in the dashboard; Shiny stays read-only.
- **No secrets** in the image; **no credentials** in Compose.
- data/raw is never mounted to the dashboard; refresh writes go through the
  governed promote path only (future), never directly from Shiny.

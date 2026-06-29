# VERSION_INFO

version_name = V4

version_role = active_project_root

project_container_root = C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT

active_project_root = C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V4

based_on = V3 (full controlled copy, 2026-06-29; .venv / __pycache__ / *.pyc excluded, recreatable)

current_status = V4 Phase 0 - baseline clone of closed V3 (parity validation)

next_stage = V4 Phase 1 - LLM explanation layer (evidence pack + provider seam)

next_block = Phase 0 close - confirm V4 starts identically to V3 from its own root

## Inherited State From V3 (CLOSED)

- V3 MVP is CLOSED (V3_MVP_CLOSED, 2026-06-29).
- Champion is frozen and governed = ETS Explicit (CHAMPION_SELECTED_WITH_CONDITIONS, median MASE 6.90 / RMSSE 1.86).
- 15-model canonical scope: 4 Growth + 5 Statistical + 3 ML + 3 DL (frozen reuse).
- Prohibited models (never execute): NBEATS, NHITS, FastNeuralAR_MLP (original).
- Last productive refresh promoted on 2026-06-28 (run_metadata run_timestamp 2026-06-28T17:27).

## V4 Objective

Add an AI / LLM explanation layer on top of the closed V3 core. The LLM only EXPLAINS already-governed artifacts (champion, tournament, risks, audit, accuracy, forecast, TTL). The LLM never computes, never sees raw data, never changes the champion.

## Active Root Rules

- All active work must happen inside V4 unless explicitly instructed otherwise.
- The parent folder is only a project container/version root.
- Historical artifacts must not be rewritten solely to change old path text.
- Shiny must remain read-only and must not recompute metrics or forecasts.
- The LLM layer must be read-only over a governed evidence pack; it must never compute, train, query raw data, or alter the champion.
- V1, V2 and V3 are frozen previous versions and must not be modified.

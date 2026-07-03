# VERSION_INFO

version_name = V5

version_role = active_project_root

project_container_root = C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT

active_project_root = C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V5

based_on = V4 (full controlled copy, 2026-06-30; .venv / __pycache__ / *.pyc excluded, recreatable)

current_status = V5.8 - Final Docker Closure Validation COMPLETE. V5_FINAL_DOCKER_VALIDATION_COMPLETED / V5_DOCKER_LOCAL_MVP_CLOSED / V5_READY_FOR_CONTAINER_DEMO

next_stage = NONE within V5 local MVP. V5.6 (real refresh in container) DEFERRED/GATED - needs non-interactive auth strategy. Azure / real refresh / scheduler / repo relocation require explicit new authorization.

next_block = V5 LOCAL DOCKER MVP CLOSED - no further V5 stage without explicit Oscar authorization

## Inherited State From V4 (CLOSED)

- V4 LOCAL MVP is CLOSED (V4_LOCAL_MVP_CLOSED / V4_READY_FOR_LOCAL_DEMO / V4_8R_UI_POLISH_COMPLETED, 2026-06-30).
- Champion is frozen and governed = ETS Explicit (CHAMPION_SELECTED_WITH_CONDITIONS, median MASE 6.90 / RMSSE 1.86).
- 15-model canonical scope: 4 Growth + 5 Statistical + 3 ML + 3 DL (frozen reuse).
- Prohibited models (never execute): NBEATS, NHITS, FastNeuralAR_MLP (original).
- LLM explanation layer present but read-only and mock-only (no real LLM, no Azure).

## V5 Objective

Package the closed V4 platform as the final local / containerized (Docker) version. V5 is packaging, deployment and refresh architecture only: it does NOT change forecasting or governance logic. No Azure, no real scheduler, no real LLM, no real refresh in this version. The Shiny dashboard stays a read-only consumer of governed artifacts; the LLM layer stays mock-only and read-only.

## Active Root Rules

- All active work must happen inside V5 unless explicitly instructed otherwise.
- The parent folder is only a project container/version root.
- Historical artifacts must not be rewritten solely to change old path text.
- Shiny must remain read-only and must not recompute metrics or forecasts.
- The LLM layer must stay read-only and mock-only; it must never compute, train, query raw data, or alter the champion.
- Do not build Docker, run SQL, run models, or run refresh without explicit per-stage authorization.
- V1, V2, V3 and V4 are frozen previous versions and must not be modified.

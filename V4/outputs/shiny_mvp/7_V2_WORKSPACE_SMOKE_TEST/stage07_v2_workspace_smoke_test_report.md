# Stage 07 — V2 Workspace Smoke Test Report

**Block:** Stage 07 — V2 Workspace Smoke Test (read-only validation)
**Active project root:** `C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V2`
**Date:** 2026-06-23
**Mode:** Read-only. No models, forecasts, tournaments, or metrics were run. V1 was not modified.

---

## 1. Objective
Validate that V2 is a working copy of V1 and confirm that all future Stage 07 work should happen only in V2. This is a passive smoke test: inspect structure, read artifacts, search for V1 path dependencies, launch the app from V2, and confirm pages are reachable.

## 2. Result
**Status: READY_FOR_OSCAR_REVIEW_V2_WORKSPACE_SMOKE_TEST** (1 benign warning).

V2 exists, mirrors the V1 project structure, the Shiny app launches from V2, the runtime root resolves to V2 (not V1), all key Shiny files and governed artifacts are present and readable, and every Stage 07 page is reachable in the DOM. The only warning is benign: copied historical reports/logs under `outputs/` still contain literal V1 paths (provenance text), which the live application does not depend on.

## 3. V2 Root Status
PASS — `...\AEGIS-FORESCASTING-IMPROVEMENT\V2` exists and contains the copied project structure (shiny_app, data, outputs, python, config, docs, scripts, tests, notebooks). V2 is a full copy of V1 (939 files / ~200 MB), with only the recreatable `.venv` excluded.

## 4. V2 Shiny App Status
PASS — `V2\shiny_app` present with `app.R`, `global.R`, `R/`, `ui/`, `server/`, `www/`, `modules/`.

## 5. Key Shiny Files Status
PASS — all checked files exist:
`app.R`, `global.R`, `R/helpers.R`, `ui/sidebar.R`, `ui/tabs.R`, `server/server.R`, `server/models_server.R`, `www/custom.css`.

## 6. Key Data Artifacts Status
PASS — all readable:
- `data/processed/forecast_viewer_model_outputs.csv` — 177,060 rows × 21 cols
- `data/processed/forecasts.csv` — 65,095 rows × 9 cols
- `data/processed/actuals.csv` — 84,537 rows × 7 cols

## 7. Tournament / Champion / Governance Artifacts Status
PASS — all readable:
- `tournament_model_scorecard.csv` — 13 × 17
- `tournament_pairwise_evidence.csv` — 78 × 16
- `tournament_entity_model_scores.csv` — 507 × 13
- `champion_decision.csv` — 1 × 9
- `model_lab_champion_summary.csv` — 1 × 11
- `champion_conditions_protocol.csv` — 5 × 11
- `champion_dashboard_language.csv` — 13 × 8

## 8. Hardcoded V1 Path Search
PASS (live source) / WARNING (historical copies).
- **Live Shiny source / config / pipeline:** no V1 filesystem dependency. The only `/v1/` hits in `shiny_app/R/ttl_provider.R` are the API-version URLs `/api/v1/calculate-ttl` (inactive API stub) — not a project path. `config/project_root_policy.json` points to V2 (`based_on_version: V1` is provenance metadata only).
- **Historical copies (benign warning):** literal V1 paths remain in copied build artifacts and docs, e.g. `docs/V1_ACTIVE_ROOT_POLICY.md`, `outputs/versioning_diagnostics/*`, `outputs/shiny_mvp/*/report.md` and `*_launch.csv`, and a historical `_diag_7_11B.R` under outputs. These recorded V1 paths at generation time and are not read by the running app. Per the do-not-rewrite-historical-artifacts policy, they were left untouched.
- **Runtime check:** `find_project_root()` resolved the loader root to `...\V2` and the app served real V2 data — confirming no accidental V1 usage at runtime.

## 9. Stage 07 Work Copied Into V2
PASS — confirmed present:
- Forecasting sidebar correction: Viewer / Accuracy / Forecast / TTL (4 distinct pages).
- Accuracy MVP page (`accuracy`).
- Models Universe page (`universe`).
- Models Tournament MVP page (`tournament`).
- Models Champion (Block A + Block B) page (`champion`) + `server/models_server.R`.
- Governance: Risks + Audit. Reference: Artifacts + Methodology + Version.
- Comparison page is intentionally absent (was removed in V1 as redundant).

## 10. Shiny Launch Details
- URL: `http://127.0.0.1:3838`
- Port: 3838
- PID: 36224
- HTTP status: 200 (LEN 144554)
- stdout log: `V2\outputs\shiny_mvp\v2_init\logs\v2_init_stdout.log`
- stderr log: `V2\outputs\shiny_mvp\v2_init\logs\v2_init_stderr.log`
- Stop command: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny_v1.ps1 -PidToStop 36224`
- Only benign preexisting warnings in stderr (vroom parsing notice); no errors.

## 11. Page Reachability (DOM data-section)
PASS — present: home, overview, explorer, accuracy, forecast, ttl, universe, tournament, champion, risks, audit, artifacts, methodology, version. ABSENT (expected): comparison.

## 12. Confirmations
- V1 NOT modified: PASS — no write operations against V1 in this block.
- No data artifacts modified: PASS — all artifact access was read-only.
- No Shiny source modified: PASS — no edits to `shiny_app` source in this block.
- No models / forecasts / tournaments / metrics run: PASS — none executed.
- Champion decision not changed: PASS — `champion_decision.csv` read-only; ETS Explicit unchanged.

## 13. Risks / Warnings
- WARNING (benign): historical V1 path strings remain inside copied reports/logs/docs under `outputs/` and `docs/`. No runtime impact; intentionally not rewritten.
- Note: launch helper scripts are still named `launch_shiny_v1.ps1` / `stop_shiny_v1.ps1`; the "v1" is a label only — they resolve their own folder via `$PSScriptRoot`, so the V2 copies launch V2 correctly. Optional future cleanup (rename) is cosmetic.

## 14. Recommended Next Step
Accept V2 as the active workspace. Proceed with Stage 07 dashboard decluttering/"more fluid" UI work in V2 only, page by page. Defer any cosmetic cleanup of historical V1 path strings and script filenames.

## 15. Final Status
**READY_FOR_OSCAR_REVIEW_V2_WORKSPACE_SMOKE_TEST**

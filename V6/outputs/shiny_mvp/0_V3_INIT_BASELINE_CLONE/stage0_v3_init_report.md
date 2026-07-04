# Stage 0 — V3 Init Baseline Clone

Date: 2026-06-25
Status: STAGE0_CLOSED (parity validated + visible version bumped to V3)
Active root after this stage: ...\AEGIS-FORESCASTING-IMPROVEMENT\V3

## 1. Objective
Create V3 as a faithful, isolated controlled clone of V2, validate that it starts
identically to V2 from its own root using its own data, and leave V3 as the active
workspace. No V3 feature work (daily job, LLM, new model, methodology docs,
architecture diagram) was implemented in this stage.

## 2. Decisions applied
- Micro-decision A: FULL clone of V2 -> V3 (complete parity; pruning deferred to a later stage).
- Micro-decision B: APP_VERSION label kept unchanged during the parity check;
  cosmetic bump to "V3" deferred to the end of Stage 0 (separate confirmed sub-step).

## 3. Clone operation
- Tool: robocopy /E (copy all subdirs) from V2 to V3.
- Exclusions (recreable junk only): .venv, __pycache__ (dirs), *.pyc (files).
- Launch logs were retained (negligible size, parity-safe).
- Result: 1158 files copied, 319 MB, 0 failed, 0 mismatched. Dirs: 301 copied, 5 skipped (excluded).
- V1 and V2 were NOT modified or deleted (clone is a copy operation into empty V3).

## 4. Root markers updated (inside V3 only)
- ACTIVE_PROJECT_ROOT.md -> points to ...\V3; declares V3 active, V1/V2 frozen.
- VERSION_INFO.md -> version_name = V3, based_on = V2 (2026-06-25), status = Stage 0.
- config/project_root_policy.json -> active_project_root = ...\V3, active_version = V3, based_on_version = V2.

## 5. Isolation verification
- find_project_root() (shiny_app/R/data_loader.R) resolves by walking up from getwd()
  to the nearest ACTIVE_PROJECT_ROOT.md. Launching from V3 -> resolves to V3.
- Confirmed RESOLVED_ROOT = ...\V3 (not V2).
- V3 reads its own data/ and outputs/ (data/processed and outputs/governance present in V3).

## 6. Startup validation
- Parse check: all shiny_app R files parse OK (PARSE_ALL_OK = TRUE).
- Launch: single clean instance from V3, PID 47140, port 3838.
- HTTP: http://127.0.0.1:3838 -> HTTP 200.
- Single listener on port 3838 (OwningProcess 47140).
- stderr: normal startup (package masks + pre-existing vroom parsing warning carried over from V2),
  ends with "Listening on http://127.0.0.1:3838". No fatal errors.

## 6b. Visible version bump (Micro-decision B, applied after parity sign-off)
- Oscar accepted parity. Cosmetic bump applied: shiny_app/R/constants.R APP_VERSION "V2" -> "V3".
- Only that single literal changed; no other constant, data artifact, model, forecast or champion touched.
- Confirmed APP_VERSION = V3 via Rscript. Relaunched single clean instance PID 46484 on port 3838 -> HTTP 200, single listener.
- Stage 0 CLOSED.

## 7. What was NOT done (deferred to later V3 stages)
- Stage 1: Methodology documents (project document + architecture diagram).
- Stage 2: AI explanation layer (provider abstraction none/mock/azure_openai/local).
- Stage 3: Replace FastNeuralAR_MLP (evaluate candidates + backtest; no auto champion change).
- Stage 4: Daily refresh orchestrator (local benchmark first, then Azure/internal scheduler).
- APP_VERSION cosmetic bump to "V3" (Micro-decision B; pending after parity sign-off).

## 8. Stop command
powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 46484

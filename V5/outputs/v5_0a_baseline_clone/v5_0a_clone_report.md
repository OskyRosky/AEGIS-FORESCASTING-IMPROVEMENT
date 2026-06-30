# AEGIS V5.0A — Baseline Clone Report

**Stage:** V5.0A — Baseline Clone from V4
**Date:** 2026-06-30
**Status:** `V5_0A_BASELINE_CLONE_COMPLETED`
**Source:** `...\AEGIS-FORESCASTING-IMPROVEMENT\V4` (V4_LOCAL_MVP_CLOSED)
**Target:** `...\AEGIS-FORESCASTING-IMPROVEMENT\V5`
**Dashboard:** http://127.0.0.1:3840 (PID 62892) — HTTP 200

---

## 1. Objective
Create V5 as a controlled copy of the closed V4 MVP, validate local parity, and prepare the V5 root for the subsequent Docker phases — **without building Docker yet** and without any change to forecasting or governance.

## 2. Pre-flight
- Confirmed project container root and presence of V1, V2, V3, V4.
- Read V4 root markers and the `find_project_root()` resolver. Resolver is **relative** (looks for `outputs/model_lab` + `shiny_app`, walks up to `ACTIVE_PROJECT_ROOT.md`); it does **not** read absolute paths from the policy JSON, so V5 resolves its own root once cloned.

## 3. Clone (robocopy, controlled)
- Command: `robocopy V4 V5 /E /MT:16 /R:1 /W:1 /XD .venv __pycache__ .Rproj.user .ipynb_checkpoints /XF *.pyc`
- Result: **2079 files copied, 504 dirs, 6 dirs skipped (excluded), 0 failed, 1.381 GB**, exit code 1 (success).
- Exclusions applied: `.venv`, `__pycache__`, `*.pyc`, `.Rproj.user`, `.ipynb_checkpoints`.

## 4. Parity check
- Tree compare (same exclusions both sides): **V4 = 2079, V5 = 2079, only_in_V4 = 0, only_in_V5 = 0**.
- SHA256 hash parity on governed artifacts: `model_champion_comparison.csv`, `model_universe_canonical.csv`, `run_metadata.csv` → **IDENTICAL**.

## 5. Root markers updated to V5
- `ACTIVE_PROJECT_ROOT.md` → active root = `...\V5`; V1–V4 declared frozen; V5 = final local/containerized version.
- `VERSION_INFO.md` → `version_name = V5`, `active_project_root = ...\V5`, `based_on = V4 (2026-06-30)`, `current_status = V5.0A`, `next_stage = V5.0B`; inherited state from V4 (CLOSED); V5 objective + root rules.
- `config/project_root_policy.json` → `active_version = V5`, `based_on_version = V4`, `active_project_root = ...\V5`; **valid JSON**.
- Code scan: **no absolute `\V4` path leakage** in V5 runtime code (`.R/.json/.yaml/.py`).

## 6. Dashboard smoke (port 3840)
- HTTP **200**; content 303,501 bytes; "Listening on http://127.0.0.1:3840".
- Champion **ETS Explicit** present (x90). Scope **15 governed models** / **15 models**. Horizons **30 / 60 / 180 days**.
- **10 assistants** (`Generate explanation` x10). All navigation tabs present (Home, Overview, Universe, Tournament, Champion, Forecast, Accuracy, Risks, Audit, Methodology).
- Logs: no critical errors (only a benign readr parsing warning, identical to V4); pandoc 3.10 active.

## 7. Invariants preserved
Champion frozen (ETS Explicit), 15-model scope, prohibited models not executed, LLM mock-only, Shiny read-only. No SQL / no models / no refresh / no Docker / no Azure / no real LLM run. `data/processed` and `data/raw` unchanged (hash parity). V1/V2/V3/V4 untouched. Backups preserved.

## 8. Outcome
All Definition-of-Done checks **PASS**. V5 is a faithful, self-rooting controlled clone of the closed V4 MVP, running locally on a distinct port.

**Next stage (requires explicit authorization):** V5.0B — Docker Readiness Audit + Reproducibility Decisions.

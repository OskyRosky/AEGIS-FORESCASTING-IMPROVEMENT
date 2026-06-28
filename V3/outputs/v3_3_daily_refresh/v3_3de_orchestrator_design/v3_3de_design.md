# V3.3D/E — Daily Refresh Orchestrator + Staging/Promote + Last Update/Pipeline Status

**Status:** `DESIGN ONLY — NOT IMPLEMENTED`
**Authoring date:** 2026-06-28
**Authorized scope:** design document only (D/E). No productive code, no real promotion, no
scheduler, no champion auto-promotion, no V3.3F, no V4, no changes to V1/V2.
**Promotion strategy preference (Oscar):** `robocopy /MIR` with prior backup, retries,
post-promotion validation, and rollback from backup. **No** folder swap / rename.

This document specifies the design of two gated modules:
- **V3.3D** — Daily Refresh Orchestrator + Staging → Validate → Promote (gated).
- **V3.3E** — Last Update + Pipeline Status contracts written **only after** full success.

Champion stays frozen (`ETS Explicit`). The daily job produces candidate / for-review
artifacts only; it never auto-promotes a champion. The 3 prohibited models
(NBEATS, NHITS, FastNeuralAR_MLP original) are never imported or executed.

---

## 0. Why staging→promote (vs the benchmark's backup→run→restore)
V3.3B-2 proved the 15-model pipeline runs S00–S14 in ~18 min wall-clock by **backing up
production, running real stages, then restoring** (Option A) so production ended unchanged.
That validated *runtime*, but it never updates the dashboard. V3.3D inverts the safety model:

> Run everything in an isolated **staging tree** → validate against gates → **only if every
> gate passes, promote** staging into `data/processed` (and the read artifacts the dashboard
> consumes). If anything fails, production is **never touched** and stays intact.

This removes the fragile mid-run mutation of `data/processed` and confines the only
production write to a single, validated, atomic-ish promote step using `robocopy /MIR`
with a fresh backup taken immediately before promote (rollback source).

---

## 1. What runs in staging
The orchestrator reuses the **same S00–S14 stages already proven in V3.3B-2**, but redirects
every model/forecast/governance write to a per-run staging root:

```
outputs/v3_3_daily_refresh/v3_3d_run_<YYYYMMDD_HHMM>/
  staging/            # everything the run produces (mirrors data/processed + outputs subset)
  backup_pre_promote/ # snapshot of production taken right before promote (rollback source)
  logs/               # per-stage logs S00..S14
  runtime/            # stage_runtime_summary.csv, model_execution_summary.csv
  status/             # last_update, pipeline_status, champion_behavior, prohibited_guard
  validation/         # gate results (29 checks + scope + guards)
  reports/            # v3_3d_run_report.md
```

Stages run in staging:
- **S00** Auth / VPN / SQL gate (precheck; PASS required to proceed).
- **S01** Ingestion (live SQL → `staging/data_raw/`).
- **S02** Transform / data contract (→ `staging/processed/`).
- **S03a** Baseline / growth / stat / ML generation (12 live-fit; staging only).
- **S03b** Clean challenger live-fit (5, torch-free clean entrypoint; staging only).
- **S03c** DL frozen reuse (3, no training; staging only).
- **S04** Forecast outputs / viewer handoff (→ staging).
- **S05** Tournament + champion **decision artifacts** (candidate only; champion frozen).
- **S06** Canonical universe (R).
- **S07** Evaluation exports.
- **S08** Governance exports.
- **S09** Reference refresh (ttl_* snapshots).
- **S10** Dashboard consolidation.
- **S11–S13** Observations (last update, pipeline status, champion audit) — staging copies.
- **S14** Validation gates. **Promote happens only if S14 = all PASS.**

Production directories are **read** as inputs where needed but **never written** until promote.

---

## 2. What gets promoted to data/processed (and read artifacts)
Promotion target set is exactly the directories the dashboard consumes (see
`v3_3de_promotion_plan.csv` for the file-level contract). Two tiers:

**Tier P1 — PROMOTE (production consumed by dashboard):**
- `data/processed/` — forecasts.csv, actuals.csv, entities.csv, run_metadata.csv,
  forecast_viewer_model_outputs.csv, forecasts_with_intervals_relative*.csv,
  model_universe_canonical.csv, ttl_* snapshots, model_evaluation_*.csv.
- `outputs/model_lab/forecast_viewer_handoff/`
- `outputs/model_lab/tournament_engine/`
- `outputs/model_lab/champion_decision/` (candidate decision; champion stays ETS Explicit)
- `outputs/evaluation/`
- `outputs/governance/`

**Tier A1 — AUDIT ONLY (never promoted):** run logs, runtime CSVs, validation CSVs,
staging copies, backup_pre_promote, prohibited_guard, fit_plan/fit_result. These remain
under `v3_3d_run_<ts>/` as the audit trail and are not copied into production.

Each promote uses: `robocopy <staging\dir> <prod\dir> /MIR /R:4 /W:2 /NFL /NDL /NJH /NJS /NP`.
Pre-promote backup is taken with the identical `/MIR` mechanism into `backup_pre_promote/`.

---

## 3. Dashboard artifacts updated
- **forecasts / viewer / intervals** drive Forecasting (Viewer, Forecast, Accuracy).
- **tournament_engine + champion_decision** drive Models (Universe, Tournament, Champion).
- **governance/evaluation** drive Governance.
- **run_metadata.csv** drives the header **Last update** badge — only this file moving makes
  the dashboard report a new refresh. It is written **last** and only after promote success.

## 4. What stays as audit artifact only
Everything in Tier A1 §2. The dashboard never reads `v3_3d_run_<ts>/`; production is the
single source of truth. Pipeline status + run report are audit, not consumed by Shiny.

---

## 5. Validation gates before promote (all must PASS)
Reuses the 29 V3.3B-2 checks + extends. Full list in `v3_3de_validation_plan.csv`. Hard gates:
1. S00 SQL/auth PASS.
2. 15-model canonical scope present (4 growth + 5 stat + 3 ML + 3 DL).
3. Prohibited guard: NBEATS / NHITS / FastNeuralAR_MLP absent from every staged output.
4. S01–S08 completed, 0 FAILED, row counts within tolerance (e.g. 13,620/model; 12 live + 3 reuse).
5. Champion unchanged = ETS Explicit (compare staging vs production canonical).
6. No NaN/negative-forecast breaches beyond contract; intervals 80% present 1-30.
7. Staging file inventory matches promotion contract (no missing P1 file).
If **any** fails → **abort promote**, leave production intact, write FAIL status, exit non-zero.

## 6. Failure of S01/S03/S05/S08/S10
- **S01 (ingestion):** abort. No transform, no promote. Prod intact. status=INGEST_FAIL.
- **S03 (model gen):** abort. Stale-but-consistent prod preserved. status=MODEL_FAIL.
- **S05 (tournament/champion):** abort. If champion would change → hard stop. status=CHAMPION_GUARD_FAIL.
- **S08 (governance):** abort. status=GOVERNANCE_FAIL.
- **S10 (dashboard consolidation):** abort before promote. status=DASHBOARD_FAIL.
All are pre-promote, so rollback is trivial: production was never written.

## 7. Rollback strategy
Promote order: backup prod → P1 robocopy promotes → post-promote validation → write Last
Update. If post-promote validation fails, restore each P1 dir from `backup_pre_promote/`
via `robocopy /MIR` (lock-tolerant, OneDrive-safe per V3.3B-2 lesson). Verify mirror rc=0.
Never rmtree+copytree. Last Update only written after rollback decision = no-rollback.

## 8. Last Update only after full success
`run_metadata.csv` (run_timestamp) is promoted last; pipeline_status set REFRESH_COMPLETED.
If anything failed, run_metadata is not promoted; dashboard keeps the previous timestamp.

## 9. pipeline_status.csv
Columns: run_id, started_at, finished_at, duration_min, stages_passed, stages_failed,
validation_result, champion_before, champion_after, champion_changed, promoted(bool),
rolled_back(bool), final_status. Audit only.

## 10. Champion frozen confirmation
S05 produces candidate decision; S13 compares staging vs prod canonical; gate fails if
champion ≠ ETS Explicit. promotion_performed_for_champion=NO always.

## 11. Prohibited model confirmation
Clean entrypoint never imports the registry. S14 text-scans staged outputs; presence → FAIL.

## 12. No partial dashboard
Single gated promote; all-or-nothing; backup+rollback; Last Update last → never partial.

## 13. Exact commands (dry-run / validate / execute-staging / promote)
```
# dry-run (no fit, prints plan)
python python/model_lab/run_daily_refresh_orchestrator.py --dry-run
# execute staging (gated, no promote)
python python/model_lab/run_daily_refresh_orchestrator.py --execute --allow-execute --no-promote
# validate only
python python/model_lab/run_daily_refresh_orchestrator.py --validate-only --run-dir <run>
# promote (requires both flags; gated)
python python/model_lab/run_daily_refresh_orchestrator.py --promote --allow-promote --run-dir <run>
```

## 14. Closing outputs
v3_3de_design.md, artifact_contract.csv, promotion_plan.csv, validation_plan.csv,
failure_modes.csv, test_plan.csv. Final status: `V3_3DE_DAILY_REFRESH_ORCHESTRATOR_DESIGN_COMPLETED`.

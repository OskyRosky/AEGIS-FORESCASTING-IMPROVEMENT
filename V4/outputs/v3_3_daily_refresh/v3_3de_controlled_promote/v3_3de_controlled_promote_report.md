# V3.3D/E-2 — Controlled Promote Report

**Final status:** V3_3DE_CONTROLLED_PROMOTE_COMPLETED
**Date:** 2026-06-28
**Source staging run:** `v3_3de_run_20260628_172644` (full staging, 32/32 gates)
**Backup:** `outputs/v3_3_daily_refresh/v3_3de_controlled_promote/backups/pre_promote_20260628_201215/`

## What happened
Promote-only. No SQL ingestion, transform, model fit, scheduler, VPN, or email re-run.
The validated candidate artifacts from the last successful full staging run were promoted
to production with a pre-promote backup. `run_metadata.csv` was promoted **last** so
Last Update only advances if everything else promoted cleanly.

## Promotion
- Backup: data/processed + forecast_viewer_handoff + tournament_engine + champion_decision + evaluation + governance (robocopy /MIR into backup).
- Promote (robocopy /R:4 /W:2, file-level, no /MIR on prod): actuals.csv, entities.csv, forecast_comparison.csv, forecasts.csv -> then run_metadata.csv LAST.
- run_metadata_pipeline.csv (9-field audit) copied as audit alongside dashboard 12-field contract.
- data/raw NOT promoted (audit-only, unchanged). Champion NOT promoted (frozen ETS Explicit).

## Last Update
- Prod run_metadata run_timestamp: 2026-06-10 -> 2026-06-28T17:27:14. Dashboard reflects promoted run.

## Closure table
| Area | Status | Notes |
|---|---|---|
| Stage completion | COMPLETED | promote-only |
| Source staging run selected | PASS | v3_3de_run_20260628_172644 |
| Source run was full staging | PASS | full, not smoke |
| Source run 32 gates | PASS | 32/32 |
| Backup pre-promote | PASS | pre_promote_20260628_201215 |
| Promote executed | PASS | 5 processed artifacts |
| robocopy used | PASS | /R:4 /W:2 file-level, /MIR for backup |
| data/processed promoted | PASS | updated from candidate |
| Dashboard artifacts promoted | PASS | forecasts/actuals/entities/comparison |
| run_metadata promoted last | PASS | last step |
| Last Update updated | PASS | 6/10 -> 6/28 |
| pipeline_status audit preserved | PASS | run_metadata_pipeline.csv |
| data/raw productive unchanged | PASS | unchanged |
| Champion frozen | PASS | ETS Explicit |
| Prohibited models absent | PASS | no NBEATS/NHITS/FastNeuralAR |
| V1/V2 untouched | PASS | unchanged |
| Rollback needed | NO | postcheck all PASS |
| Post-promote validation | PASS | 6/6 |
| Files created | YES | promote CSVs + reports |
| Files modified | YES | data/processed/* |
| Next step | H final validation (await explicit auth) | not started |
</content>
</invoke>

# V3.3D/E — Implementation Prompt (APPROVED, gated)

**Status:** APPROVED to prepare. Design approved conceptually by Oscar (2026-06-28) with two
adjustments incorporated. Implementation execution still requires explicit per-step authorization.

## Scope
Implement `python/model_lab/run_daily_refresh_orchestrator.py` (S00–S14 staging → 32-gate
validate → promote) with backup + rollback. Staging-only by default; promote behind double flags.

## Modes
- `--dry-run` plan only, no writes.
- `--execute --allow-execute --no-promote` run real S00–S14 into run-dir staging; validate; NO promote.
- `--validate-only --run-dir R` regenerate gate report.
- `--promote --allow-promote --run-dir R` backup → robocopy /MIR P1 → post-promote validate → run_metadata last; rollback on fail.

## Adjustment 1 — Pipeline status (DUAL)
- Keep `pipeline_status.csv` audit-only (full history).
- Promote minimal dashboard status via `data/processed/run_metadata.csv` (extended), written
  LAST after all gates pass + all other P1 promoted. Required fields: last_successful_refresh_timestamp,
  pipeline_status, total_runtime_minutes, model_scope_count, champion_model, validation_status,
  promoted_run_id, source_data_date, notes. Gate G30 verifies fields complete.

## Adjustment 2 — Raw traceability
- S01 raw snapshot stays in `v3_3d_run_<ts>/data_raw/` (audit). Gate G31 verifies retained.
- `data/raw` production audit-only, NOT mutated (gate G32) unless explicitly tiered P1.
- run_metadata source_data_date + promoted_run_id trace raw → processed.

## Hard constraints (unchanged)
robocopy /MIR + backup + rollback; 32 gates hard-block before promote; run_metadata promoted
last; champion frozen ETS Explicit; prohibited guard; NO scheduler; NO V3.3F; NO V4; NO V1/V2.
data/raw prod not mutated. Promote requires both --promote AND --allow-promote.

## Refs
design.md, artifact_contract.csv (P1+raw audit), promotion_plan.csv (16 steps), validation_plan.csv
(G01-G32), failure_modes.csv, test_plan.csv (T01-T17).

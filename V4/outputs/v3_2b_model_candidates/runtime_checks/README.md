# runtime_checks/

Results of the MANDATORY runtime gate (subset dry-run) that every candidate must pass
BEFORE any full backtest.

- `runtime_gate_results.csv` — candidate_id, stage (subset|full), n_series, n_windows,
  runtime_seconds, runtime_per_series, gate_threshold_seconds, gate_status
  (PASS|FAIL|NOT_VIABLE_FOR_V3_DAILY_REFRESH), failure_reason.
- Written by the V3.2C harness ONLY. Empty until V3.2C runs.

Gate policy (see ../runtime_risk_assessment.md):
- Subset dry-run target: <= 3-5 minutes total.
- Candidate approaching ~30 min => NOT_VIABLE_FOR_V3_DAILY_REFRESH (deferred, not run full).

# V3.2B — Backtest Plan (Model Candidate Experimental Harness)

**Scope:** V3 only. Experimental. No champion change, no promotion, no production-artifact writes.
**Status:** PLAN ONLY — execution happens in V3.2C after explicit authorization.

This plan defines exactly how candidate models will be evaluated in V3.2C so the comparison
against the governed champion (ETS Explicit) and baselines is fair, reproducible, and
runtime-bounded.

---

## 1. Series to evaluate

- Same governed universe used in V3.2A: the **39 backtest-eligible series** that already have
  multi-model backtest coverage (the series present in
  `outputs/model_lab/tournament_engine/tournament_entity_model_scores.csv` /
  `data/processed/forecast_viewer_model_outputs.csv`).
- **Subset dry-run:** a fixed, deterministic sample of **5 series** spanning easy + hard cases,
  including at least one multi-tenant high-scale series where the current FastNeuralAR_MLP
  collapsed (e.g. NAM-Multitenant, EUR-Multitenant) plus a well-behaved series (e.g. NAM-TDF).
- **Full backtest:** all 39 series — only for candidates that PASS the runtime gate.
- The 6 actuals-only series (AUT/CHL/DNK/EUR/IDN/MYS-Go Local) are excluded from candidate
  fitting exactly as in the governed handoff (no multi-model backtest coverage).

## 2. Horizons

- **h1..h30** (daily), identical to the governed backtest grain. No 31-60 (no governed
  evidence beyond 30 in V3; matches V3.2A finding).
- Direct multi-horizon candidates emit all 30 horizons per origin in one shot (no recursion).

## 3. Splits (walk-forward)

- Re-use the governed walk-forward design: expanding-window walk-forward, **12 windows**,
  `MIN_TRAIN=365`, step aligned to the existing harness (`config/backtesting.yaml`,
  `forecast_horizon_days: 30`).
- Same train cutoffs / test windows for EVERY candidate and for the champion/baseline anchors,
  so deltas are apples-to-apples.
- Subset dry-run may use a reduced window count (e.g. 3 windows) purely to measure runtime;
  full backtest uses all 12.

## 4. Metrics

- **Primary:** median MASE (lower better). **Guardrail:** median RMSSE.
- **Secondary:** sMAPE, wMAPE, signed bias, negative_forecast_count.
- **Operational:** runtime_seconds (subset and full), runtime_per_series.
- MASE/RMSSE computed against the SAME seasonal-naive in-sample scale the governed tournament
  uses, so candidate numbers sit on the same axis as the V3.2A scorecard.
- All metric rows conform to `experiment_contract.csv`.

## 5. Champion / baseline comparisons

- Anchors (NOT re-fit, NOT modified): champion **ETS Explicit** (MASE 6.90 / RMSSE 1.856) and
  the existing baselines from `tournament_model_scorecard.csv` (AutoARIMA 8.09, Theta 10.64,
  current LightGBM 16.04, current XGBoost 14.55, FixedGrowth_*).
- The failing **FastNeuralAR_MLP (current)** (MASE 739.92) is kept as the "model to beat".
- A candidate is interesting only if it materially beats the current FastNeuralAR_MLP AND is
  competitive with the mid-pack baselines; champion-level performance is the stretch goal.

## 6. Runtime measurement

- Wall-clock per candidate, per stage (subset, full), and per series where feasible.
- Recorded in `runtime_checks/runtime_gate_results.csv` and echoed into the per-row
  `runtime_seconds` of `experiment_contract.csv`.
- Environment captured: CPU-only (torch 2.12.0+cpu, CUDA not available), single process.

## 7. Failure handling

- If a candidate errors during fit/predict: status=`failed`, failure_reason recorded, candidate
  marked and SKIPPED for full backtest. No retry-loop, no silent fallback.
- If a candidate exceeds the runtime gate: status=`deferred`,
  failure_reason=`NOT_VIABLE_FOR_V3_DAILY_REFRESH`, excluded from full backtest.
- Partial results are kept and clearly labeled; never extrapolated.

## 8. Guardrails

- **Non-negativity:** every candidate clamps forecasts to >= 0; negative_forecast_count must be 0
  after clamp (raw negatives, if any, are logged before clamp).
- **MASE/RMSSE guardrails:** reuse the governed guardrail thresholds; a candidate failing
  guardrails is reported but NOT promoted.
- **Stability:** flag any candidate whose error grows pathologically with horizon (the recursive
  collapse signature) — direct multi-horizon design is the primary mitigation.

## 9. Promotion criteria (for later governance review — NOT executed here)

A candidate may be RECOMMENDED for governance review (still no auto-promote) only if ALL hold:
1. Passes runtime gate (viable for a future daily refresh).
2. negative_forecast_count == 0 after clamp.
3. Median MASE materially better than current FastNeuralAR_MLP AND within competitive range of
   mid-pack baselines.
4. Guardrails pass or are clearly explained.
5. Stable across horizons (no recursive-collapse signature).
Promotion itself remains a separate, Oscar-authorized governance step.

## 10. Rejection criteria

A candidate is REJECTED or DEFERRED if any hold:
- Runtime gate fail / approaches ~30 min (`NOT_VIABLE_FOR_V3_DAILY_REFRESH`).
- Persistent negative forecasts after clamp, or numeric instability.
- No material improvement over the current FastNeuralAR_MLP.
- Dependency unavailable or non-reproducible.

## 11. Determinism

- Fixed random seed (42) for all stochastic candidates (torch, sklearn, LightGBM, XGBoost).
- Same series order, same windows, same horizons across candidates.

# Challenger Onboarding Report - Stage 5.28

Created timestamp: 2026-06-12T15:07:26
Run id: challenger_onboarding_20260612_150726

## Purpose of the Block

Block 5.28 formally registers and prepares the seven planned challenger models
for future execution. It is onboarding only: no challenger is trained, no
forecast is generated, no MASE/RMSSE is calculated, no ranking is built, no
tournament output is produced, and no champion is selected. Every challenger
remains `official_execution_ready = false` because execution belongs to a later
block.

## Models Onboarded

| challenger_id | model_name | model_family | model_type | leakage_risk_level | runtime_class | sandbox_ready | official_ready |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CH-01 | AutoARIMA | statistical | auto_arima | low | medium | False | False |
| CH-02 | Theta | statistical | theta | low | light | False | False |
| CH-03 | ETS Explicit | statistical | ets_explicit | low | light | False | False |
| CH-04 | LightGBM | machine_learning | gradient_boosting | medium | medium | False | False |
| CH-05 | XGBoost | machine_learning | gradient_boosting | medium | medium | False | False |
| CH-06 | NBEATS | deep_learning | neural_basis_expansion | high | heavy | False | False |
| CH-07 | NHITS | deep_learning | neural_hierarchical_interpolation | high | heavy | False | False |

- Statistical challengers: 3 (AutoARIMA, Theta, ETS Explicit)
- Machine learning challengers: 2 (LightGBM, XGBoost)
- Deep learning challengers: 2 (NBEATS, NHITS)

## Dependency Findings

- Distinct dependencies inspected: 8
- Distinct dependencies available in current environment: 0
- Challengers with no available backend dependency: 7
- Models missing a sandbox dependency: AutoARIMA, ETS Explicit, LightGBM, NBEATS, NHITS, Theta, XGBoost

Dependency availability was checked using safe import-spec inspection only. No
packages were installed. Missing dependencies are recorded as informational and
do not block onboarding; they keep `sandbox_ready = false` for the affected
challenger and have no effect on `official_execution_ready`, which is false for
all challengers in this block.

## Readiness Findings

- Planned challengers: 7
- Registered challengers: 7
- Sandbox-ready challengers: 0
- Official-execution-ready challengers: 0 (must be 0)
- Onboarding-blocking models: 0

Every challenger is registered, has dependencies checked, has leakage controls
mapped, has its tuning policy declared, and has its hyperparameter-space status
declared (metadata only).

## Leakage-Control Mapping

All leakage controls from the Stage 5.26 No-Tuning-Leakage Contract are mapped to
every challenger. Total control mappings: 84 rows across
7 challengers and
12 distinct controls. Each control is
recorded with status `mapped_pending_official_verification` because verification occurs at execution
time, not during onboarding.

## Sandbox vs Official Execution Policy

See `challenger_execution_mode_policy.md`. Sandbox mode is exploratory and cannot
be promoted to official evidence. Official mode requires locked configuration,
windows, features, and seeds, no post-hoc tuning, and full audit metadata.

## Why Official Execution Remains False

Official execution requires completed preregistration, verified leakage controls,
recorded dependencies, locked reproducibility metadata, and audit review. None of
these execution-time gates are performed in an onboarding block, so all
challengers remain `official_execution_ready = false`.

## What Remains for 5.29

- Lock per-challenger hyperparameter spaces and tuning budgets.
- Resolve or record any missing dependencies required for execution.
- Define the challenger execution plan (sandbox first, then official).
- Verify leakage controls at execution time against locked windows.
- Capture full reproducibility metadata for official runs.

## Recommendation

PROCEED_TO_5.29_CHALLENGER_EXECUTION_PLANNING

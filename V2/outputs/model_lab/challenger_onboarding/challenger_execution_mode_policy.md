# Challenger Execution Mode Policy - Stage 5.28

Created timestamp: 2026-06-12T15:07:26

## Purpose

This policy governs how the seven onboarded challengers may be executed in
future blocks. Block 5.28 is onboarding only. No challenger is trained, no
forecast is generated, no metric is calculated, and no challenger is promoted to
official execution in this block.

## Sandbox Mode Definition

`sandbox_mode` is an exploratory mode used to verify code stability, data
plumbing, and dependency wiring for a challenger. Sandbox runs:

- are not eligible for champion decisions;
- cannot be promoted to official tournament evidence;
- cannot be used as official benchmark evidence;
- require at least one usable backend dependency to be present.

## Official Mode Definition

`official_mode` is the formal comparison mode. It requires locked configuration,
locked backtesting windows, locked features, locked random seeds, no post-hoc
tuning, and full metadata capture for audit. Official mode is used only for
formal benchmark comparison against the baseline cohort.

## Why Official Execution Remains False

Every onboarded challenger has `official_execution_ready = false` in this block
because official execution belongs to a later block (5.29 and beyond).
Onboarding only registers the challengers, checks dependency availability, maps
leakage controls, and declares tuning and hyperparameter-space policy. No model
has been run, locked, or audited for official comparison.

## No-Tuning-Leakage Requirement

All challenger tuning must obey the Stage 5.26 No-Tuning-Leakage Contract.
Tuning may occur only through an inner-validation process using training-only
data. Official MASE, official RMSSE, statistical significance outputs, tournament
rank, and champion-selection feedback must never be used for tuning.

## Model Preregistration Requirement

Before official execution, each challenger must complete preregistration:
`model_name`, `model_family`, `allowed_features`, `hyperparameter_space`,
`tuning_budget`, `training_window_policy`, `random_seed_policy`,
`dependency_requirements`, `expected_runtime_class`, and `leakage_risk_level`.

## Dependency Requirement

A challenger may not enter sandbox or official execution unless its required
dependencies are available and recorded. Dependency availability is checked in
this block via safe import-spec inspection only; no packages are installed.

## Reproducibility Requirement

Every official challenger run must record `run_id`, git status, config snapshot,
input data hashes if available, random seeds, dependency versions if available,
a model registry snapshot, and the execution timestamp.

## Denominator Note

MASE and RMSSE use the official training-only lag-1 naive denominators:

- MASE denominator: training-only lag-1 naive MAE,
  `mean(abs(y_train[t] - y_train[t-1]))`.
- RMSSE denominator: training-only lag-1 naive MSE,
  `mean((y_train[t] - y_train[t-1])^2)`.

The denominator is computed per entity and window using only actuals with date
`<= train_end_date`. It is never computed on the test horizon.

## Interpretation Note

The corrected MASE scale may be high because the denominator is an
in-sample one-step lag-1 naive error rather than an out-of-sample flat naive.
A 30-day horizon model error divided by a small in-sample one-step error can
yield MASE values well above 1. This is expected and methodologically standard;
it is not a defect. The same logic applies to the RMSSE guardrail scale.

## Scope Boundary

This block creates no champion, no tournament output, and no ranking. Challenger
execution, metric calculation, ranking, and champion selection are explicitly
deferred to later blocks.

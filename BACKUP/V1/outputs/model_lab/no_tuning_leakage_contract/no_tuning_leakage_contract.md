# No-Tuning-Leakage Contract - Stage 5.26

Created timestamp: 2026-06-12T14:14:07

## Purpose

This contract governs all future challenger models for TESSERACT v2 / AEGIS Forecast Improvement Platform. Its purpose is to prevent tuning leakage from test windows, future actuals, benchmark results, MASE/RMSSE outcomes, statistical significance outputs, tournament outputs, and champion-selection feedback.

## Scope

The contract applies to all future challenger onboarding, sandbox execution, official execution, feature generation, hyperparameter tuning, metadata capture, and audit review. It does not register or execute challengers in this block.

## Allowed Future Challenger Families

- AutoARIMA
- Theta
- ETS Explicit
- LightGBM
- XGBoost
- NBEATS
- NHITS

These challengers are planned only. They are not ready for official execution until preregistration, leakage controls, and audit checks pass.

## Temporal Isolation Rules

- For every backtesting window, training data must end at `train_end_date`.
- Test data must not be used for fitting.
- Future actuals must not be used for features.
- Future actuals must not be used for hyperparameter tuning.
- Forecast horizon actuals may only be used after forecasts are generated and only for evaluation.
- Models must not use data from future windows to tune earlier windows.

## Feature Leakage Rules

- No future timestamps may be used in features.
- No target leakage is allowed.
- Rolling windows must not include test-period actuals.
- Lag features must not be created from future values.
- Global transformations must not be fitted on full history including test rows.
- Normalization must not be fitted using future or test rows.
- Imputation must not use future or test rows.

## Tuning Rules

- Official MASE must not be used for hyperparameter tuning.
- Official RMSSE must not be used for hyperparameter tuning.
- Statistical significance outputs must not be used for tuning.
- Tournament rank must not be used for tuning.
- Champion selection feedback must not be used for tuning.
- If tuning is needed, it must occur only inside an explicitly defined inner-validation process using training-only data.

## Sandbox Mode

`sandbox_mode` is exploratory and may be used for code stability checks. Sandbox results are not eligible for champion decisions, cannot be promoted to official tournament results, and cannot be used as official benchmark evidence.

## Official Mode

`official_mode` requires locked configuration, locked windows, locked features, locked seeds, no post-hoc tuning, and formal metadata capture. Official mode is used for formal comparison only.

## Challenger Preregistration Requirements

Before official challenger execution, each challenger must declare:

- `model_name`
- `model_family`
- `allowed_features`
- `hyperparameter_space`
- `tuning_budget`
- `training_window_policy`
- `random_seed_policy`
- `dependency_requirements`
- `expected_runtime_class`
- `leakage_risk_level`

## Cross-Entity and Entity/Window Isolation

Cross-entity learning is allowed only when the model design explicitly declares it, the training data remains temporally valid, and no test-window outcomes leak across entities. Entity/window isolation must be preserved for every official backtesting window.

## Reproducibility Requirements

Every official challenger run must record:

- `run_id`
- git status
- config snapshot
- input data hashes if available
- random seeds
- dependency versions if available
- model registry snapshot
- execution timestamp

## Audit Requirements

Every challenger must produce enough metadata for Claude Code and future reviewers to inspect what data was used, what features were used, what hyperparameters were used, whether tuning occurred, and whether the run was sandbox or official.

## Blocking Conditions

Official challenger execution is blocked if any required leakage control fails, preregistration is incomplete, official mode is not declared, tuning uses official results, future actuals are used before forecast generation, metadata is insufficient for audit, or the run cannot be reproduced.

## Prohibited Practices

- Using test-window actuals for fitting.
- Using future actuals for features or tuning.
- Tuning from official MASE/RMSSE outcomes.
- Tuning from significance outcomes.
- Tuning from tournament or champion feedback.
- Promoting sandbox outputs to official tournament evidence.
- Creating challenger official outputs without preregistration and audit controls.

## Input Configuration Findings

Missing optional config files are informational in this block and do not block contract creation:

- `config\model_registry.yaml`: missing informational
- `config\training_job_plan.yaml`: missing informational
- `config\execution.yaml`: present

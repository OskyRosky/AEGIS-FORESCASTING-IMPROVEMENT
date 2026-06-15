"""Block 5.29D-Recovery - official challenger model set re-scope.

Documents the approved replacement of NBEATS with FastNeuralAR_MLP for the
current official challenger execution set. This script creates current-state
addendum artifacts only; it does not create forecasts, metrics, rankings,
tournaments, or champion outputs.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_model_set_rescope")

RUN_ID = "block_5_29d_recovery_model_set_rescope"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "challenger_model_set_rescope"

FINAL_MODELS = [
    {
        "model_name": "AutoARIMA",
        "model_family": "statistical",
        "model_type": "auto_arima",
        "backend": "pmdarima",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "Theta",
        "model_family": "statistical",
        "model_type": "theta",
        "backend": "darts",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "ETS Explicit",
        "model_family": "statistical",
        "model_type": "ets_explicit",
        "backend": "statsmodels",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "LightGBM",
        "model_family": "machine_learning",
        "model_type": "gradient_boosted_tree",
        "backend": "lightgbm",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "XGBoost",
        "model_family": "machine_learning",
        "model_type": "gradient_boosted_tree",
        "backend": "xgboost",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "FastNeuralAR_MLP",
        "model_family": "lightweight_neural",
        "model_type": "autoregressive_mlp",
        "backend": "sklearn.neural_network.MLPRegressor",
        "official_candidate": True,
        "deferred": False,
        "deferred_reason": "",
        "included_in_final_official_execution": True,
    },
    {
        "model_name": "NBEATS",
        "model_family": "deep_learning",
        "model_type": "nbeats",
        "backend": "darts.torch",
        "official_candidate": False,
        "deferred": True,
        "deferred_reason": (
            "deferred_runtime_impractical: too slow for MVP/prototype automation "
            "profile in current Python/container execution context"
        ),
        "included_in_final_official_execution": False,
    },
    {
        "model_name": "NHITS",
        "model_family": "deep_learning",
        "model_type": "nhits",
        "backend": "neuralforecast/ray",
        "official_candidate": False,
        "deferred": True,
        "deferred_reason": (
            "deferred_dependency_blocked: Python 3.14 / neuralforecast / ray "
            "incompatibility"
        ),
        "included_in_final_official_execution": False,
    },
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _write_csv(df: pd.DataFrame, name: str, columns: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(OUTPUT_DIR / name, index=False)


def _write_text(name: str, text: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(text, encoding="utf-8")


def _decision(ts: str) -> pd.DataFrame:
    rows = [
        {
            "decision_id": RUN_ID,
            "previous_model_name": "NBEATS",
            "new_model_name": "",
            "decision_type": "defer_existing_model",
            "previous_status": "official_candidate",
            "new_status": "deferred_runtime_impractical",
            "reason": (
                "NBEATS was interrupted and deferred because runtime was too slow "
                "for the MVP/prototype automation profile in the current "
                "Python/container execution context."
            ),
            "approved_by_user": True,
            "created_timestamp": ts,
        },
        {
            "decision_id": RUN_ID,
            "previous_model_name": "NHITS",
            "new_model_name": "",
            "decision_type": "maintain_existing_deferral",
            "previous_status": "deferred_dependency_blocked",
            "new_status": "deferred_dependency_blocked",
            "reason": (
                "NHITS remains deferred because Python 3.14, neuralforecast, "
                "and ray dependencies are incompatible in this environment."
            ),
            "approved_by_user": True,
            "created_timestamp": ts,
        },
        {
            "decision_id": RUN_ID,
            "previous_model_name": "",
            "new_model_name": "FastNeuralAR_MLP",
            "decision_type": "add_replacement_model",
            "previous_status": "not_in_official_set",
            "new_status": "added_lightweight_neural_replacement",
            "reason": (
                "Adds a fast autoregressive neural MLP challenger, similar in "
                "spirit to NNETAR, to preserve a practical neural-style "
                "comparison for the MVP."
            ),
            "approved_by_user": True,
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def _current_set(ts: str) -> pd.DataFrame:
    rows = []
    for row in FINAL_MODELS:
        rows.append({**row, "created_timestamp": ts})
    return pd.DataFrame(rows)


def _onboarding(ts: str) -> pd.DataFrame:
    rows = [
        {
            "model_name": "FastNeuralAR_MLP",
            "onboarding_status": "added_lightweight_neural",
            "dependency_status": "available_or_lightweight_install_required",
            "leakage_controls_required": (
                "train only on actuals up to train_end_date; recursive forecast "
                "uses prior predictions after horizon day 1"
            ),
            "tuning_policy_required": (
                "fixed preregistered settings; no official metric feedback tuning "
                "and no tournament feedback tuning"
            ),
            "official_candidate": True,
            "notes": "Replacement neural-style MVP challenger using sklearn MLPRegressor.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NBEATS",
            "onboarding_status": "deferred_runtime_impractical",
            "dependency_status": "not_current_blocker",
            "leakage_controls_required": "not applicable while deferred",
            "tuning_policy_required": "not applicable while deferred",
            "official_candidate": False,
            "notes": "Deferred for runtime impracticality, not statistical failure.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NHITS",
            "onboarding_status": "deferred_dependency_blocked",
            "dependency_status": "blocked_python_3_14_neuralforecast_ray",
            "leakage_controls_required": "not applicable while deferred",
            "tuning_policy_required": "not applicable while deferred",
            "official_candidate": False,
            "notes": "Deferred for dependency incompatibility, not statistical failure.",
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def _execution_plan(ts: str) -> pd.DataFrame:
    rows = [
        {
            "model_name": "FastNeuralAR_MLP",
            "execution_plan_status": "added_to_current_official_plan",
            "recommended_mode": "official_after_sandbox",
            "runtime_class": "light_or_medium",
            "expected_runtime_profile": "fast enough for MVP/prototype automation",
            "official_execution_allowed": True,
            "notes": "Run sandbox first, then official 454 entity-window execution.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NBEATS",
            "execution_plan_status": "excluded_from_current_official_execution",
            "recommended_mode": "deferred",
            "runtime_class": "heavy",
            "expected_runtime_profile": "runtime impractical for current MVP automation",
            "official_execution_allowed": False,
            "notes": "Partial interrupted rows must not be included in final forecasts.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NHITS",
            "execution_plan_status": "excluded_from_current_official_execution",
            "recommended_mode": "deferred",
            "runtime_class": "blocked",
            "expected_runtime_profile": "dependency blocked",
            "official_execution_allowed": False,
            "notes": "Python 3.14 / neuralforecast / ray incompatibility.",
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def _official_prep(ts: str) -> pd.DataFrame:
    rows = [
        {
            "model_name": "FastNeuralAR_MLP",
            "official_prep_status": "ready_pending_sandbox",
            "sandbox_required": True,
            "official_scope_locked": True,
            "output_contract_locked": True,
            "ready_for_current_official_execution": True,
            "notes": "Must pass sandbox before official recovery execution.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NBEATS",
            "official_prep_status": "deferred_runtime_impractical",
            "sandbox_required": False,
            "official_scope_locked": True,
            "output_contract_locked": True,
            "ready_for_current_official_execution": False,
            "notes": "Preserve evidence but exclude partial official rows from final output.",
            "created_timestamp": ts,
        },
        {
            "model_name": "NHITS",
            "official_prep_status": "deferred_dependency_blocked",
            "sandbox_required": False,
            "official_scope_locked": True,
            "output_contract_locked": True,
            "ready_for_current_official_execution": False,
            "notes": "No NHITS official forecast rows are allowed.",
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def _policy_markdown(ts: str) -> str:
    return f"""# FastNeuralAR_MLP Policy

Generated: {ts}

## Purpose

FastNeuralAR_MLP is introduced as the lightweight neural replacement for the
current official challenger set after NBEATS was deferred for runtime
impracticality. It keeps a neural-style comparison in the MVP without requiring
heavy deep-learning training loops or dependency stacks.

## MVP Suitability

The model uses `sklearn.neural_network.MLPRegressor` with fixed parameters and
lagged historical actuals as features. It is designed to run quickly across the
locked 454 entity-windows and to remain suitable for future container and Azure
automation.

## Conceptual Relationship to NNETAR

Like R's NNETAR, the model is an autoregressive neural network: recent lagged
values are the inputs and the next value is the supervised target. Forecasts are
generated recursively for the 30-day horizon.

## Leakage Policy

- Training uses only actual values with `date <= train_end_date`.
- No future actual values are used in recursive forecasting.
- Horizon day 2 and later may use prior model predictions, not test actuals.

## Tuning Policy

- Lags are capped at 30 and reduced only when history is insufficient.
- Hidden layer size is fixed at `(32,)`.
- Activation is `relu`, solver is `adam`, `max_iter` is 300, and random seed is
  42.
- No official metric feedback tuning, no tournament feedback tuning, and no
  champion feedback tuning are allowed in this block.

## Runtime Policy

FastNeuralAR_MLP is classified as `light_or_medium`. It may replace heavier
neural candidates in MVP official execution when those candidates are runtime
impractical.

## Automation and Container Suitability

The dependency footprint is limited to `scikit-learn`, `numpy`, and `pandas`.
This is compatible with a lightweight Python container profile and avoids the
Python 3.14 neuralforecast/ray blocker that affects NHITS.
"""


def _report(ts: str) -> str:
    return f"""# Block 5.29D-Recovery - Model Set Re-scope Report

Generated: {ts}

## Original Model Set

The started 5.29D official set contained AutoARIMA, Theta, ETS Explicit,
LightGBM, XGBoost, and NBEATS. NHITS was already deferred.

## Runtime and Dependency Issue

NBEATS became runtime-impractical for the current MVP/prototype execution
profile. NHITS remains dependency-blocked due to Python 3.14 /
neuralforecast / ray incompatibility.

## Final Model Set

The current official challenger set is AutoARIMA, Theta, ETS Explicit,
LightGBM, XGBoost, and FastNeuralAR_MLP.

## Deferred Models

- NBEATS: `deferred_runtime_impractical`; too slow for MVP/prototype automation
  in the current Python/container execution context.
- NHITS: `deferred_dependency_blocked`; Python 3.14 / neuralforecast / ray
  incompatibility.

## FastNeuralAR_MLP Role

FastNeuralAR_MLP provides a lightweight neural/autoregressive comparison
similar in spirit to NNETAR. It uses lagged actuals and an sklearn MLPRegressor
with fixed settings.

## Workload Impact

The final workload remains six official models over 454 entity-windows and a
30-day horizon, for 81,720 forecast rows.

## Scope and Safety

This re-scope does not calculate metrics, rankings, tournament outputs, or
champion selections. It does not rewrite historical evidence for NBEATS or
NHITS.

## Recommendation

Proceed with recovery execution: preserve completed official forecasts, exclude
partial NBEATS rows, sandbox FastNeuralAR_MLP, run it officially if sandbox
passes, and validate the final forecast contract.
"""


def main() -> None:
    ts = _now()
    logger.info("=== Block 5.29D-Recovery - Model Set Re-scope ===")

    _write_csv(
        _decision(ts),
        "model_set_rescope_decision.csv",
        [
            "decision_id",
            "previous_model_name",
            "new_model_name",
            "decision_type",
            "previous_status",
            "new_status",
            "reason",
            "approved_by_user",
            "created_timestamp",
        ],
    )
    _write_csv(
        _current_set(ts),
        "current_official_challenger_set.csv",
        [
            "model_name",
            "model_family",
            "model_type",
            "backend",
            "official_candidate",
            "deferred",
            "deferred_reason",
            "included_in_final_official_execution",
            "created_timestamp",
        ],
    )
    _write_csv(
        _onboarding(ts),
        "onboarding_addendum.csv",
        [
            "model_name",
            "onboarding_status",
            "dependency_status",
            "leakage_controls_required",
            "tuning_policy_required",
            "official_candidate",
            "notes",
            "created_timestamp",
        ],
    )
    _write_csv(
        _execution_plan(ts),
        "execution_planning_addendum.csv",
        [
            "model_name",
            "execution_plan_status",
            "recommended_mode",
            "runtime_class",
            "expected_runtime_profile",
            "official_execution_allowed",
            "notes",
            "created_timestamp",
        ],
    )
    _write_csv(
        _official_prep(ts),
        "official_execution_prep_addendum.csv",
        [
            "model_name",
            "official_prep_status",
            "sandbox_required",
            "official_scope_locked",
            "output_contract_locked",
            "ready_for_current_official_execution",
            "notes",
            "created_timestamp",
        ],
    )
    _write_text("fast_neural_policy.md", _policy_markdown(ts))
    _write_text("model_set_rescope_report.md", _report(ts))
    logger.info("Model-set re-scope artifacts written to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()

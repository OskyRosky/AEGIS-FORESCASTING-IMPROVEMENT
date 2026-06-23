"""Review larger baseline pilot forecasts for sanity and stability.

This Stage 5.9D script performs read-only forecast diagnostics. It does not
calculate accuracy metrics, rankings, tournament scores, rerun models, or
modify forecast inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("review_forecast_sanity")

PILOT_FORECASTS = (
    PROJECT_ROOT / "outputs" / "model_lab" / "baseline_pilot" / "baseline_pilot_forecasts.csv"
)
SANITY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "sanity_review"
SANITY_SUMMARY_OUTPUT = SANITY_DIR / "forecast_sanity_summary.csv"
SANITY_BY_MODEL_OUTPUT = SANITY_DIR / "forecast_sanity_by_model.csv"
SANITY_BY_ENTITY_OUTPUT = SANITY_DIR / "forecast_sanity_by_entity.csv"
SANITY_FLAGS_OUTPUT = SANITY_DIR / "forecast_sanity_flags.csv"

BASELINE_MODELS = [
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
]
VARIABLE_MODELS = {"ARIMA_Fixed", "ETS_Current", "LinearRegression"}
FIXED_GROWTH_MODELS = [
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
]


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required sanity review input missing: {path}")


def _add_flag(flags: list[dict], level: str, subject: str, flag_type: str, message: str) -> None:
    """Append one sanity flag row."""

    flags.append(
        {
            "level": level,
            "subject": subject,
            "flag_type": flag_type,
            "severity": "warning",
            "message": message,
        }
    )


def _load_forecasts() -> pd.DataFrame:
    """Load baseline pilot forecasts with numeric forecast values."""

    _require_file(PILOT_FORECASTS)
    forecasts = pd.read_csv(PILOT_FORECASTS, parse_dates=["forecast_date"])
    forecasts["forecast_value"] = pd.to_numeric(
        forecasts["forecast_value"], errors="coerce"
    )
    return forecasts


def _build_summary(forecasts: pd.DataFrame, flags: list[dict]) -> pd.DataFrame:
    """Build one-row global sanity summary."""

    values = forecasts["forecast_value"]
    return pd.DataFrame(
        [
            {
                "forecast_rows_reviewed": len(forecasts),
                "entity_count": forecasts["entity_key"].nunique(),
                "model_count": forecasts["model_name"].nunique(),
                "job_count": forecasts["job_id"].nunique(),
                "null_forecast_count": int(values.isna().sum()),
                "null_horizon_count": int(forecasts["horizon_day"].isna().sum()),
                "null_date_count": int(forecasts["forecast_date"].isna().sum()),
                "null_entity_key_count": int(forecasts["entity_key"].isna().sum()),
                "nan_forecast_count": int(np.isnan(values.to_numpy(dtype=float)).sum()),
                "positive_inf_forecast_count": int(np.isposinf(values.to_numpy(dtype=float)).sum()),
                "negative_inf_forecast_count": int(np.isneginf(values.to_numpy(dtype=float)).sum()),
                "negative_forecast_count": int((values < 0).sum()),
                "flag_count": len(flags),
                "recommendation": "APPROVE_FOR_FULL_BASELINE_EXECUTION"
                if len(flags) == 0
                else "REVIEW_FLAGS_BEFORE_FULL_BASELINE_EXECUTION",
            }
        ]
    )


def _review_by_model(forecasts: pd.DataFrame, flags: list[dict]) -> pd.DataFrame:
    """Build model-level sanity diagnostics and flags."""

    rows = []
    for model_name, group in forecasts.groupby("model_name", sort=True):
        values = group["forecast_value"]
        median_forecast = float(values.median())
        max_forecast = float(values.max())
        variance = float(values.var(ddof=0))
        negative_count = int((values < 0).sum())
        negative_pct = negative_count / len(group) if len(group) else 0.0
        explosion_flag = bool(
            median_forecast > 0 and max_forecast > 100 * median_forecast
        )
        collapse_flag = bool(model_name in VARIABLE_MODELS and variance <= 1e-12)

        drift_by_job = (
            group.sort_values("horizon_day")
            .groupby("job_id")["forecast_value"]
            .agg(lambda series: float(series.iloc[-1] - series.iloc[0]))
        )
        max_abs_drift = float(drift_by_job.abs().max()) if not drift_by_job.empty else 0.0

        if explosion_flag:
            _add_flag(
                flags,
                "model",
                model_name,
                "explosion",
                f"max_forecast {max_forecast} exceeds 100x median {median_forecast}.",
            )
        if collapse_flag:
            _add_flag(
                flags,
                "model",
                model_name,
                "collapse",
                "Forecast variance is effectively zero for a model expected to vary.",
            )
        if negative_count > 0:
            _add_flag(
                flags,
                "model",
                model_name,
                "negative_forecasts",
                f"{negative_count} forecasts are negative ({negative_pct:.2%}).",
            )

        rows.append(
            {
                "model_name": model_name,
                "forecast_rows": len(group),
                "job_count": group["job_id"].nunique(),
                "entity_count": group["entity_key"].nunique(),
                "min_forecast": float(values.min()),
                "max_forecast": max_forecast,
                "median_forecast": median_forecast,
                "forecast_variance": variance,
                "negative_forecast_count": negative_count,
                "negative_forecast_pct": negative_pct,
                "explosion_flag": explosion_flag,
                "collapse_flag": collapse_flag,
                "max_abs_horizon_drift": max_abs_drift,
            }
        )

    return pd.DataFrame(rows)


def _review_fixed_growth_ordering(forecasts: pd.DataFrame, flags: list[dict]) -> None:
    """Validate fixed-growth trajectories are ordered by growth rate."""

    growth = forecasts[forecasts["model_name"].isin(FIXED_GROWTH_MODELS)]
    pivot = growth.pivot_table(
        index=["entity_key", "window_id", "horizon_day"],
        columns="model_name",
        values="forecast_value",
        aggfunc="first",
    )
    missing_columns = [name for name in FIXED_GROWTH_MODELS if name not in pivot.columns]
    if missing_columns:
        _add_flag(
            flags,
            "model",
            "FixedGrowth",
            "missing_growth_model",
            f"Missing fixed growth models: {missing_columns}",
        )
        return

    ordered = (
        (pivot["FixedGrowth_1_5"] <= pivot["FixedGrowth_3"])
        & (pivot["FixedGrowth_3"] <= pivot["FixedGrowth_4"])
        & (pivot["FixedGrowth_4"] <= pivot["FixedGrowth_6"])
    )
    violations = int((~ordered).sum())
    if violations:
        _add_flag(
            flags,
            "model",
            "FixedGrowth",
            "growth_order_violation",
            f"{violations} fixed-growth rows violate expected growth-rate ordering.",
        )


def _review_by_entity(forecasts: pd.DataFrame, flags: list[dict]) -> pd.DataFrame:
    """Build entity-level forecast range diagnostics and flags."""

    rows = []
    global_median = float(forecasts["forecast_value"].median())
    for entity_key, group in forecasts.groupby("entity_key", sort=True):
        values = group["forecast_value"]
        min_forecast = float(values.min())
        max_forecast = float(values.max())
        median_forecast = float(values.median())
        if global_median > 0 and max_forecast > 100 * global_median:
            _add_flag(
                flags,
                "entity",
                entity_key,
                "entity_extreme_range",
                f"Entity max {max_forecast} exceeds 100x global median {global_median}.",
            )

        rows.append(
            {
                "entity_key": entity_key,
                "forecast_rows": len(group),
                "model_count": group["model_name"].nunique(),
                "window_count": group[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "forecast_min": min_forecast,
                "forecast_max": max_forecast,
                "forecast_median": median_forecast,
                "negative_forecast_count": int((values < 0).sum()),
            }
        )

    return pd.DataFrame(rows)


def review_forecast_sanity() -> dict[str, pd.DataFrame]:
    """Run all forecast sanity checks and write review outputs."""

    logger.info("Stage 5.9D forecast sanity review started")
    SANITY_DIR.mkdir(parents=True, exist_ok=True)
    forecasts = _load_forecasts()
    flags: list[dict] = []

    if len(forecasts) != 2100:
        _add_flag(
            flags,
            "global",
            "baseline_pilot_forecasts",
            "row_count",
            f"Expected 2100 rows, found {len(forecasts)}.",
        )
    unexpected_models = sorted(set(forecasts["model_name"]) - set(BASELINE_MODELS))
    if unexpected_models:
        _add_flag(
            flags,
            "global",
            "baseline_pilot_forecasts",
            "unexpected_models",
            f"Unexpected models found: {unexpected_models}",
        )

    by_model = _review_by_model(forecasts, flags)
    _review_fixed_growth_ordering(forecasts, flags)
    by_entity = _review_by_entity(forecasts, flags)
    flags_frame = pd.DataFrame(
        flags, columns=["level", "subject", "flag_type", "severity", "message"]
    )
    summary = _build_summary(forecasts, flags)

    summary.to_csv(SANITY_SUMMARY_OUTPUT, index=False)
    by_model.to_csv(SANITY_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(SANITY_BY_ENTITY_OUTPUT, index=False)
    flags_frame.to_csv(SANITY_FLAGS_OUTPUT, index=False)

    logger.info("Created %s with %s rows", SANITY_SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s with %s rows", SANITY_BY_MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", SANITY_BY_ENTITY_OUTPUT, len(by_entity))
    logger.info("Created %s with %s rows", SANITY_FLAGS_OUTPUT, len(flags_frame))
    logger.info("Stage 5.9D forecast sanity review completed")
    return {
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
        "flags": flags_frame,
    }


if __name__ == "__main__":
    review_forecast_sanity()

"""Review baseline metrics for sanity before ranking design.

This Stage 5.12 script performs diagnostics on baseline metric outputs. It does
not create rankings, composite scores, tournament outputs, or winners.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("review_metrics_sanity")

METRICS_INPUT = PROJECT_ROOT / "outputs" / "model_lab" / "metrics" / "baseline_metrics.csv"
METRICS_SANITY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "metrics_sanity"
METRICS_SANITY_SUMMARY_OUTPUT = METRICS_SANITY_DIR / "metrics_sanity_summary.csv"
METRICS_SANITY_BY_MODEL_OUTPUT = METRICS_SANITY_DIR / "metrics_sanity_by_model.csv"
METRICS_SANITY_BY_ENTITY_OUTPUT = METRICS_SANITY_DIR / "metrics_sanity_by_entity.csv"
METRICS_SANITY_FLAGS_OUTPUT = METRICS_SANITY_DIR / "metrics_sanity_flags.csv"

METRIC_COLUMNS = ["wmape", "mape", "rmse", "smape", "abs_bias"]
NON_NEGATIVE_METRICS = ["wmape", "mape", "rmse", "smape"]
EXTREME_PERCENT_METRIC_THRESHOLD = 1.0


def _require_file(path) -> None:
    """Validate that a required metrics sanity input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required metrics sanity input missing: {path}")


def _add_flag(
    flags: list[dict],
    flag_type: str,
    level: str,
    subject: str,
    metric_name: str,
    value: float | str,
    threshold: float | str,
    message: str,
) -> None:
    """Append one metrics sanity flag."""

    flags.append(
        {
            "flag_type": flag_type,
            "level": level,
            "subject": subject,
            "metric_name": metric_name,
            "value": value,
            "threshold": threshold,
            "severity": "warning",
            "message": message,
        }
    )


def _load_metrics() -> pd.DataFrame:
    """Load baseline metrics and derive absolute bias."""

    _require_file(METRICS_INPUT)
    metrics = pd.read_csv(METRICS_INPUT)
    for column in ["wmape", "mape", "rmse", "smape", "bias"]:
        metrics[column] = pd.to_numeric(metrics[column], errors="coerce")
    metrics["abs_bias"] = metrics["bias"].abs()
    return metrics


def _validate_metric_values(metrics: pd.DataFrame, flags: list[dict]) -> None:
    """Check invalid, non-finite, and impossible metric values."""

    for column in ["wmape", "mape", "rmse", "smape", "bias"]:
        values = metrics[column]
        null_count = int(values.isna().sum())
        inf_count = int(np.isinf(values.to_numpy(dtype=float)).sum())
        if null_count:
            _add_flag(
                flags,
                "metric_invalid",
                "metric",
                column,
                column,
                null_count,
                0,
                f"{column} contains {null_count} null/NaN values.",
            )
        if inf_count:
            _add_flag(
                flags,
                "metric_invalid",
                "metric",
                column,
                column,
                inf_count,
                0,
                f"{column} contains {inf_count} infinite values.",
            )

    for column in NON_NEGATIVE_METRICS:
        negative_count = int((metrics[column] < 0).sum())
        if negative_count:
            _add_flag(
                flags,
                "metric_invalid",
                "metric",
                column,
                column,
                negative_count,
                0,
                f"{column} contains {negative_count} negative values.",
            )


def _distribution_rows(metrics: pd.DataFrame, flags: list[dict]) -> list[dict]:
    """Build distribution summary rows and global metric flags."""

    rows = []
    for metric_name in METRIC_COLUMNS:
        values = metrics[metric_name].dropna()
        median = float(values.median())
        p99 = float(values.quantile(0.99))
        max_value = float(values.max())
        ten_x_median = 10 * median if median > 0 else np.inf
        high_count = int((values > ten_x_median).sum()) if np.isfinite(ten_x_median) else 0
        p99_count = int((values >= p99).sum())

        if metric_name in {"wmape", "mape"}:
            extreme_count = int((values > EXTREME_PERCENT_METRIC_THRESHOLD).sum())
            if extreme_count:
                _add_flag(
                    flags,
                    f"{metric_name}_extreme",
                    "metric",
                    metric_name,
                    metric_name,
                    extreme_count,
                    EXTREME_PERCENT_METRIC_THRESHOLD,
                    f"{metric_name} has {extreme_count} rows above 1.0.",
                )
        if high_count:
            flag_type = "bias_extreme" if metric_name == "abs_bias" else f"{metric_name}_extreme"
            _add_flag(
                flags,
                flag_type,
                "metric",
                metric_name,
                metric_name,
                high_count,
                ten_x_median,
                f"{metric_name} has {high_count} rows greater than 10x median.",
            )

        rows.append(
            {
                "metric_name": metric_name,
                "min": float(values.min()),
                "p25": float(values.quantile(0.25)),
                "median": median,
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.90)),
                "p95": float(values.quantile(0.95)),
                "p99": p99,
                "max": max_value,
                "p99_outlier_rows": p99_count,
                "greater_than_10x_median_rows": high_count,
            }
        )

    return rows


def _model_summary(metrics: pd.DataFrame, flags: list[dict]) -> pd.DataFrame:
    """Build model-level sanity diagnostics."""

    rows = []
    global_wmape_median = float(metrics["wmape"].median())
    for model_name, group in metrics.groupby("model_name", sort=True):
        under_pct = float((group["bias"] < 0).mean())
        over_pct = float((group["bias"] > 0).mean())
        median_wmape = float(group["wmape"].median())
        p95_wmape = float(group["wmape"].quantile(0.95))
        median_rmse = float(group["rmse"].median())
        p95_rmse = float(group["rmse"].quantile(0.95))
        avg_signed_bias = float(group["bias"].mean())
        avg_abs_bias = float(group["abs_bias"].mean())

        if global_wmape_median > 0 and median_wmape > 10 * global_wmape_median:
            _add_flag(
                flags,
                "model_outlier",
                "model",
                model_name,
                "wmape",
                median_wmape,
                10 * global_wmape_median,
                "Model median wMAPE exceeds 10x global median wMAPE.",
            )

        rows.append(
            {
                "model_name": model_name,
                "metric_rows": len(group),
                "median_wmape": median_wmape,
                "p95_wmape": p95_wmape,
                "median_rmse": median_rmse,
                "p95_rmse": p95_rmse,
                "avg_signed_bias": avg_signed_bias,
                "avg_absolute_bias": avg_abs_bias,
                "underforecast_pct": under_pct,
                "overforecast_pct": over_pct,
            }
        )

    return pd.DataFrame(rows)


def _entity_summary(metrics: pd.DataFrame, flags: list[dict]) -> pd.DataFrame:
    """Build entity-level sanity diagnostics."""

    rows = []
    global_wmape_median = float(metrics["wmape"].median())
    for entity_key, group in metrics.groupby("entity_key", sort=True):
        median_wmape = float(group["wmape"].median())
        p95_wmape = float(group["wmape"].quantile(0.95))
        median_rmse = float(group["rmse"].median())
        p95_rmse = float(group["rmse"].quantile(0.95))
        avg_signed_bias = float(group["bias"].mean())
        model_wmape = group.groupby("model_name")["wmape"].mean()
        worst_model = str(model_wmape.idxmax())
        best_model = str(model_wmape.idxmin())

        if global_wmape_median > 0 and median_wmape > 10 * global_wmape_median:
            _add_flag(
                flags,
                "entity_outlier",
                "entity",
                entity_key,
                "wmape",
                median_wmape,
                10 * global_wmape_median,
                "Entity median wMAPE exceeds 10x global median wMAPE.",
            )

        rows.append(
            {
                "entity_key": entity_key,
                "metric_rows": len(group),
                "median_wmape": median_wmape,
                "p95_wmape": p95_wmape,
                "median_rmse": median_rmse,
                "p95_rmse": p95_rmse,
                "avg_signed_bias": avg_signed_bias,
                "worst_model_by_wmape": worst_model,
                "best_model_by_wmape": best_model,
            }
        )

    return pd.DataFrame(rows)


def review_metrics_sanity() -> dict[str, pd.DataFrame]:
    """Run baseline metrics sanity review and write outputs."""

    logger.info("Stage 5.12 metrics sanity review started")
    METRICS_SANITY_DIR.mkdir(parents=True, exist_ok=True)
    metrics = _load_metrics()
    flags: list[dict] = []

    _validate_metric_values(metrics, flags)
    distribution_rows = _distribution_rows(metrics, flags)
    by_model = _model_summary(metrics, flags)
    by_entity = _entity_summary(metrics, flags)
    flags_frame = pd.DataFrame(
        flags,
        columns=[
            "flag_type",
            "level",
            "subject",
            "metric_name",
            "value",
            "threshold",
            "severity",
            "message",
        ],
    )
    summary = pd.DataFrame(
        [
            {
                "metric_rows_reviewed": len(metrics),
                "entities": metrics["entity_key"].nunique(),
                "windows": metrics[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "models": metrics["model_name"].nunique(),
                "invalid_metric_flag_count": int(
                    (flags_frame["flag_type"] == "metric_invalid").sum()
                )
                if not flags_frame.empty
                else 0,
                "flag_count": len(flags_frame),
                "recommendation": "APPROVE_BASELINE_RANKING_STAGE"
                if flags_frame.empty
                else "BLOCK_BASELINE_RANKING_STAGE",
            }
        ]
    )
    distribution = pd.DataFrame(distribution_rows)

    summary.to_csv(METRICS_SANITY_SUMMARY_OUTPUT, index=False)
    by_model.to_csv(METRICS_SANITY_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(METRICS_SANITY_BY_ENTITY_OUTPUT, index=False)
    flags_frame.to_csv(METRICS_SANITY_FLAGS_OUTPUT, index=False)

    logger.info("Created %s with %s rows", METRICS_SANITY_SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s with %s rows", METRICS_SANITY_BY_MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", METRICS_SANITY_BY_ENTITY_OUTPUT, len(by_entity))
    logger.info("Created %s with %s rows", METRICS_SANITY_FLAGS_OUTPUT, len(flags_frame))
    logger.info("Metric distributions reviewed: %s", distribution.to_dict("records"))
    logger.info("Stage 5.12 metrics sanity review completed")
    return {
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
        "flags": flags_frame,
        "distribution": distribution,
    }


if __name__ == "__main__":
    review_metrics_sanity()

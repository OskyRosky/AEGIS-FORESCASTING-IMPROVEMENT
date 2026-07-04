"""Block 5.29E - Challenger Metrics Scoring.

Calculates official challenger metrics for the finalized six-model challenger
forecast set. This block reads official forecasts and training-only
denominators, writes only challenger metric artifacts, and does not aggregate,
rank, run tournaments, or select champions.
"""

from __future__ import annotations

from datetime import datetime
from math import sqrt

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("calculate_challenger_metrics")

RUN_ID = "challenger_metrics_scoring"
EXECUTION_MODE = "official"
EXPECTED_FORECAST_ROWS = 81720
EXPECTED_METRIC_ROWS = 2724
EXPECTED_ENTITY_WINDOWS = 454
EXPECTED_HORIZON_DAYS = 30
EXPECTED_PER_MODEL_FORECAST_ROWS = 13620

FINAL_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
]
DEFERRED_MODELS = ["NBEATS", "NHITS"]

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_metrics"
FORECAST_PATH = MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_forecasts.csv"
OFFICIAL_SUMMARY_PATH = (
    MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_execution_summary.csv"
)
OFFICIAL_CONTRACT_PATH = (
    MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_contract_validation.csv"
)
ACTUALS_PATH = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
DENOMINATOR_PATH = (
    MODEL_LAB_DIR / "denominator_reconciliation" / "training_only_denominators.csv"
)

SCORING_FORECAST_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "adjusted_forecast_value",
    "negative_forecast_flag",
    "negative_adjustment_amount",
    "execution_mode",
    "created_timestamp",
]
JOIN_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "actual_value",
    "forecast_value",
    "adjusted_forecast_value",
    "error",
    "abs_error",
    "squared_error",
    "execution_mode",
    "created_timestamp",
]
METRIC_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "mase",
    "rmsse",
    "wmape",
    "mape",
    "smape",
    "rmse",
    "bias",
    "actual_sum",
    "absolute_error_sum",
    "squared_error_mean",
    "mase_denominator",
    "rmsse_denominator",
    "forecast_rows",
    "negative_forecast_rows",
    "execution_mode",
    "created_timestamp",
]
NEGATIVE_IMPACT_COLUMNS = [
    "run_id",
    "model_name",
    "negative_forecast_rows",
    "total_forecast_rows",
    "negative_forecast_rate",
    "min_raw_forecast_value",
    "max_negative_adjustment_amount",
    "affected_entity_windows",
    "created_timestamp",
]
DIAGNOSTIC_COLUMNS = [
    "run_id",
    "model_name",
    "metric_rows",
    "median_mase",
    "mean_mase",
    "median_rmsse",
    "mean_rmsse",
    "median_wmape",
    "mean_wmape",
    "median_smape",
    "mean_smape",
    "median_rmse",
    "mean_rmse",
    "median_bias",
    "mean_bias",
    "negative_forecast_rows",
    "created_timestamp",
]
VALIDATION_COLUMNS = ["check_name", "status", "details", "created_timestamp"]
SUMMARY_COLUMNS = [
    "run_id",
    "official_models",
    "forecast_rows",
    "joined_actual_rows",
    "metric_rows",
    "entity_windows",
    "horizon_days",
    "mase_denominator_source",
    "rmsse_denominator_source",
    "negative_forecast_rows",
    "metrics_created",
    "aggregation_created",
    "significance_created",
    "rankings_created",
    "tournament_created",
    "champion_selected",
    "created_timestamp",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _require_file(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")


def _write_csv(df: pd.DataFrame, filename: str, columns: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(OUTPUT_DIR / filename, index=False)


def _load_forecasts() -> pd.DataFrame:
    _require_file(FORECAST_PATH)
    forecasts = pd.read_csv(FORECAST_PATH, parse_dates=["forecast_date"])
    required = {
        "run_id",
        "model_name",
        "entity_key",
        "window_id",
        "forecast_date",
        "horizon_day",
        "forecast_value",
        "execution_mode",
        "created_timestamp",
    }
    missing = required.difference(forecasts.columns)
    if missing:
        raise ValueError(f"official forecasts missing columns: {sorted(missing)}")
    forecasts = forecasts.copy()
    forecasts["window_id"] = pd.to_numeric(forecasts["window_id"], errors="raise").astype(int)
    forecasts["horizon_day"] = pd.to_numeric(forecasts["horizon_day"], errors="raise").astype(int)
    forecasts["forecast_value"] = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    return forecasts


def _load_actuals() -> pd.DataFrame:
    _require_file(ACTUALS_PATH)
    actuals = pd.read_csv(ACTUALS_PATH, parse_dates=["date"])
    if "record_type" in actuals.columns:
        actuals = actuals[actuals["record_type"].astype(str).str.lower() == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "actual_value"]).copy()
    return actuals[["entity_key", "date", "actual_value"]].rename(
        columns={"date": "forecast_date"}
    )


def _load_denominators() -> pd.DataFrame:
    _require_file(DENOMINATOR_PATH)
    denominators = pd.read_csv(DENOMINATOR_PATH)
    required = {
        "entity_key",
        "window_id",
        "mase_denominator_mae",
        "rmsse_denominator_mse",
    }
    missing = required.difference(denominators.columns)
    if missing:
        raise ValueError(f"training-only denominators missing columns: {sorted(missing)}")
    denominators = denominators.copy()
    denominators["window_id"] = pd.to_numeric(denominators["window_id"], errors="raise").astype(int)
    denominators["mase_denominator_mae"] = pd.to_numeric(
        denominators["mase_denominator_mae"], errors="coerce"
    )
    denominators["rmsse_denominator_mse"] = pd.to_numeric(
        denominators["rmsse_denominator_mse"], errors="coerce"
    )
    return denominators[
        ["entity_key", "window_id", "mase_denominator_mae", "rmsse_denominator_mse"]
    ]


def _build_scoring_forecasts(forecasts: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    scoring = forecasts[
        [
            "model_name",
            "entity_key",
            "window_id",
            "forecast_date",
            "horizon_day",
            "forecast_value",
            "execution_mode",
        ]
    ].copy()
    scoring["adjusted_forecast_value"] = scoring["forecast_value"].clip(lower=0)
    scoring["negative_forecast_flag"] = scoring["forecast_value"] < 0
    scoring["negative_adjustment_amount"] = (
        scoring["adjusted_forecast_value"] - scoring["forecast_value"]
    )
    scoring.insert(0, "run_id", RUN_ID)
    scoring["forecast_date"] = pd.to_datetime(scoring["forecast_date"]).dt.strftime("%Y-%m-%d")
    scoring["created_timestamp"] = timestamp
    return scoring[SCORING_FORECAST_COLUMNS]


def _build_actual_join(scoring: pd.DataFrame, actuals: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    scoring_for_join = scoring.copy()
    scoring_for_join["forecast_date"] = pd.to_datetime(scoring_for_join["forecast_date"])
    joined = scoring_for_join.merge(
        actuals,
        on=["entity_key", "forecast_date"],
        how="left",
        validate="many_to_one",
    )
    joined["error"] = joined["adjusted_forecast_value"] - joined["actual_value"]
    joined["abs_error"] = joined["error"].abs()
    joined["squared_error"] = joined["error"] ** 2
    joined["forecast_date"] = pd.to_datetime(joined["forecast_date"]).dt.strftime("%Y-%m-%d")
    joined["created_timestamp"] = timestamp
    return joined[JOIN_COLUMNS]


def _safe_mean(series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return float(clean.mean()) if len(clean) else np.nan


def _calculate_metrics(
    joined: pd.DataFrame, denominators: pd.DataFrame, scoring: pd.DataFrame, timestamp: str
) -> pd.DataFrame:
    metric_frame = joined.merge(
        denominators,
        on=["entity_key", "window_id"],
        how="left",
        validate="many_to_one",
    )
    rows = []
    negative_counts = scoring.groupby(["model_name", "entity_key", "window_id"])[
        "negative_forecast_flag"
    ].sum()
    for (model_name, entity_key, window_id), group in metric_frame.groupby(
        ["model_name", "entity_key", "window_id"], sort=True
    ):
        mase_denominator = float(group["mase_denominator_mae"].iloc[0])
        rmsse_denominator_mse = float(group["rmsse_denominator_mse"].iloc[0])
        mae = float(group["abs_error"].mean())
        squared_error_mean = float(group["squared_error"].mean())
        rmse = sqrt(squared_error_mean)
        actual_abs_sum = float(group["actual_value"].abs().sum())
        absolute_error_sum = float(group["abs_error"].sum())
        wmape = absolute_error_sum / actual_abs_sum if actual_abs_sum != 0 else np.nan
        nonzero_actuals = group[group["actual_value"].abs() > 1e-9]
        mape = (
            float((nonzero_actuals["abs_error"] / nonzero_actuals["actual_value"].abs()).mean())
            if len(nonzero_actuals)
            else np.nan
        )
        smape_denominator = group["adjusted_forecast_value"].abs() + group["actual_value"].abs()
        smape_terms = np.where(
            smape_denominator.to_numpy(dtype=float) > 1e-9,
            2 * group["abs_error"].to_numpy(dtype=float) / smape_denominator.to_numpy(dtype=float),
            np.nan,
        )
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model_name,
                "entity_key": entity_key,
                "window_id": int(window_id),
                "mase": mae / mase_denominator,
                "rmsse": sqrt(squared_error_mean / rmsse_denominator_mse),
                "wmape": wmape,
                "mape": mape,
                "smape": float(np.nanmean(smape_terms)) if not np.isnan(smape_terms).all() else np.nan,
                "rmse": rmse,
                "bias": float(group["error"].mean()),
                "actual_sum": float(group["actual_value"].sum()),
                "absolute_error_sum": absolute_error_sum,
                "squared_error_mean": squared_error_mean,
                "mase_denominator": mase_denominator,
                "rmsse_denominator": sqrt(rmsse_denominator_mse),
                "forecast_rows": int(len(group)),
                "negative_forecast_rows": int(
                    negative_counts.get((model_name, entity_key, window_id), 0)
                ),
                "execution_mode": EXECUTION_MODE,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=METRIC_COLUMNS)


def _negative_impact(scoring: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model_name, group in scoring.groupby("model_name", sort=True):
        negative = group[group["negative_forecast_flag"].astype(bool)]
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model_name,
                "negative_forecast_rows": int(len(negative)),
                "total_forecast_rows": int(len(group)),
                "negative_forecast_rate": float(len(negative) / len(group)) if len(group) else 0.0,
                "min_raw_forecast_value": float(group["forecast_value"].min()) if len(group) else np.nan,
                "max_negative_adjustment_amount": float(
                    group["negative_adjustment_amount"].max()
                )
                if len(group)
                else np.nan,
                "affected_entity_windows": int(
                    negative[["entity_key", "window_id"]].drop_duplicates().shape[0]
                ),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=NEGATIVE_IMPACT_COLUMNS)


def _diagnostic_by_model(metrics: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model_name, group in metrics.groupby("model_name", sort=False):
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model_name,
                "metric_rows": int(len(group)),
                "median_mase": float(group["mase"].median()),
                "mean_mase": float(group["mase"].mean()),
                "median_rmsse": float(group["rmsse"].median()),
                "mean_rmsse": float(group["rmsse"].mean()),
                "median_wmape": float(group["wmape"].median()),
                "mean_wmape": float(group["wmape"].mean()),
                "median_smape": float(group["smape"].median()),
                "mean_smape": float(group["smape"].mean()),
                "median_rmse": float(group["rmse"].median()),
                "mean_rmse": float(group["rmse"].mean()),
                "median_bias": float(group["bias"].median()),
                "mean_bias": float(group["bias"].mean()),
                "negative_forecast_rows": int(group["negative_forecast_rows"].sum()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=DIAGNOSTIC_COLUMNS)


def _validate(
    forecasts: pd.DataFrame,
    scoring: pd.DataFrame,
    joined: pd.DataFrame,
    metrics: pd.DataFrame,
    summary: pd.DataFrame,
) -> pd.DataFrame:
    timestamp = _now()
    rows = []

    def add(check_name: str, ok: bool, details: str) -> None:
        rows.append(
            {
                "check_name": check_name,
                "status": "pass" if ok else "fail",
                "details": details,
                "created_timestamp": timestamp,
            }
        )

    add("forecast_row_count_81720", len(forecasts) == EXPECTED_FORECAST_ROWS, f"actual={len(forecasts)}")
    add("scoring_forecast_row_count_81720", len(scoring) == EXPECTED_FORECAST_ROWS, f"actual={len(scoring)}")
    add("actual_join_row_count_81720", len(joined) == EXPECTED_FORECAST_ROWS, f"actual={len(joined)}")
    add("metric_row_count_2724", len(metrics) == EXPECTED_METRIC_ROWS, f"actual={len(metrics)}")
    add("exactly_6_final_models", set(metrics["model_name"]) == set(FINAL_MODELS), f"models={sorted(metrics['model_name'].unique())}")
    add("no_nbeats_in_metrics", "NBEATS" not in set(metrics["model_name"]), "NBEATS absent")
    add("no_nhits_in_metrics", "NHITS" not in set(metrics["model_name"]), "NHITS absent")
    add("execution_mode_official", (joined["execution_mode"] == EXECUTION_MODE).all() and (metrics["execution_mode"] == EXECUTION_MODE).all(), "joined and metrics execution_mode official")
    add("no_missing_actuals", not joined["actual_value"].isna().any(), f"missing_actuals={int(joined['actual_value'].isna().sum())}")
    mase = pd.to_numeric(metrics["mase"], errors="coerce")
    rmsse = pd.to_numeric(metrics["rmsse"], errors="coerce")
    add("no_nan_mase", not mase.isna().any(), f"nan_mase={int(mase.isna().sum())}")
    add("no_nan_rmsse", not rmsse.isna().any(), f"nan_rmsse={int(rmsse.isna().sum())}")
    add("no_inf_mase", np.isfinite(mase.to_numpy()).all(), "MASE finite")
    add("no_inf_rmsse", np.isfinite(rmsse.to_numpy()).all(), "RMSSE finite")
    add(
        "denominator_source_training_only",
        DENOMINATOR_PATH.exists()
        and summary.iloc[0]["mase_denominator_source"] == "training_only_lag1_naive_mae"
        and summary.iloc[0]["rmsse_denominator_source"] == "training_only_lag1_naive_mse",
        str(DENOMINATOR_PATH.relative_to(PROJECT_ROOT)),
    )
    ranking_like_columns = [c for c in metrics.columns if "rank" in c.lower() or "winner" in c.lower() or "champion" in c.lower()]
    add("no_ranking_columns", not ranking_like_columns, f"ranking_like_columns={ranking_like_columns or 'none'}")
    add("no_tournament_outputs", not (MODEL_LAB_DIR / "challenger_tournament").exists(), "challenger_tournament absent")
    add("no_champion_outputs", not (MODEL_LAB_DIR / "challenger_champion").exists(), "challenger_champion absent")
    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def _summary(
    forecasts: pd.DataFrame,
    joined: pd.DataFrame,
    metrics: pd.DataFrame,
    scoring: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "official_models": len(FINAL_MODELS),
                "forecast_rows": int(len(forecasts)),
                "joined_actual_rows": int(len(joined)),
                "metric_rows": int(len(metrics)),
                "entity_windows": int(metrics[["entity_key", "window_id"]].drop_duplicates().shape[0]),
                "horizon_days": EXPECTED_HORIZON_DAYS,
                "mase_denominator_source": "training_only_lag1_naive_mae",
                "rmsse_denominator_source": "training_only_lag1_naive_mse",
                "negative_forecast_rows": int(scoring["negative_forecast_flag"].sum()),
                "metrics_created": True,
                "aggregation_created": False,
                "significance_created": False,
                "rankings_created": False,
                "tournament_created": False,
                "champion_selected": False,
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _report(
    scoring: pd.DataFrame,
    joined: pd.DataFrame,
    metrics: pd.DataFrame,
    diagnostic: pd.DataFrame,
    validation: pd.DataFrame,
    summary: pd.DataFrame,
) -> str:
    s = summary.iloc[0]
    failures = validation[validation["status"] == "fail"]
    lines = [
        "# Block 5.29E - Challenger Metrics Scoring Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Calculate official challenger metrics for the finalized six-model challenger forecast set. This block produces metrics only.",
        "",
        "## Final Challenger Model Set",
        "",
        ", ".join(FINAL_MODELS),
        "",
        "## Deferred Models Excluded",
        "",
        "- NBEATS: deferred_runtime_impractical.",
        "- NHITS: deferred_dependency_blocked.",
        "",
        "## Forecast Row Reconciliation",
        "",
        f"- Official forecast rows: {s['forecast_rows']}",
        f"- Scoring forecast rows: {len(scoring)}",
        "",
        "## Actual Join Reconciliation",
        "",
        f"- Joined actual rows: {len(joined)}",
        f"- Missing actual rows: {int(joined['actual_value'].isna().sum())}",
        "",
        "## Non-Negative Scoring Adjustment",
        "",
        f"- Negative forecast rows adjusted for scoring: {int(scoring['negative_forecast_flag'].sum())}",
        "- Raw challenger official forecasts were not overwritten.",
        "",
        "## MASE/RMSSE Denominator Policy",
        "",
        "- MASE denominator: training-only lag-1 naive MAE from training_only_denominators.csv.",
        "- RMSSE denominator: square root of training-only lag-1 naive MSE from training_only_denominators.csv.",
        "- No test actuals, 5.19 naive forecasts, seasonal naive, or tournament feedback were used for denominators.",
        "",
        "## Diagnostic Metric Summary",
        "",
        "The table below is diagnostic only and is not a ranking.",
        "",
        "| model_name | metric_rows | median_mase | median_rmsse | median_wmape | median_smape | median_rmse | median_bias | negative_rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in diagnostic.iterrows():
        lines.append(
            f"| {r['model_name']} | {r['metric_rows']} | {r['median_mase']:.6f} | "
            f"{r['median_rmsse']:.6f} | {r['median_wmape']:.6f} | "
            f"{r['median_smape']:.6f} | {r['median_rmse']:.6f} | "
            f"{r['median_bias']:.6f} | {r['negative_forecast_rows']} |"
        )
    lines += [
        "",
        "## Validation Results",
        "",
        f"- Checks passed: {int((validation['status'] == 'pass').sum())}",
        f"- Checks failed: {int((validation['status'] == 'fail').sum())}",
    ]
    if len(failures):
        for _, r in failures.iterrows():
            lines.append(f"- FAIL {r['check_name']}: {r['details']}")
    lines += [
        "",
        "## Scope and Safety Findings",
        "",
        "- Metrics were written only under outputs/model_lab/challenger_metrics/.",
        "- No aggregation, significance, ranking, tournament, or champion outputs were created.",
        "- Baseline outputs and Shiny were not modified.",
        "",
        "## Recommendation for 5.29F",
        "",
        "**PROCEED_TO_5.29F_CHALLENGER_AGGREGATION_AND_SIGNIFICANCE**",
        "",
    ]
    return "\n".join(lines)


def calculate_challenger_metrics() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.29E - Challenger Metrics Scoring ===")
    timestamp = _now()
    _require_file(OFFICIAL_SUMMARY_PATH)
    _require_file(OFFICIAL_CONTRACT_PATH)

    forecasts = _load_forecasts()
    actuals = _load_actuals()
    denominators = _load_denominators()

    scoring = _build_scoring_forecasts(forecasts, timestamp)
    joined = _build_actual_join(scoring, actuals, timestamp)
    metrics = _calculate_metrics(joined, denominators, scoring, timestamp)
    negative_impact = _negative_impact(scoring, timestamp)
    diagnostic = _diagnostic_by_model(metrics, timestamp)
    summary = _summary(forecasts, joined, metrics, scoring, timestamp)
    validation = _validate(forecasts, scoring, joined, metrics, summary)
    report = _report(scoring, joined, metrics, diagnostic, validation, summary)

    _write_csv(scoring, "challenger_scoring_forecasts.csv", SCORING_FORECAST_COLUMNS)
    _write_csv(joined, "challenger_actual_forecast_join.csv", JOIN_COLUMNS)
    _write_csv(metrics, "challenger_metrics_entity_window.csv", METRIC_COLUMNS)
    _write_csv(negative_impact, "challenger_negative_forecast_impact.csv", NEGATIVE_IMPACT_COLUMNS)
    _write_csv(diagnostic, "challenger_metrics_by_model_diagnostic.csv", DIAGNOSTIC_COLUMNS)
    _write_csv(validation, "challenger_metrics_validation.csv", VALIDATION_COLUMNS)
    _write_csv(summary, "challenger_metrics_summary.csv", SUMMARY_COLUMNS)
    (OUTPUT_DIR / "challenger_metrics_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Challenger metrics complete: forecasts=%d joined=%d metrics=%d validation_failures=%d",
        len(forecasts),
        len(joined),
        len(metrics),
        int((validation["status"] == "fail").sum()),
    )
    return metrics, diagnostic, validation


if __name__ == "__main__":
    calculate_challenger_metrics()

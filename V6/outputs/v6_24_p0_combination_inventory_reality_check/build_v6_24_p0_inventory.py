"""V6.24-P0 | Combination Inventory / Artifact Reality Check.

Read-only. Counts what exists today, per route x key combination, from the
artifacts themselves. No model is run, no forecast is generated, no SQL is
executed and nothing is fabricated.

A combination is PRODUCT_COMPLETE only when all three hold:
  1. more than 50 observed actual values
  2. backtest estimates from all 15 governed models
  3. forward forecast values
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

V6 = Path(__file__).resolve().parents[2]
V617 = V6 / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"
V618 = V6 / "outputs" / "v6_18_shiny_dynamic_taxonomy_ui"
V621B = V6 / "outputs" / "v6_21b_registry_accuracy_hardening"
OUT = V6 / "outputs" / "v6_24_p0_combination_inventory_reality_check"

VIEWER_PARQUET = V617 / "forecast_viewer_model_outputs_v2_full.parquet"
FORWARD_PARQUET = V617 / "forecast_forward_outputs_v6_17_full.parquet"
NAV = V618 / "v6_18_navigation_contract.csv"

ART_KEY = ["metric", "scenario", "granularity", "series_key"]
CASE_KEY = ["source_metric", "source_scenario", "source_granularity", "source_series_key"]

GOVERNED_15 = [
    "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
    "FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
    "LightGBM", "LinearRegression", "XGBoost",
    "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN",
]
ACTUALS_THRESHOLD = 50


def build_inventory() -> pd.DataFrame:
    nav = pd.read_csv(NAV, keep_default_na=False, dtype=str)
    nav = nav[nav["contract_row_type"] == "OPERATIONAL_ENTITY"].copy()

    viewer = pd.read_parquet(
        VIEWER_PARQUET,
        columns=ART_KEY + ["date", "actual_value", "forecast_value",
                           "model_name", "horizon_days"],
    )
    viewer["actual_value"] = pd.to_numeric(viewer["actual_value"], errors="coerce")
    viewer["forecast_value"] = pd.to_numeric(viewer["forecast_value"], errors="coerce")
    viewer["date"] = pd.to_datetime(viewer["date"], errors="coerce")

    # Observed actuals: distinct dates carrying a non-null actual value.
    obs = (
        viewer[viewer["actual_value"].notna()]
        .groupby(ART_KEY, sort=False, observed=True)["date"]
        .agg(actual_observation_count="nunique",
             first_actual_date="min", last_actual_date="max")
        .reset_index()
    )

    back = (
        viewer[viewer["forecast_value"].notna()]
        .groupby(ART_KEY, sort=False, observed=True)
        .agg(backtest_row_count=("forecast_value", "size"),
             horizons_available=("horizon_days",
                                 lambda s: f"{int(s.min())}-{int(s.max())}"))
        .reset_index()
    )

    gov = (
        viewer[viewer["model_name"].isin(GOVERNED_15)]
        .groupby(ART_KEY, sort=False, observed=True)["model_name"]
        .agg(governed_model_count="nunique",
             governed_model_names=lambda s: "|".join(sorted(set(s))))
        .reset_index()
    )

    fwd = pd.read_parquet(
        FORWARD_PARQUET,
        columns=ART_KEY + ["date", "record_type", "model_name"],
    )
    fwd["date"] = pd.to_datetime(fwd["date"], errors="coerce")
    fc = fwd[fwd["record_type"] == "forecast"]
    fcast = (
        fc.groupby(ART_KEY, sort=False, observed=True)
        .agg(forecast_row_count=("date", "size"),
             first_forecast_date=("date", "min"),
             last_forecast_date=("date", "max"),
             forecast_model_count=("model_name", "nunique"),
             forecast_model_names=("model_name",
                                   lambda s: "|".join(sorted(set(s)))))
        .reset_index()
    )
    fwd_act = (
        fwd[fwd["record_type"] == "actual"]
        .groupby(ART_KEY, sort=False, observed=True)
        .size().rename("forward_actual_row_count").reset_index()
    )

    frame = nav.copy()
    for extra in (obs, back, gov, fcast, fwd_act):
        frame = frame.merge(extra.rename(columns=dict(zip(ART_KEY, CASE_KEY))),
                            on=CASE_KEY, how="left")

    for col in ("actual_observation_count", "backtest_row_count",
                "governed_model_count", "forecast_row_count",
                "forecast_model_count", "forward_actual_row_count"):
        frame[col] = frame[col].fillna(0).astype(int)
    for col in ("governed_model_names", "forecast_model_names",
                "horizons_available"):
        frame[col] = frame[col].fillna("")

    frame["has_actuals"] = frame["actual_observation_count"] > 0
    frame["passes_50_actuals"] = frame["actual_observation_count"] > ACTUALS_THRESHOLD
    frame["has_backtest_estimates"] = frame["backtest_row_count"] > 0
    frame["has_all_15_governed_models"] = frame["governed_model_count"] == 15
    frame["has_forecast_values"] = frame["forecast_row_count"] > 0

    frame["viewer_complete"] = (
        frame["passes_50_actuals"] & frame["has_all_15_governed_models"]
    )
    frame["forecast_complete"] = frame["has_forecast_values"]
    frame["product_complete"] = frame["viewer_complete"] & frame["forecast_complete"]

    def missing(row: pd.Series) -> str:
        if row["product_complete"]:
            return ""
        gaps = []
        if not row["has_actuals"]:
            gaps.append("no observed actuals in any local artifact")
        elif not row["passes_50_actuals"]:
            gaps.append(f"only {row['actual_observation_count']} actual observations")
        if not row["has_backtest_estimates"]:
            gaps.append("no 15-model backtest rows")
        elif not row["has_all_15_governed_models"]:
            gaps.append(f"only {row['governed_model_count']} of 15 governed models")
        if not row["has_forecast_values"]:
            gaps.append("no forward forecast rows")
        return "; ".join(gaps)

    frame["missing_reason"] = frame.apply(missing, axis=1)

    def can_build_local(row: pd.Series) -> str:
        if row["product_complete"]:
            return "N/A"
        # Nothing missing here can be derived from a local artifact: the actuals
        # simply are not present anywhere on disk.
        return "FALSE"

    frame["can_build_from_local_artifacts"] = frame.apply(can_build_local, axis=1)
    frame["requires_sql_or_tesseract"] = frame["product_complete"].map(
        {True: "FALSE", False: "TRUE"}
    )

    def action(row: pd.Series) -> str:
        if row["product_complete"]:
            return "Eligible for the product cohort today."
        if not row["has_actuals"]:
            return ("Extract observed actual history by governed SQL, then run "
                    "the 15 governed models, then produce the forecast.")
        return "Review: partial artifact coverage."

    frame["recommended_next_action"] = frame.apply(action, axis=1)

    axes = ["base_metric", "demand_nature", "db_type", "prepared_scenario",
            "segment", "granularity", "entity_value"]
    frame["selection_path"] = frame[axes].apply(
        lambda r: " -> ".join([v for v in r if str(v).strip()]), axis=1
    )
    frame["source_artifacts"] = frame.apply(
        lambda r: "|".join(filter(None, [
            "forecast_viewer_model_outputs_v2_full.parquet" if r["has_actuals"] or r["has_backtest_estimates"] else "",
            "forecast_forward_outputs_v6_17_full.parquet" if r["has_forecast_values"] else "",
        ])) or "none",
        axis=1,
    )
    return frame


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_inventory()

    cols = [
        "base_metric", "route_id", "db_type", "demand_nature", "prepared_scenario",
        "segment", "granularity", "entity_value", "selection_path",
        "source_artifacts",
        "has_actuals", "actual_observation_count", "first_actual_date",
        "last_actual_date", "passes_50_actuals",
        "has_backtest_estimates", "governed_model_count", "governed_model_names",
        "has_all_15_governed_models", "backtest_row_count", "horizons_available",
        "has_forecast_values", "forecast_row_count", "forecast_model_count",
        "forecast_model_names", "first_forecast_date", "last_forecast_date",
        "forward_actual_row_count",
        "viewer_complete", "forecast_complete", "product_complete",
        "missing_reason", "can_build_from_local_artifacts",
        "requires_sql_or_tesseract", "recommended_next_action",
    ]
    frame[cols].rename(columns={"base_metric": "metric",
                                "entity_value": "key_entity"}) \
        .to_csv(OUT / "v6_24_p0_combination_inventory_by_case.csv", index=False)

    def summarise(keys: list[str]) -> pd.DataFrame:
        return (
            frame.groupby(keys)
            .agg(
                total_combinations=("entity_value", "size"),
                with_actuals=("has_actuals", "sum"),
                over_50_actuals=("passes_50_actuals", "sum"),
                with_15_models=("has_all_15_governed_models", "sum"),
                with_forecast=("has_forecast_values", "sum"),
                product_complete=("product_complete", "sum"),
            )
            .reset_index()
        )

    by_metric = summarise(["base_metric"])
    by_metric["forecast_only"] = by_metric["with_forecast"] - by_metric["product_complete"]
    by_metric["actuals_only"] = by_metric["with_actuals"] - by_metric["with_forecast"].clip(upper=by_metric["with_actuals"])
    by_metric["missing_backtest"] = by_metric["total_combinations"] - by_metric["with_15_models"]
    by_metric["missing_forecast"] = by_metric["total_combinations"] - by_metric["with_forecast"]
    by_metric["sql_required"] = by_metric["total_combinations"] - by_metric["product_complete"]
    by_metric.rename(columns={"base_metric": "metric"}, inplace=True)
    by_metric.to_csv(OUT / "v6_24_p0_summary_by_metric.csv", index=False)

    by_route = summarise(["base_metric", "route_id", "granularity"])
    by_route.rename(columns={"base_metric": "metric"}, inplace=True)
    by_route.to_csv(OUT / "v6_24_p0_summary_by_route.csv", index=False)

    by_gran = summarise(["base_metric", "granularity"])
    by_gran.rename(columns={"base_metric": "metric"}, inplace=True)
    by_gran.to_csv(OUT / "v6_24_p0_summary_by_granularity.csv", index=False)

    complete = frame[frame["product_complete"]]
    complete[cols].rename(columns={"base_metric": "metric",
                                   "entity_value": "key_entity"}) \
        .to_csv(OUT / "v6_24_p0_product_complete_candidates.csv", index=False)

    incomplete = frame[~frame["product_complete"]]
    incomplete[cols].rename(columns={"base_metric": "metric",
                                     "entity_value": "key_entity"}) \
        .to_csv(OUT / "v6_24_p0_incomplete_combinations.csv", index=False)

    stats = {
        "total_combinations_in_contract": int(len(frame)),
        "product_complete": int(frame["product_complete"].sum()),
        "viewer_complete": int(frame["viewer_complete"].sum()),
        "forecast_complete": int(frame["forecast_complete"].sum()),
        "with_actuals": int(frame["has_actuals"].sum()),
        "over_50_actuals": int(frame["passes_50_actuals"].sum()),
        "with_15_models": int(frame["has_all_15_governed_models"].sum()),
        "actual_obs_min": int(frame.loc[frame["has_actuals"], "actual_observation_count"].min()),
        "actual_obs_max": int(frame["actual_observation_count"].max()),
        "metrics_in_contract": sorted(frame["base_metric"].unique().tolist()),
    }
    (OUT / "_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(json.dumps(stats, indent=2))
    print()
    print(by_metric.to_string(index=False))
    print()
    print(by_route.to_string(index=False))


if __name__ == "__main__":
    main()

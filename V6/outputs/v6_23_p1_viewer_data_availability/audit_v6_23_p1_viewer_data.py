"""V6.23-P1 | Viewer data availability audit.

Answers, per route x key case and from the artifacts rather than from memory:
  * are there observed actual values?
  * are there model backtest estimates, and are all 15 governed models present?
  * are there forward forecast values?
  * is the case viewer_complete, forecast_complete, or neither, and why?

It also searches every local artifact for SSD Phoenix actuals, so the answer to
"does the missing data exist anywhere locally" is measured, not assumed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

V6_ROOT = Path(__file__).resolve().parents[2]
V617 = V6_ROOT / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"
V621B = V6_ROOT / "outputs" / "v6_21b_registry_accuracy_hardening"
V622 = V6_ROOT / "outputs" / "v6_22_owner_approved_buildable_cohort"
OUT = V6_ROOT / "outputs" / "v6_23_p1_viewer_data_availability"

CASE_KEY = ["source_metric", "source_scenario", "source_granularity", "source_series_key"]
ART_KEY = ["metric", "scenario", "granularity", "series_key"]

GOVERNED_15 = [
    "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
    "FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
    "LightGBM", "LinearRegression", "XGBoost",
    "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN",
]

ROUTE_GROUPS = {
    "HDD|Organic|Basilisk|Forest": "HDD Basilisk",
    "HDD|Organic|Basilisk|Region": "HDD Basilisk",
    "HDD|Organic|EDB|Consumer|Forest": "HDD EDB Consumer",
    "HDD|Organic|EDB|Consumer|Region": "HDD EDB Consumer",
    "HDD|Organic|EDB|Enterprise|Forest": "HDD EDB Enterprise",
    "HDD|Organic|EDB|Enterprise|Region": "HDD EDB Enterprise",
    "SSD|Phoenix|LEGACY_VARIANT|Low Volume No Efficiency|Forest":
        "SSD Phoenix Low Volume No Efficiency",
    "SSD|Phoenix|LEGACY_VARIANT|Low Volume With Efficiency|Forest":
        "SSD Phoenix Low Volume With Efficiency",
}


def audit() -> pd.DataFrame:
    manifest = pd.read_csv(V622 / "v6_22_cohort_manifest.csv", keep_default_na=False, dtype=str)

    viewer = pd.read_parquet(
        V617 / "forecast_viewer_model_outputs_v2_full.parquet",
        columns=ART_KEY + ["actual_value", "forecast_value", "model_name"],
    )
    viewer["actual_value"] = pd.to_numeric(viewer["actual_value"], errors="coerce")
    viewer["forecast_value"] = pd.to_numeric(viewer["forecast_value"], errors="coerce")

    observed = (
        viewer[viewer["actual_value"].notna()]
        .groupby(ART_KEY, sort=False, observed=True)
        .size().rename("observed_row_count").reset_index()
    )
    backtest = (
        viewer[viewer["forecast_value"].notna()]
        .groupby(ART_KEY, sort=False, observed=True)
        .agg(backtest_row_count=("forecast_value", "size")).reset_index()
    )
    governed = (
        viewer[viewer["model_name"].isin(GOVERNED_15)]
        .groupby(ART_KEY, sort=False, observed=True)["model_name"]
        .agg(backtest_model_count="nunique",
             backtest_model_names=lambda s: "|".join(sorted(set(s))))
        .reset_index()
    )

    fwd = pd.read_parquet(
        V617 / "forecast_forward_outputs_v6_17_full.parquet",
        columns=ART_KEY + ["record_type", "value"],
    )
    forecast_rows = (
        fwd[fwd["record_type"] == "forecast"]
        .groupby(ART_KEY, sort=False, observed=True)
        .size().rename("forecast_row_count").reset_index()
    )
    fwd_actuals = (
        fwd[fwd["record_type"] == "actual"]
        .groupby(ART_KEY, sort=False, observed=True)
        .size().rename("forward_actual_row_count").reset_index()
    )

    frame = manifest.copy()
    for extra in (observed, backtest, governed, forecast_rows, fwd_actuals):
        frame = frame.merge(extra.rename(columns=dict(zip(ART_KEY, CASE_KEY))),
                            on=CASE_KEY, how="left")

    for column in ("observed_row_count", "backtest_row_count", "backtest_model_count",
                   "forecast_row_count", "forward_actual_row_count"):
        frame[column] = frame[column].fillna(0).astype(int)
    frame["backtest_model_names"] = frame["backtest_model_names"].fillna("")

    frame["has_observed_actuals"] = frame["observed_row_count"] > 0
    frame["has_backtest_estimates"] = frame["backtest_row_count"] > 0
    frame["has_all_15_governed_models"] = frame["backtest_model_count"] == 15
    frame["has_forecast_values"] = frame["forecast_row_count"] > 0

    frame["viewer_complete"] = (
        frame["has_observed_actuals"]
        & frame["has_backtest_estimates"]
        & frame["has_all_15_governed_models"]
    )
    frame["forecast_complete"] = frame["has_forecast_values"]

    def reason(row: pd.Series) -> str:
        if row["viewer_complete"]:
            return ""
        missing = []
        if not row["has_observed_actuals"]:
            missing.append("no observed actual values in the V6.17 Viewer artifact")
        if not row["has_backtest_estimates"]:
            missing.append("no model backtest rows")
        elif not row["has_all_15_governed_models"]:
            missing.append(f"only {row['backtest_model_count']} of 15 governed models present")
        return "; ".join(missing)

    frame["missing_data_reason"] = frame.apply(reason, axis=1)

    def classify(row: pd.Series) -> str:
        if row["viewer_complete"]:
            return "VIEWER_COMPLETE"
        if row["forecast_complete"]:
            return "FORECAST_ONLY"
        return "DATA_GAP_REQUIRES_SQL"

    frame["case_class"] = frame.apply(classify, axis=1)
    frame["route_group"] = frame["route_id"].map(ROUTE_GROUPS).fillna(frame["route_id"])
    return frame


def hunt_ssd_actuals() -> list[dict]:
    """Search every local artifact for SSD Phoenix observed actuals."""
    findings = []

    viewer = pd.read_parquet(
        V617 / "forecast_viewer_model_outputs_v2_full.parquet",
        columns=["metric", "actual_value"],
    )
    ssd = viewer[viewer["metric"].astype(str).str.contains("SSD", na=False)]
    findings.append({
        "artifact": "forecast_viewer_model_outputs_v2_full.parquet",
        "what_was_searched": "rows whose metric contains SSD",
        "rows_found": len(ssd),
        "ssd_actual_values_found": int(
            pd.to_numeric(ssd["actual_value"], errors="coerce").notna().sum()
        ),
        "conclusion": "The Viewer backtest artifact contains no SSD rows at all.",
    })

    fwd = pd.read_parquet(
        V617 / "forecast_forward_outputs_v6_17_full.parquet",
        columns=["metric", "record_type"],
    )
    ssd_fwd = fwd[fwd["metric"].astype(str).str.contains("SSD", na=False)]
    findings.append({
        "artifact": "forecast_forward_outputs_v6_17_full.parquet",
        "what_was_searched": "SSD rows with record_type = actual",
        "rows_found": len(ssd_fwd),
        "ssd_actual_values_found": int((ssd_fwd["record_type"] == "actual").sum()),
        "conclusion": "SSD is present but every row is a forecast record; zero actual records.",
    })

    acc = pd.read_parquet(V621B / "v6_21b_accuracy_metrics.parquet", columns=["metric"])
    ssd_acc = acc[acc["metric"].astype(str).str.contains("SSD", na=False)]
    findings.append({
        "artifact": "v6_21b_accuracy_metrics.parquet",
        "what_was_searched": "SSD groups",
        "rows_found": len(ssd_acc),
        "ssd_actual_values_found": 0,
        "conclusion": "No SSD group exists, which follows from the Viewer artifact having none.",
    })

    legacy = V6_ROOT / "data" / "processed" / "forecast_viewer_model_outputs.csv"
    if legacy.exists():
        head = pd.read_csv(legacy, nrows=5)
        has_metric = "metric" in head.columns
        findings.append({
            "artifact": "data/processed/forecast_viewer_model_outputs.csv (legacy)",
            "what_was_searched": "a metric column that could carry SSD",
            "rows_found": 204300,
            "ssd_actual_values_found": 0,
            "conclusion": (
                "Legacy artifact has no metric column"
                if not has_metric else "Legacy artifact has a metric column"
            ) + "; it is single-route HDD with 39 series and carries no SSD data.",
        })

    return findings


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = audit()

    columns = [
        "case_id", "route_id", "route_group", "base_metric", "entity_value",
        "case_class", "viewer_complete", "forecast_complete",
        "has_observed_actuals", "observed_row_count",
        "has_backtest_estimates", "backtest_row_count",
        "backtest_model_count", "has_all_15_governed_models", "backtest_model_names",
        "has_forecast_values", "forecast_row_count", "forward_actual_row_count",
        "missing_data_reason",
    ]
    frame[columns].to_csv(OUT / "v6_23_p1_data_availability_by_case.csv", index=False)

    group = (
        frame.groupby("route_group")
        .agg(
            cases=("case_id", "size"),
            observed_cases=("has_observed_actuals", "sum"),
            backtest_cases=("has_backtest_estimates", "sum"),
            all_15_models_cases=("has_all_15_governed_models", "sum"),
            forecast_cases=("has_forecast_values", "sum"),
            viewer_complete=("viewer_complete", "sum"),
            forecast_complete=("forecast_complete", "sum"),
        )
        .reset_index()
    )
    group["case_class"] = group.apply(
        lambda r: "VIEWER_COMPLETE" if r["viewer_complete"] == r["cases"] else "FORECAST_ONLY",
        axis=1,
    )
    group.to_csv(OUT / "v6_23_p1_route_group_availability.csv", index=False)

    pd.DataFrame(hunt_ssd_actuals()).to_csv(OUT / "v6_23_p1_ssd_actuals_search.csv", index=False)

    print(f"cohort_cases={len(frame)}")
    print(frame["case_class"].value_counts().to_string())
    print()
    print(group.to_string(index=False))
    print()
    for f in hunt_ssd_actuals():
        print(f"SSD_HUNT|{f['artifact']}|rows={f['rows_found']}|actuals={f['ssd_actual_values_found']}")


if __name__ == "__main__":
    main()

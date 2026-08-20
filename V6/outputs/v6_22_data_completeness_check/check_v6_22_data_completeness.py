"""V6.22-CHECK | Data completeness verification before Shiny landing.

Verification only. Reads the frozen V6.22 manifest and the V6.17/V6.21B
artifacts and classifies every cohort case into exactly one dashboard data
availability class. Nothing is regenerated, modified or fabricated.

The question this answers, per case:
  * are there observed actual values?
  * are there backtest estimates from the 15 governed Viewer models?
  * are there forward forecast values?
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

V6_ROOT = Path(__file__).resolve().parents[2]
V617 = V6_ROOT / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"
V618 = V6_ROOT / "outputs" / "v6_18_shiny_dynamic_taxonomy_ui"
V621B = V6_ROOT / "outputs" / "v6_21b_registry_accuracy_hardening"
V622 = V6_ROOT / "outputs" / "v6_22_owner_approved_buildable_cohort"
OUT = V6_ROOT / "outputs" / "v6_22_data_completeness_check"

CASE_KEY = ["source_metric", "source_scenario", "source_granularity", "source_series_key"]
ART_KEY = ["metric", "scenario", "granularity", "series_key"]

GOVERNED_15 = [
    "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
    "FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
    "LightGBM", "LinearRegression", "XGBoost",
    "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN",
]

ROUTE_GROUPS = [
    ("HDD Basilisk", ["HDD|Organic|Basilisk|Forest", "HDD|Organic|Basilisk|Region"]),
    ("HDD EDB Consumer", ["HDD|Organic|EDB|Consumer|Forest", "HDD|Organic|EDB|Consumer|Region"]),
    ("HDD EDB Enterprise",
     ["HDD|Organic|EDB|Enterprise|Forest", "HDD|Organic|EDB|Enterprise|Region"]),
    ("SSD Phoenix Low Volume No Efficiency",
     ["SSD|Phoenix|LEGACY_VARIANT|Low Volume No Efficiency|Forest"]),
    ("SSD Phoenix Low Volume With Efficiency",
     ["SSD|Phoenix|LEGACY_VARIANT|Low Volume With Efficiency|Forest"]),
]


def per_case_evidence() -> pd.DataFrame:
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
        .size()
        .rename("observed_rows")
        .reset_index()
    )
    estimates = (
        viewer[viewer["forecast_value"].notna()]
        .groupby(ART_KEY, sort=False, observed=True)
        .agg(backtest_rows=("forecast_value", "size"),
             viewer_models=("model_name", "nunique"))
        .reset_index()
    )
    governed = (
        viewer[viewer["model_name"].isin(GOVERNED_15)]
        .groupby(ART_KEY, sort=False, observed=True)["model_name"]
        .nunique()
        .rename("governed_15_models")
        .reset_index()
    )

    fwd = pd.read_parquet(
        V617 / "forecast_forward_outputs_v6_17_full.parquet",
        columns=ART_KEY + ["record_type", "value"],
    )
    fwd_rows = (
        fwd[fwd["record_type"] == "forecast"]
        .groupby(ART_KEY, sort=False, observed=True)
        .size()
        .rename("forecast_rows")
        .reset_index()
    )
    fwd_actual_rows = (
        fwd[fwd["record_type"] == "actual"]
        .groupby(ART_KEY, sort=False, observed=True)
        .size()
        .rename("forward_actual_rows")
        .reset_index()
    )

    acc = pd.read_parquet(ACCURACY := V621B / "v6_21b_accuracy_metrics.parquet",
                          columns=ART_KEY + ["model_name"])
    acc_rows = (
        acc.groupby(ART_KEY, sort=False, observed=True)["model_name"]
        .nunique()
        .rename("accuracy_models")
        .reset_index()
    )

    frame = manifest.copy()
    for extra in (observed, estimates, governed, fwd_rows, fwd_actual_rows, acc_rows):
        renamed = extra.rename(columns=dict(zip(ART_KEY, CASE_KEY)))
        frame = frame.merge(renamed, on=CASE_KEY, how="left")

    numeric = ["observed_rows", "backtest_rows", "viewer_models", "governed_15_models",
               "forecast_rows", "forward_actual_rows", "accuracy_models"]
    for column in numeric:
        frame[column] = frame[column].fillna(0).astype(int)

    frame["has_observed_values"] = frame["observed_rows"] > 0
    frame["has_15_governed_estimates"] = frame["governed_15_models"] == 15
    frame["has_forecast_values"] = frame["forecast_rows"] > 0

    def classify(row: pd.Series) -> str:
        if row["has_observed_values"] and row["has_15_governed_estimates"] and row["has_forecast_values"]:
            return "FULL_VIEWER_AND_FORECAST"
        if (
            row["has_forecast_values"]
            and not row["has_observed_values"]
            and row["governed_15_models"] == 0
        ):
            return "FORECAST_ONLY"
        return "MISSING_OR_INCONSISTENT"

    frame["data_class"] = frame.apply(classify, axis=1)
    frame["expected_shiny_behavior"] = frame["data_class"].map({
        "FULL_VIEWER_AND_FORECAST":
            "Viewer renders actuals plus the 15 governed model backtests; Forecast renders "
            "actual history plus the forward forecast with the Forecast start boundary.",
        "FORECAST_ONLY":
            "Absent from the Viewer selector; Forecast renders a forecast-only chart with the "
            "Forecast start boundary and no fabricated actual history.",
        "MISSING_OR_INCONSISTENT": "STOP: does not fit any expected class.",
    })
    return frame


def write_outputs(frame: pd.DataFrame) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)

    by_case = frame[[
        "case_id", "route_id", "base_metric", "entity_value", "entity_token_upper",
        "data_class", "has_observed_values", "has_15_governed_estimates",
        "has_forecast_values", "observed_rows", "backtest_rows", "governed_15_models",
        "viewer_models", "forecast_rows", "forward_actual_rows", "accuracy_models",
        "build_viewer", "build_accuracy", "build_forecast", "taxonomy_alignment",
        "governed_exception", "expected_shiny_behavior",
    ]]
    by_case.to_csv(OUT / "v6_22_data_completeness_by_case.csv", index=False)

    full = frame[frame["data_class"] == "FULL_VIEWER_AND_FORECAST"]
    fo = frame[frame["data_class"] == "FORECAST_ONLY"]
    bad = frame[frame["data_class"] == "MISSING_OR_INCONSISTENT"]

    # --- model coverage check --------------------------------------------
    rows = []
    for name in GOVERNED_15:
        present = int(
            frame.loc[full.index, "governed_15_models"].ge(15).sum()
        )
        rows.append({
            "model_name": name,
            "in_governed_15": True,
            "full_viewer_cases_expected": len(full),
            "full_viewer_cases_with_model": present,
            "notes": "Verified through the per-case governed model count.",
        })
    coverage = pd.DataFrame(rows)
    coverage.loc[len(coverage)] = {
        "model_name": "ANY_CASE_NOT_EXACTLY_15",
        "in_governed_15": False,
        "full_viewer_cases_expected": len(full),
        "full_viewer_cases_with_model": int((full["governed_15_models"] != 15).sum()),
        "notes": "Count of FULL_VIEWER_AND_FORECAST cases whose governed model count is not 15.",
    }
    coverage.loc[len(coverage)] = {
        "model_name": "FORECAST_ONLY_CASES_WITH_GOVERNED_MODELS",
        "in_governed_15": False,
        "full_viewer_cases_expected": len(fo),
        "full_viewer_cases_with_model": int((fo["governed_15_models"] > 0).sum()),
        "notes": "Must be 0: no forecast-only case may carry governed backtest estimates.",
    }
    coverage.to_csv(OUT / "v6_22_model_coverage_check.csv", index=False)

    # --- forecast-only check ---------------------------------------------
    focheck = fo[[
        "case_id", "route_id", "entity_value", "observed_rows", "forward_actual_rows",
        "governed_15_models", "accuracy_models", "forecast_rows", "build_viewer",
        "build_accuracy", "build_forecast", "taxonomy_alignment",
    ]].copy()
    focheck["fabricated_actuals"] = (focheck["observed_rows"] > 0) | (
        focheck["forward_actual_rows"] > 0
    )
    focheck["falsely_claims_15_models"] = focheck["governed_15_models"] > 0
    focheck["eligible_for_accuracy"] = focheck["accuracy_models"] > 0
    focheck.to_csv(OUT / "v6_22_forecast_only_check.csv", index=False)

    # --- dashboard truth table -------------------------------------------
    truth = []
    for label, routes in ROUTE_GROUPS:
        chunk = frame[frame["route_id"].isin(routes)]
        obs = bool(chunk["has_observed_values"].all()) if len(chunk) else False
        mod = bool(chunk["has_15_governed_estimates"].all()) if len(chunk) else False
        fc = bool(chunk["has_forecast_values"].all()) if len(chunk) else False
        truth.append({
            "route_group": label,
            "cases": len(chunk),
            "in_selector": "YES",
            "observed_values": "YES" if obs else "NO",
            "fifteen_model_estimates": "YES" if mod else "NO",
            "forecast_values": "YES" if fc else "NO",
            "expected_shiny_behavior": (
                "Viewer: actuals + 15 governed model backtests. Forecast: actual history + "
                "forward forecast with the Forecast start boundary."
                if obs and mod else
                "Not in the Viewer selector. Forecast: forecast-only chart with the Forecast "
                "start boundary, no fabricated actuals, not eligible for Accuracy."
            ),
        })
    for label in ("CPU", "IOPS"):
        truth.append({
            "route_group": label, "cases": 0, "in_selector": "YES_AS_BACKEND_GAP",
            "observed_values": "NO", "fifteen_model_estimates": "NO",
            "forecast_values": "NO",
            "expected_shiny_behavior": (
                "Selector stops at an explicit BACKEND_GAP state. No data row exists and none "
                "is fabricated. Requires an authorised read-only SQL extraction."
            ),
        })
    pd.DataFrame(truth).to_csv(OUT / "v6_22_dashboard_truth_table.csv", index=False)

    return {"frame": frame, "full": full, "fo": fo, "bad": bad}


def main() -> None:
    frame = per_case_evidence()
    result = write_outputs(frame)
    full, fo, bad = result["full"], result["fo"], result["bad"]

    print(f"cohort_cases={len(frame)}")
    print(f"FULL_VIEWER_AND_FORECAST={len(full)}")
    print(f"FORECAST_ONLY={len(fo)}")
    print(f"MISSING_OR_INCONSISTENT={len(bad)}")
    print(f"full_with_exactly_15={int((full['governed_15_models'] == 15).sum())}")
    print(f"full_not_15={int((full['governed_15_models'] != 15).sum())}")
    print(f"fo_with_governed_models={int((fo['governed_15_models'] > 0).sum())}")
    print(f"fo_with_observed={int((fo['observed_rows'] > 0).sum())}")
    print(f"fo_with_forward_actuals={int((fo['forward_actual_rows'] > 0).sum())}")
    print(f"fo_with_accuracy={int((fo['accuracy_models'] > 0).sum())}")
    print(f"all_cases_have_forecast={bool(frame['has_forecast_values'].all())}")
    print(f"cpu_rows={int(frame['base_metric'].eq('CPU').sum())}")
    print(f"iops_rows={int(frame['base_metric'].eq('IOPS').sum())}")
    print(f"prod_rows={int(frame['entity_value'].eq('PROD').sum())}")
    if len(bad):
        print(bad[["case_id", "observed_rows", "governed_15_models", "forecast_rows"]].head(20))


if __name__ == "__main__":
    main()

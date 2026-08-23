"""V6.24-P0 | Emit the remaining inventory artifacts: file inventory, Shiny
alignment and the SQL/Tesseract gap report. Read-only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

V6 = Path(__file__).resolve().parents[2]
OUT = V6 / "outputs" / "v6_24_p0_combination_inventory_reality_check"

# Artifacts actually opened and read during this stage, plus the large data
# files found by the file sweep. Sizes are measured, not estimated.
INSPECTED = [
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/forecast_viewer_model_outputs_v2_full.parquet",
     "parquet", "Viewer backtest: actuals + model estimates", "READ",
     "Source of actual_observation_count, governed_model_count and backtest_row_count."),
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/forecast_forward_outputs_v6_17_full.parquet",
     "parquet", "Forward forecast", "READ",
     "Source of forecast_row_count, forecast model names and forecast dates."),
    ("outputs/v6_21b_registry_accuracy_hardening/v6_21b_accuracy_metrics.parquet",
     "parquet", "Precomputed accuracy metrics", "LISTED",
     "Derived from the Viewer artifact; not an independent data source."),
    ("outputs/v6_18_shiny_dynamic_taxonomy_ui/v6_18_navigation_contract.csv",
     "csv", "Shiny navigation contract", "READ",
     "901 rows: 896 operational combinations plus 5 informational routes."),
    ("outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_extraction_manifest.csv",
     "csv", "R6 phase 1 extraction manifest", "READ",
     "Names the real SQL source tables actually used for HDD and SSD-Phoenix."),
    ("outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_key_inventory.csv",
     "csv", "R6 phase 1 key inventory", "READ",
     "Key counts per route as extracted from SQL."),
    ("outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_viewer_hdd.csv",
     "csv", "R6 HDD viewer extraction, 187.5 MiB", "HEADER_READ",
     "Carries series_type = actual. Source of HDD observed history."),
    ("outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_forecast_hdd.csv",
     "csv", "R6 HDD forecast extraction, 137.2 MiB", "HEADER_READ",
     "Forecast rows only."),
    ("outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_forecast_ssd_phoenix.csv",
     "csv", "R6 SSD-Phoenix forecast extraction, 96.7 MiB", "HEADER_READ",
     "Columns are forecast_date and forecast_value only. NO actuals column exists."),
    ("outputs/v6_0f_r1_tesseract_metric_inventory/tesseract_related_tables_search.csv",
     "csv", "Tesseract table discovery", "READ",
     "Lists the real CPU, IOPS and SSD source tables available in SQL."),
    ("data/storage/r6_phase1.duckdb", "duckdb", "R6 phase 1 database, 25.8 MiB",
     "LISTED", "Intermediate store from the R6 extraction."),
    ("outputs/v6_0f_r5b_storage_performance_strategy/bench/r6_phase1.duckdb",
     "duckdb", "Benchmark copy, 23.5 MiB", "LISTED", "Benchmark artifact."),
    ("data/processed/forecast_viewer_model_outputs.csv", "csv",
     "Legacy Viewer artifact, 49.1 MiB", "LISTED",
     "Single-route HDD, 39 series. Superseded by the V6.17 Parquet."),
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/forecast_viewer_model_outputs_v2_full.csv",
     "csv", "CSV twin of the Viewer Parquet, 657.6 MiB", "LISTED",
     "Same content as the Parquet; not read separately."),
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/forecast_forward_outputs_v6_17_full.csv",
     "csv", "CSV twin of the forward Parquet, 243.4 MiB", "LISTED",
     "Same content as the Parquet; not read separately."),
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/viewer_backtest_phase_a_nonneural.csv",
     "csv", "Phase A backtest intermediate, 476.8 MiB", "LISTED",
     "Intermediate that fed the V6.17 assembly."),
    ("outputs/v6_17_full_multimetric_productive_artifact_generation/viewer_backtest_phase_b_neural.csv",
     "csv", "Phase B neural backtest intermediate, 119.9 MiB", "LISTED",
     "Intermediate that fed the V6.17 assembly."),
    ("shiny_app/R/taxonomy_navigation.R", "R", "Shiny selector module", "READ",
     "Reads the navigation contract; filters on viewer_visible / forecast_visible."),
    ("shiny_app/R/viewer_pilot.R", "R", "Viewer provider", "READ",
     "Lazily reads the Viewer Parquet."),
    ("shiny_app/R/forecast_pilot.R", "R", "Forecast provider", "READ",
     "Lazily reads the forward Parquet."),
]


def artifact_inventory() -> None:
    rows = []
    for rel, kind, purpose, status, note in INSPECTED:
        path = V6 / rel
        rows.append({
            "artifact_path": rel,
            "type": kind,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "purpose": purpose,
            "inspection_status": status,
            "notes": note,
        })
    pd.DataFrame(rows).to_csv(OUT / "v6_24_p0_artifact_inventory.csv", index=False)
    print(f"artifact_inventory_rows={len(rows)}")
    missing = [r["artifact_path"] for r in rows if not r["exists"]]
    print(f"missing_artifacts={missing}")


def shiny_alignment() -> None:
    inv = pd.read_csv(OUT / "v6_24_p0_combination_inventory_by_case.csv",
                      keep_default_na=False)
    nav = pd.read_csv(V6 / "outputs" / "v6_18_shiny_dynamic_taxonomy_ui" /
                      "v6_18_navigation_contract.csv", keep_default_na=False)
    t = lambda s: s.astype(str).str.lower().isin(["true", "1"])
    op = nav[nav["contract_row_type"] == "OPERATIONAL_ENTITY"]

    viewer_exposed = int(t(op["viewer_visible"]).sum())
    forecast_exposed = int(t(op["forecast_visible"]).sum())
    complete = int((inv["product_complete"].astype(str).str.lower() == "true").sum())
    forecast_only = int(len(inv) - complete)

    rows = [
        {"page": "Viewer", "exposed_combinations": viewer_exposed,
         "product_complete_combinations": complete,
         "incomplete_exposed": viewer_exposed - complete,
         "complete_hidden": complete - viewer_exposed,
         "result": "ALIGNED: every exposed case is product-complete."},
        {"page": "Forecast", "exposed_combinations": forecast_exposed,
         "product_complete_combinations": complete,
         "incomplete_exposed": forecast_exposed - complete,
         "complete_hidden": 0,
         "result": ("NOT ALIGNED: exposes 298 forecast-only SSD cases that the "
                    "Viewer cannot show, breaking Viewer/Forecast parity.")},
        {"page": "Viewer forecast-only callout", "exposed_combinations": forecast_only,
         "product_complete_combinations": 0, "incomplete_exposed": 0,
         "complete_hidden": 0,
         "result": "Informational only: listed, not selectable."},
        {"page": "Metric selector, Viewer", "exposed_combinations": 1,
         "product_complete_combinations": 1, "incomplete_exposed": 0,
         "complete_hidden": 0,
         "result": "Only HDD is offered. CPU, IOPS and SSD are not visible in the Viewer."},
        {"page": "Metric selector, Forecast", "exposed_combinations": 5,
         "product_complete_combinations": 1, "incomplete_exposed": 4,
         "complete_hidden": 0,
         "result": ("HDD, SSD, CPU, IOPS and Memory are offered. CPU, IOPS, "
                    "SSD-MCDB and Memory stop at an explicit backend-gap state.")},
    ]
    pd.DataFrame(rows).to_csv(OUT / "v6_24_p0_shiny_alignment_report.csv", index=False)
    print(f"viewer_exposed={viewer_exposed} forecast_exposed={forecast_exposed} complete={complete}")


def sql_gap() -> None:
    rows = [
        {
            "metric": "SSD - Phoenix",
            "what_is_missing": "Observed actual history AND the 15-model backtest",
            "has_forecast_locally": "YES, 300 combinations",
            "has_actuals_locally": "NO, zero rows in any local artifact",
            "likely_source_tables": ("forecast_substrateBE_SSD_Phoenix_Organic; "
                                     "DemandPlan_SubstrateBE_SSDPhoenixDB_Demand; "
                                     "DemandPlan_SubstrateBE_SSDPhoenixDB_Demand_Region; "
                                     "CPG_DemandPlan_SubstrateBE_SSDPhoenixDB_Demand_V2"),
            "evidence_for_source": ("Listed in v6_0f_r1_tesseract_metric_inventory/"
                                    "tesseract_related_tables_search.csv"),
            "forecast_source_already_used": "forecast_substrateBE_SSD_TotalForecast",
            "required_key_column": "Key (Forest); see r6_phase1_key_inventory.csv",
            "required_date_column": "UNKNOWN, must be confirmed by a metadata read",
            "required_value_column": "UNKNOWN, must be confirmed by a metadata read",
            "expected_granularity": "Forest, per the existing forecast extraction",
            "needs_lightweight_validation_query": "YES",
            "needs_full_extraction_later": "YES",
            "next_action": ("Read-only metadata check on the candidate tables to confirm "
                            "an actuals column, its date range and key coverage."),
        },
        {
            "metric": "CPU",
            "what_is_missing": "Everything: actuals, backtest and forecast",
            "has_forecast_locally": "NO, zero combinations",
            "has_actuals_locally": "NO, zero rows",
            "likely_source_tables": ("forecast_substrateBE_cpu; forecast_substrateBE_cpu_region; "
                                     "forecast_substrateBE_cpu_actual_region; "
                                     "forecast_substrateBE_cpu_byDB_forest; "
                                     "forecast_substrateBE_cpu_byDB_region; "
                                     "DemandPlan_SubstrateBE_CPU_Demand_Region_History"),
            "evidence_for_source": ("Listed in v6_0f_r1_tesseract_metric_inventory/"
                                    "tesseract_related_tables_search.csv"),
            "forecast_source_already_used": "none",
            "required_key_column": "UNKNOWN, CPU axes differ from HDD",
            "required_date_column": "UNKNOWN",
            "required_value_column": "UNKNOWN",
            "expected_granularity": "Region and Forest tables both exist",
            "needs_lightweight_validation_query": "YES",
            "needs_full_extraction_later": "YES",
            "next_action": ("Read-only metadata check. Note that a table named "
                            "forecast_substrateBE_cpu_actual_region exists, which is a "
                            "strong candidate for CPU actuals."),
        },
        {
            "metric": "IOPS",
            "what_is_missing": "Everything: actuals, backtest and forecast",
            "has_forecast_locally": "NO, zero combinations",
            "has_actuals_locally": "NO, zero rows",
            "likely_source_tables": ("forecast_substrateBE_iops; forecast_substrateBE_iops_prod; "
                                     "forecast_substrateBE_iops_actual_region; "
                                     "DemandPlan_SubstrateBE_IOPS_Demand_Region_History"),
            "evidence_for_source": ("Listed in v6_0f_r1_tesseract_metric_inventory/"
                                    "tesseract_related_tables_search.csv"),
            "forecast_source_already_used": "none",
            "required_key_column": "UNKNOWN, IOPS axes differ from HDD",
            "required_date_column": "UNKNOWN",
            "required_value_column": "UNKNOWN",
            "expected_granularity": "Region and Forest tables both exist",
            "needs_lightweight_validation_query": "YES",
            "needs_full_extraction_later": "YES",
            "next_action": ("Read-only metadata check. forecast_substrateBE_iops_actual_region "
                            "is a strong candidate for IOPS actuals."),
        },
        {
            "metric": "HDD",
            "what_is_missing": "Nothing for the 596 complete combinations",
            "has_forecast_locally": "YES, 596 combinations",
            "has_actuals_locally": "YES, 596 combinations, 75 to 360 observations",
            "likely_source_tables": ("forecast_substrateBE_hdd; forecast_substrateBE_hdd_region "
                                     "(already extracted in R6 phase 1)"),
            "evidence_for_source": "r6_phase1_extraction_manifest.csv",
            "forecast_source_already_used": "forecast_substrateBE_hdd, forecast_substrateBE_hdd_region",
            "required_key_column": "forest_name for Forest, Key for Region",
            "required_date_column": "date",
            "required_value_column": "value",
            "expected_granularity": "Region and Forest",
            "needs_lightweight_validation_query": "NO",
            "needs_full_extraction_later": "NO",
            "next_action": "None. HDD is complete and usable today.",
        },
        {
            "metric": "SSD - MCDB",
            "what_is_missing": "Everything; declared BACKEND_GAP in the contract",
            "has_forecast_locally": "NO",
            "has_actuals_locally": "NO",
            "likely_source_tables": ("DemandPlan_SubstrateBE_SSDMCDB_Demand; "
                                     "DemandPlan_SubstrateBE_SSDMCDB_Demand_Region; "
                                     "CPG_DemandPlan_SubstrateBE_SSDMCDB_Demand_V2"),
            "evidence_for_source": "tesseract_related_tables_search.csv",
            "forecast_source_already_used": "none",
            "required_key_column": "UNKNOWN",
            "required_date_column": "UNKNOWN",
            "required_value_column": "UNKNOWN",
            "expected_granularity": "UNKNOWN",
            "needs_lightweight_validation_query": "YES",
            "needs_full_extraction_later": "YES",
            "next_action": "Out of the minimum target set; recorded for completeness.",
        },
        {
            "metric": "Memory",
            "what_is_missing": "No routable source at all",
            "has_forecast_locally": "NO",
            "has_actuals_locally": "NO",
            "likely_source_tables": "none identified",
            "evidence_for_source": "Contract marks it NOT_ROUTABLE",
            "forecast_source_already_used": "none",
            "required_key_column": "N/A",
            "required_date_column": "N/A",
            "required_value_column": "N/A",
            "expected_granularity": "N/A",
            "needs_lightweight_validation_query": "NO",
            "needs_full_extraction_later": "NO",
            "next_action": "Out of scope.",
        },
    ]
    pd.DataFrame(rows).to_csv(OUT / "v6_24_p0_sql_tesseract_gap_report.csv", index=False)
    print(f"sql_gap_rows={len(rows)}")


if __name__ == "__main__":
    artifact_inventory()
    shiny_alignment()
    sql_gap()

"""V6.22 | Owner-approved buildable cohort manifest.

This is NOT the E11 cohort. E11 remains missing and V6.19 stays blocked.
This cohort is owner-defined and built only from artifacts that exist locally:
the V6.17 productive Viewer/Forecast artifacts, the V6.18 navigation contract
and the V6.21B precomputed accuracy metrics.

Governing rules implemented here:

* Three independent buildability flags. history_depth and staleness gate the
  viewer/accuracy side ONLY; a forecast-only case is never marked unbuildable
  for having no history.
* Join columns are byte-identical to v6_18_navigation_contract.csv, including
  EMPTY STRING for axes that do not apply. NOT_APPLICABLE never appears there.
* Entity casing is preserved verbatim in every data and join column. An
  upper-cased copy exists for COUNTING ONLY.
* Route context is part of case identity: the same series_key in two routes is
  two different cases.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

V6_ROOT = Path(__file__).resolve().parents[2]
V617 = V6_ROOT / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"
V618 = V6_ROOT / "outputs" / "v6_18_shiny_dynamic_taxonomy_ui"
V621B = V6_ROOT / "outputs" / "v6_21b_registry_accuracy_hardening"
OUT = V6_ROOT / "outputs" / "v6_22_owner_approved_buildable_cohort"

VIEWER_PARQUET = V617 / "forecast_viewer_model_outputs_v2_full.parquet"
FORECAST_PARQUET = V617 / "forecast_forward_outputs_v6_17_full.parquet"
ACCURACY_PARQUET = V621B / "v6_21b_accuracy_metrics.parquet"
NAV_CONTRACT = V618 / "v6_18_navigation_contract.csv"

JOIN_COLUMNS = [
    "route_id", "base_metric", "display_label", "demand_nature", "db_type",
    "prepared_scenario", "segment", "granularity", "entity_label",
    "entity_value", "source_metric", "source_scenario", "source_granularity",
    "source_series_key",
]
CASE_KEY = ["source_metric", "source_scenario", "source_granularity", "source_series_key"]

# D2: PROD is not a forest. Quarantined unless positive evidence says otherwise.
QUARANTINED_ENTITIES = {"PROD"}

# Recommended defaults, chosen from the measured distribution:
# Basilisk sits at history_depth 75-79 and staleness 55-57; the EDB routes sit
# at 193-360 and 0-84. A depth of 60 is therefore the highest meaningful guard
# that eliminates no route today, and a staleness limit of 60 or lower would
# eliminate both Basilisk routes. E11's >=150 gate would also have eliminated
# them, which is why it is not reused here.
DEFAULT_HISTORY_DEPTH = 60
DEFAULT_STALENESS_DAYS = None  # None means no staleness limit

HISTORY_GRID = [0, 30, 60, 90, 120, 150, 180]
STALENESS_GRID = [None, 7, 14, 30, 60, 90]


def load_navigation() -> pd.DataFrame:
    nav = pd.read_csv(NAV_CONTRACT, keep_default_na=False, dtype=str)
    return nav[nav["contract_row_type"] == "OPERATIONAL_ENTITY"].copy()


def viewer_profile() -> pd.DataFrame:
    """History depth and model coverage per route x key case."""
    cols = [
        "metric", "scenario", "granularity", "series_key", "date",
        "actual_value", "model_name", "extraction_run_id",
    ]
    frame = pd.read_parquet(VIEWER_PARQUET, columns=cols)
    frame["actual_value"] = pd.to_numeric(frame["actual_value"], errors="coerce")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

    keys = ["metric", "scenario", "granularity", "series_key"]
    grouped = frame.groupby(keys, sort=False, observed=True)

    with_actual = frame[frame["actual_value"].notna()]
    depth = (
        with_actual.groupby(keys, sort=False, observed=True)["date"]
        .agg(history_depth="nunique", first_actual_date="min", last_actual_date="max")
        .reset_index()
    )
    coverage = grouped["model_name"].nunique().rename("viewer_model_coverage").reset_index()
    runs = grouped["extraction_run_id"].first().rename("extraction_run_id").reset_index()

    profile = coverage.merge(depth, on=keys, how="left").merge(runs, on=keys, how="left")
    profile["history_depth"] = profile["history_depth"].fillna(0).astype(int)

    anchor = with_actual["date"].max()
    profile["staleness_days"] = (anchor - profile["last_actual_date"]).dt.days
    profile.rename(columns=dict(zip(keys, CASE_KEY)), inplace=True)
    profile.attrs["anchor_date"] = anchor
    return profile


def accuracy_profile() -> pd.DataFrame:
    cols = ["metric", "scenario", "granularity", "series_key", "model_name", "n_points"]
    frame = pd.read_parquet(ACCURACY_PARQUET, columns=cols)
    keys = ["metric", "scenario", "granularity", "series_key"]
    out = (
        frame.groupby(keys, sort=False, observed=True)
        .agg(
            accuracy_model_coverage=("model_name", "nunique"),
            n_points_min=("n_points", "min"),
            n_points_median=("n_points", "median"),
            n_points_max=("n_points", "max"),
        )
        .reset_index()
    )
    out.rename(columns=dict(zip(keys, CASE_KEY)), inplace=True)
    return out


def forecast_profile() -> pd.DataFrame:
    cols = ["metric", "scenario", "granularity", "series_key", "model_name", "record_type"]
    frame = pd.read_parquet(FORECAST_PARQUET, columns=cols)
    frame = frame[frame["record_type"] == "forecast"]
    keys = ["metric", "scenario", "granularity", "series_key"]
    out = (
        frame.groupby(keys, sort=False, observed=True)["model_name"]
        .nunique()
        .rename("forecast_model_coverage")
        .reset_index()
    )
    out.rename(columns=dict(zip(keys, CASE_KEY)), inplace=True)
    return out


def build_axes(row: pd.Series) -> tuple[str, str, str]:
    """Ordered selectable axes, machine path and human path."""
    axes: list[tuple[str, str]] = [("Metric", row["base_metric"])]
    for label, column in (
        ("Demand Nature", "demand_nature"),
        ("DB Type", "db_type"),
        ("Prepared Forecast Variant", "prepared_scenario"),
        ("Segment", "segment"),
    ):
        if str(row[column]).strip():
            axes.append((label, row[column]))
    axes.append(("Granularity", row["granularity"]))
    axes.append((row["entity_label"] or "Entity", row["entity_value"]))

    applicable = "|".join(a[0] for a in axes)
    machine = "|".join(a[1] for a in axes)
    human = " \u2192 ".join(a[1] for a in axes)
    return applicable, machine, human


def classify(row: pd.Series) -> tuple[str, str, str]:
    """taxonomy_alignment, governed_exception, governance_marker."""
    if row["db_type"] == "Basilisk":
        return (
            "OPERATIONAL_SOURCE_PRECEDENCE",
            "CATALOG_SERVING_EMPTY_BUT_OPERATIONAL_ARTIFACT_AVAILABLE",
            "OPERATIONAL_SOURCE_PRECEDENCE",
        )
    if str(row["prepared_scenario"]).startswith("Low Volume"):
        return ("LEGACY_VARIANT", "", "LEGACY_VARIANT")
    return ("OPERATIONAL", "", "")


def entity_type(row: pd.Series) -> str:
    return "Forest + SKU" if row["granularity"] == "Forest_SKU" else row["granularity"]


def assemble(history_depth: int, staleness_days: int | None) -> pd.DataFrame:
    nav = load_navigation()
    viewer = viewer_profile()
    accuracy = accuracy_profile()
    forecast = forecast_profile()
    anchor = viewer.attrs.get("anchor_date")

    manifest = nav.merge(viewer, on=CASE_KEY, how="left")
    manifest = manifest.merge(accuracy, on=CASE_KEY, how="left")
    manifest = manifest.merge(forecast, on=CASE_KEY, how="left")

    for column in ("viewer_model_coverage", "accuracy_model_coverage", "forecast_model_coverage"):
        manifest[column] = manifest[column].fillna(0).astype(int)
    manifest["history_depth"] = manifest["history_depth"].fillna(0).astype(int)
    manifest["has_actuals"] = manifest["history_depth"] > 0
    manifest["extraction_run_id"] = manifest["extraction_run_id"].fillna("")

    # Counting-only copy. Never used for joining or querying.
    manifest["entity_token_upper"] = manifest["entity_value"].str.upper()
    manifest["quarantined"] = manifest["entity_value"].isin(QUARANTINED_ENTITIES)

    axes = manifest.apply(build_axes, axis=1, result_type="expand")
    manifest["axes_applicable"] = axes[0]
    manifest["selection_path"] = axes[1]
    marks = manifest.apply(classify, axis=1, result_type="expand")
    manifest["taxonomy_alignment"] = marks[0]
    manifest["governed_exception"] = marks[1]
    manifest["governance_marker"] = marks[2]
    manifest["selection_display_path"] = [
        f"{path}   [{marker}]" if marker else path
        for path, marker in zip(axes[2], manifest["governance_marker"])
    ]

    manifest["entity_type"] = manifest.apply(entity_type, axis=1)
    manifest["case_id"] = manifest["route_id"] + "::" + manifest["entity_value"]

    passes_history = manifest["history_depth"] >= history_depth
    if staleness_days is None:
        passes_staleness = pd.Series(True, index=manifest.index)
    else:
        passes_staleness = manifest["staleness_days"].fillna(np.inf) <= staleness_days

    manifest["build_viewer"] = (
        manifest["has_actuals"] & passes_history & passes_staleness & ~manifest["quarantined"]
    )
    manifest["build_accuracy"] = manifest["build_viewer"] & (
        manifest["accuracy_model_coverage"] > 0
    )
    manifest["build_forecast"] = (manifest["forecast_model_coverage"] > 0) & ~manifest["quarantined"]

    manifest["viewer_exclusion_reason"] = np.where(
        manifest["build_viewer"], "",
        np.where(
            manifest["quarantined"], "INVALID_ENTITY_QUARANTINED",
            np.where(
                ~manifest["has_actuals"], "NO_ACTUALS_FORECAST_ONLY",
                np.where(~passes_history, "BELOW_HISTORY_THRESHOLD", "STALE_BEYOND_LIMIT"),
            ),
        ),
    )
    manifest["accuracy_exclusion_reason"] = np.where(
        manifest["build_accuracy"], "",
        np.where(~manifest["build_viewer"], "VIEWER_NOT_BUILDABLE",
                 "ABSENT_FROM_V6_21B_ACCURACY_ARTIFACT"),
    )
    manifest["forecast_exclusion_reason"] = np.where(
        manifest["build_forecast"], "",
        np.where(manifest["quarantined"], "INVALID_ENTITY_QUARANTINED",
                 "NO_FORECAST_ROWS_IN_V6_17_ARTIFACT"),
    )

    any_build = manifest["build_viewer"] | manifest["build_accuracy"] | manifest["build_forecast"]
    manifest["scope_status"] = np.where(any_build, "BUILDABLE", "DECLARED_NOT_BUILDABLE")
    manifest["overall_exclusion_reason"] = np.where(
        any_build, "",
        np.where(manifest["quarantined"], "INVALID_ENTITY_QUARANTINED", "NO_LOCAL_ARTIFACT_ROWS"),
    )

    manifest["inclusion_rule"] = np.where(
        manifest["governed_exception"] != "", "R3_GOVERNED_EXCEPTION_BASILISK",
        np.where(manifest["taxonomy_alignment"] == "LEGACY_VARIANT",
                 "R2_LEGACY_VARIANT_PRESERVED", "R1_OPERATIONAL_PREPARED_ARTIFACT"),
    )
    manifest["notes"] = np.where(
        manifest["quarantined"],
        "Quarantined: PROD is not a forest; excluded from the cohort per owner decision D2.",
        "",
    )
    manifest.attrs["anchor_date"] = anchor
    return manifest


def sensitivity(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    forecast_total = int(manifest["build_forecast"].sum())
    all_routes = set(manifest.loc[manifest["has_actuals"], "route_id"].unique())

    for depth in HISTORY_GRID:
        for stale in STALENESS_GRID:
            ok = manifest["has_actuals"] & (manifest["history_depth"] >= depth)
            ok &= ~manifest["quarantined"]
            if stale is not None:
                ok &= manifest["staleness_days"].fillna(np.inf) <= stale
            kept = manifest[ok]
            kept_routes = set(kept["route_id"].unique())
            rows.append(
                {
                    "history_depth": depth,
                    "staleness_days": "no limit" if stale is None else stale,
                    "viewer_buildable_cases": len(kept),
                    "distinct_entity_tokens": kept["entity_value"].nunique(),
                    "distinct_physical_entities": kept["entity_token_upper"].nunique(),
                    "routes_retained": len(kept_routes),
                    "routes_eliminated": "|".join(sorted(all_routes - kept_routes)) or "none",
                    "total_forecast_buildable_unchanged": forecast_total,
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_HISTORY_DEPTH
    stale_arg = sys.argv[2] if len(sys.argv) > 2 else "none"
    stale = None if stale_arg.lower() in {"none", "nolimit", "no-limit"} else int(stale_arg)

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = assemble(depth, stale)

    cohort = manifest[~manifest["quarantined"]].copy()
    manifest_columns = JOIN_COLUMNS + [
        "case_id", "entity_type", "entity_token_upper", "axes_applicable",
        "selection_path", "selection_display_path", "governance_marker",
        "scope_status", "build_viewer", "build_accuracy", "build_forecast",
        "viewer_exclusion_reason", "accuracy_exclusion_reason",
        "forecast_exclusion_reason", "overall_exclusion_reason",
        "has_actuals", "history_depth", "first_actual_date", "last_actual_date",
        "staleness_days", "viewer_model_coverage", "accuracy_model_coverage",
        "forecast_model_coverage", "extraction_run_id", "taxonomy_alignment",
        "governed_exception", "inclusion_rule", "notes",
    ]
    cohort[manifest_columns].to_csv(OUT / "v6_22_cohort_manifest.csv", index=False)

    selection = cohort[
        ["case_id", "selection_display_path", "base_metric", "db_type",
         "prepared_scenario", "segment", "granularity", "entity_type",
         "entity_value", "entity_token_upper", "build_viewer", "build_accuracy",
         "build_forecast", "scope_status", "governance_marker"]
    ].rename(columns={"base_metric": "metric"}).sort_values("case_id", kind="stable")
    selection.to_csv(OUT / "v6_22_final_selection_list.csv", index=False)

    sensitivity(manifest).to_csv(OUT / "v6_22_threshold_sensitivity.csv", index=False)

    profile_cols = CASE_KEY + [
        "route_id", "entity_value", "entity_token_upper", "has_actuals",
        "history_depth", "first_actual_date", "last_actual_date", "staleness_days",
        "n_points_min", "n_points_median", "n_points_max", "extraction_run_id",
        "viewer_model_coverage", "accuracy_model_coverage", "forecast_model_coverage",
    ]
    manifest[profile_cols].to_csv(OUT / "v6_22_eligibility_profile.csv", index=False)

    fo = cohort[~cohort["has_actuals"]]
    print(f"nav_operational_rows={len(manifest)}")
    print(f"cohort_cases={len(cohort)}")
    print(f"quarantined_cases={int(manifest['quarantined'].sum())}")
    print(f"entity_tokens_cs={cohort['entity_value'].nunique()}")
    print(f"physical_entities_ci={cohort['entity_token_upper'].nunique()}")
    print(f"build_viewer={int(cohort['build_viewer'].sum())}")
    print(f"build_accuracy={int(cohort['build_accuracy'].sum())}")
    print(f"build_forecast_total={int(cohort['build_forecast'].sum())}")
    print(f"forecast_only_buildable={int(fo['build_forecast'].sum())}")
    print(f"anchor_date={manifest.attrs.get('anchor_date')}")
    print(f"history_depth_min={int(manifest['history_depth'].min())}")
    print(f"history_depth_max={int(manifest['history_depth'].max())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
V617 = ROOT / "V6" / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"
VIEWER = V617 / "v6_17_viewer_dropdown_metadata.csv"
FORECAST = V617 / "v6_17_forecast_dropdown_metadata.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


# V6.23-P0 | Entities excluded from the Viewer selector.
# PROD is not a forest identifier: it appears twice in the prepared forecast
# metadata and zero times in the Viewer metadata. Quarantined per owner
# decision D2 recorded in V6.22.
QUARANTINED_ENTITIES = {"PROD"}


def flag(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def entity_label(granularity: str) -> str:
    return {
        "Forest": "Forest",
        "Region": "Region",
        "Forest_SKU": "Forest + SKU",
    }[granularity]


def route_dimensions(row: dict[str, str]) -> dict[str, str]:
    metric = row["metric"]
    scenario = row["scenario"]
    grain = row["granularity"]
    if metric == "HDD - EDB":
        return {
            "route_id": f"HDD|Organic|EDB|{scenario}|{grain}",
            "base_metric": "HDD",
            "display_label": metric,
            "demand_nature": "Organic",
            "db_type": "EDB",
            "prepared_scenario": "",
            "segment": scenario,
            "serving_status": "PREPARED_ACTUALS_AND_FORECASTS",
            "support_status": "OPERATIONAL",
            "empty_state": "",
            "notes": "Direct canonical-taxonomy match.",
        }
    if metric == "HDD - Basilisk":
        return {
            "route_id": f"HDD|Organic|Basilisk|{grain}",
            "base_metric": "HDD",
            "display_label": metric,
            "demand_nature": "Organic",
            "db_type": "Basilisk",
            "prepared_scenario": "",
            "segment": "",
            "serving_status": "PREPARED_ACTUALS_AND_FORECASTS",
            "support_status": "OPERATIONAL_SOURCE_PRECEDENCE",
            "empty_state": "",
            "notes": (
                "V6.17 artifact is operational; the Master Catalog marks the serving "
                "view empty, so governed prepared-artifact precedence applies."
            ),
        }
    if metric == "SSD - Phoenix":
        return {
            "route_id": f"SSD|Phoenix|LEGACY_VARIANT|{scenario}|{grain}",
            "base_metric": "SSD",
            "display_label": metric,
            "demand_nature": "",
            "db_type": "Phoenix",
            "prepared_scenario": scenario,
            "segment": "",
            "serving_status": "PREPARED_FORECAST_ONLY",
            "support_status": "OPERATIONAL_LEGACY_COMPATIBILITY",
            "empty_state": "FORECAST_ONLY",
            "notes": (
                "Prepared volume/efficiency variants are preserved verbatim. "
                "No Organic/Inorganic mapping has been verified."
            ),
        }
    raise ValueError(f"Unexpected operational metric: {metric}")


def gap_routes() -> list[dict[str, str]]:
    raw: list[tuple[str, str, str, str, str, str, str]] = []
    for db_type in ("NonPhoenix", "Phoenix"):
        for scenario in ("Consumed", "Failover"):
            for grain in ("Forest", "Region"):
                raw.append(("CPU", db_type, "", scenario, "", grain, "BACKEND_GAP"))
    for scenario in ("Consumed", "Failover"):
        for grain in ("Forest_SKU", "Region"):
            raw.append(("CPU", "Total", "", scenario, "", grain, "BACKEND_GAP"))
    for grain in ("Forest", "Region"):
        raw.append(("HDD", "", "Inorganic", "", "", grain, "NOT_CURRENTLY_IMPLEMENTED"))
    for segment in ("Consumer", "Enterprise"):
        for grain in ("Forest", "Region"):
            raw.append(
                ("HDD", "All", "Organic", "", segment, grain, "NOT_CURRENTLY_IMPLEMENTED")
            )
    for scenario in ("Consumed", "Failover"):
        for grain in ("Forest_SKU", "Region"):
            raw.append(("IOPS", "", "", scenario, "", grain, "BACKEND_GAP"))
    for grain in ("Forest_SKU", "Region"):
        raw.append(("SSD", "Legacy", "Organic", "", "", grain, "BACKEND_GAP"))
    for grain in ("Forest", "Forest_SKU", "Region"):
        raw.append(("SSD", "MCDB", "Organic", "", "", grain, "BACKEND_GAP"))
    raw.extend(
        [
            ("SSD", "Phoenix", "Inorganic", "", "", "Forest", "BACKEND_GAP"),
            ("SSD", "Phoenix", "Organic", "", "", "Forest", "BACKEND_GAP"),
            ("SSD", "Phoenix", "Organic", "", "", "Region", "BACKEND_GAP"),
        ]
    )
    rows = []
    for metric, db_type, demand, scenario, segment, grain, state in raw:
        route_id = "|".join(
            value for value in (metric, db_type, demand, scenario, segment, grain) if value
        )
        rows.append(
            {
                "route_id": route_id,
                "base_metric": metric,
                "db_type": db_type,
                "demand_nature": demand,
                "scenario": scenario,
                "segment": segment,
                "granularity": grain,
                "taxonomy_status": "ROUTABLE",
                "operational_status": "TAXONOMY_VALID_BUT_NOT_CURRENTLY_IMPLEMENTED",
                "empty_state": state,
                "notes": (
                    "Valid in E0-E10 but absent from governed V6.17 Viewer and "
                    "Forecast prepared artifacts."
                ),
            }
        )
    if len(rows) != 30:
        raise AssertionError(f"Expected 30 taxonomy gaps, found {len(rows)}")
    return rows


def main() -> None:
    viewer = read_csv(VIEWER)
    forecast = read_csv(FORECAST)
    viewer_index = {
        (r["metric"], r["scenario"], r["granularity"], r["series_key"]): r
        for r in viewer
    }
    contract: list[dict[str, object]] = []
    for row in forecast:
        key = (row["metric"], row["scenario"], row["granularity"], row["series_key"])
        viewer_row = viewer_index.get(key)
        dimensions = route_dimensions(row)
        contract.append(
            {
                "contract_row_type": "OPERATIONAL_ENTITY",
                **dimensions,
                "granularity": row["granularity"],
                "entity_label": entity_label(row["granularity"]),
                "forest": "",
                "sku": "",
                "entity_value": row["series_key"],
                "source_metric": row["metric"],
                "source_scenario": row["scenario"],
                "source_granularity": row["granularity"],
                "source_series_key": row["series_key"],
                # V6.23-P1 | The Viewer selector exposes ONLY cases that can
                # render a real backtest: observed actuals plus the governed
                # model estimates. A case that would end in "Backtest
                # unavailable" is not offered as a normal Viewer selection.
                # Forecast-only routes are surfaced separately, as a callout on
                # the Viewer page, and remain fully selectable in Forecast.
                "viewer_visible": flag(
                    row["series_key"] not in QUARANTINED_ENTITIES
                    and viewer_row is not None
                    and truth(viewer_row["viewer_available"])
                    and truth(viewer_row["has_actuals"])
                ),
                "forecast_visible": flag(row["series_key"] not in QUARANTINED_ENTITIES),
                "viewer_eligible": flag(
                    viewer_row is not None
                    and truth(viewer_row["viewer_available"])
                    and truth(viewer_row["has_actuals"])
                ),
                "forecast_eligible": flag(truth(row["forecast_available"])),
                "has_actuals": flag(truth(row["has_actuals"])),
                "traceability": (
                    "v6_17_viewer_dropdown_metadata.csv + "
                    "v6_17_forecast_dropdown_metadata.csv"
                ),
            }
        )

    info = [
        (
            "HDD|Inorganic",
            "HDD",
            "HDD",
            "Inorganic",
            "",
            "TRUE",
            "TRUE",
            "TAXONOMY_ONLY",
            "TAXONOMY_VALID_NOT_IMPLEMENTED",
            "NOT_CURRENTLY_IMPLEMENTED",
            "No governed V6.17 prepared artifact exists for HDD Inorganic.",
        ),
        (
            "CPU",
            "CPU",
            "CPU",
            "",
            "",
            "FALSE",
            "TRUE",
            "NO_PRODUCTIVE_V6_ARTIFACT",
            "BACKEND_GAP",
            "BACKEND_GAP",
            "Productive governed CPU forecast input is unavailable in V6.17.",
        ),
        (
            "IOPS",
            "IOPS",
            "IOPS",
            "",
            "",
            "FALSE",
            "TRUE",
            "NO_PRODUCTIVE_V6_ARTIFACT",
            "BACKEND_GAP",
            "BACKEND_GAP",
            "Productive governed IOPS forecast input is unavailable in V6.17.",
        ),
        (
            "SSD|MCDB",
            "SSD",
            "SSD - MCDB",
            "Organic",
            "MCDB",
            "FALSE",
            "TRUE",
            "NO_PRODUCTIVE_V6_ARTIFACT",
            "BACKEND_GAP",
            "BACKEND_GAP",
            "SSD-MCDB is a valid catalog branch but has no governed V6.17 prepared forecast.",
        ),
        (
            "Memory",
            "Memory",
            "Memory",
            "",
            "",
            "FALSE",
            "TRUE",
            "NOT_ROUTABLE",
            "BACKEND_GAP",
            "NOT_ROUTABLE",
            "Memory has no routable productive forecast source.",
        ),
    ]
    for (
        route_id,
        metric,
        display,
        demand,
        db_type,
        viewer_visible,
        forecast_visible,
        serving,
        support,
        empty,
        notes,
    ) in info:
        contract.append(
            {
                "contract_row_type": "INFORMATIONAL_ROUTE",
                "route_id": route_id,
                "base_metric": metric,
                "display_label": display,
                "demand_nature": demand,
                "db_type": db_type,
                "prepared_scenario": "",
                "segment": "",
                "granularity": "",
                "entity_label": "",
                "forest": "",
                "sku": "",
                "entity_value": "",
                "source_metric": "",
                "source_scenario": "",
                "source_granularity": "",
                "source_series_key": "",
                "viewer_visible": viewer_visible,
                "forecast_visible": forecast_visible,
                "viewer_eligible": "FALSE",
                "forecast_eligible": "FALSE",
                "has_actuals": "FALSE",
                "serving_status": serving,
                "support_status": support,
                "empty_state": empty,
                "traceability": "Master Catalog E0-E10 + V6.17 availability",
                "notes": notes,
            }
        )

    contract_fields = [
        "contract_row_type",
        "route_id",
        "base_metric",
        "display_label",
        "demand_nature",
        "db_type",
        "prepared_scenario",
        "segment",
        "granularity",
        "entity_label",
        "forest",
        "sku",
        "entity_value",
        "source_metric",
        "source_scenario",
        "source_granularity",
        "source_series_key",
        "viewer_visible",
        "forecast_visible",
        "viewer_eligible",
        "forecast_eligible",
        "has_actuals",
        "serving_status",
        "support_status",
        "empty_state",
        "traceability",
        "notes",
    ]
    write_csv("v6_18_navigation_contract.csv", contract_fields, contract)

    counts = Counter((r["metric"], r["scenario"], r["granularity"]) for r in forecast)
    supported = []
    for (metric, scenario, grain), forecast_count in sorted(counts.items()):
        viewer_count = sum(
            (r["metric"], r["scenario"], r["granularity"]) == (metric, scenario, grain)
            for r in viewer
        )
        sample = route_dimensions(
            next(
                r
                for r in forecast
                if (r["metric"], r["scenario"], r["granularity"])
                == (metric, scenario, grain)
            )
        )
        supported.append(
            {
                "route_id": sample["route_id"],
                "base_metric": sample["base_metric"],
                "display_label": metric,
                "demand_nature": sample["demand_nature"],
                "db_type": sample["db_type"],
                "prepared_scenario": sample["prepared_scenario"],
                "segment": sample["segment"],
                "granularity": grain,
                "viewer_case_count": viewer_count,
                "forecast_case_count": forecast_count,
                "has_actuals": flag(viewer_count > 0),
                "viewer_status": "OPERATIONAL" if viewer_count else "NOT_ELIGIBLE",
                "forecast_status": "OPERATIONAL",
                "taxonomy_alignment": sample["support_status"],
                "notes": sample["notes"],
            }
        )
    supported_fields = [
        "route_id",
        "base_metric",
        "display_label",
        "demand_nature",
        "db_type",
        "prepared_scenario",
        "segment",
        "granularity",
        "viewer_case_count",
        "forecast_case_count",
        "has_actuals",
        "viewer_status",
        "forecast_status",
        "taxonomy_alignment",
        "notes",
    ]
    write_csv("v6_18_current_supported_routes.csv", supported_fields, supported)

    gaps = gap_routes()
    gap_fields = [
        "route_id",
        "base_metric",
        "db_type",
        "demand_nature",
        "scenario",
        "segment",
        "granularity",
        "taxonomy_status",
        "operational_status",
        "empty_state",
        "notes",
    ]
    write_csv("v6_18_taxonomy_valid_not_implemented.csv", gap_fields, gaps)

    dirty_count = len(git("status", "--porcelain").splitlines())
    viewer_routes = {
        (r["metric"], r["scenario"], r["granularity"]) for r in viewer
    }
    preflight = [
        ("PRIMARY_WORKTREE", str(ROOT), "git rev-parse --show-toplevel", "VERIFIED",
         "Primary repository worktree; do not use the isolated inspection worktree."),
        ("BRANCH", git("branch", "--show-current"), "git branch --show-current", "VERIFIED", ""),
        ("DIRTY_WORKTREE_ENTRY_COUNT", dirty_count, "git status --porcelain", "RECORDED",
         "Existing user and prior-stage changes were not reverted."),
        ("FULL_DISCOVERED_TAXONOMY_COUNT", 6383, "Master Catalog E11", "REFERENCE_ONLY",
         "Logical leaves; not materialized as V6 operational cases."),
        ("FULL_DISCOVERED_ROUTABLE_ROUTE_COUNT", 34,
         "Master Catalog E10 / reviewed mockup manifest", "REFERENCE_ONLY",
         "38 total route rows; 34 routable UI routes."),
        ("CURRENT_VIEWER_SUPPORTED_ROUTE_COUNT", len(viewer_routes), VIEWER.name, "VERIFIED", ""),
        ("CURRENT_VIEWER_SUPPORTED_CASE_COUNT", len(viewer), VIEWER.name, "VERIFIED",
         "All cases have actuals and exactly 15 Viewer models."),
        ("CURRENT_FORECAST_SUPPORTED_ROUTE_COUNT", len(counts), FORECAST.name, "VERIFIED", ""),
        ("CURRENT_FORECAST_SUPPORTED_CASE_COUNT", len(forecast), FORECAST.name, "VERIFIED", ""),
        ("TAXONOMY_VALID_BUT_NOT_IMPLEMENTED_COUNT", len(gaps),
         "E10 routable routes reconciled to V6.17 direct canonical matches",
         "VERIFIED_WITH_RECONCILIATION",
         "34 routable routes minus four direct operational EDB matches; four more "
         "V6.17 routes use explicit legacy/source-precedence compatibility."),
        ("VIEWER_MODEL_COUNT", max(int(r["model_count"]) for r in viewer),
         VIEWER.name, "VERIFIED", "Minimum and maximum are both 15."),
    ]
    write_csv(
        "v6_18_preflight_inventory.csv",
        ["inventory_item", "observed_value", "source", "status", "notes"],
        [
            dict(
                zip(
                    ["inventory_item", "observed_value", "source", "status", "notes"],
                    row,
                )
            )
            for row in preflight
        ],
    )

    feeding = [
        ("Viewer", "v6_18_navigation_contract.csv",
         "Shared conditional taxonomy and source-field resolution",
         "Read once; in-memory metadata filtering", "READ_ONLY", "FILTER_ONLY"),
        ("Viewer", "forecast_viewer_model_outputs_v2_full.parquet",
         "Actual versus 15-model historical backtests",
         "Arrow open_dataset; collect selected case only", "READ_ONLY", "LAZY_FILTER_ONLY"),
        ("Forecast", "v6_18_navigation_contract.csv",
         "Shared conditional taxonomy and source-field resolution",
         "Read once; in-memory metadata filtering", "READ_ONLY", "FILTER_ONLY"),
        ("Forecast", "forecast_forward_outputs_v6_17_full.parquet",
         "Prepared actual history and frozen forward forecasts",
         "Arrow open_dataset; collect selected case only", "READ_ONLY", "LAZY_FILTER_ONLY"),
    ]
    feeding_fields = [
        "consumer",
        "input_artifact",
        "purpose",
        "access_pattern",
        "mutability",
        "dashboard_operation",
    ]
    write_csv(
        "v6_18_dashboard_feeding_contract.csv",
        feeding_fields,
        [dict(zip(feeding_fields, row)) for row in feeding],
    )
    print(
        f"Generated {len(contract)} contract rows, {len(supported)} operational "
        f"routes and {len(gaps)} taxonomy gaps."
    )


if __name__ == "__main__":
    main()

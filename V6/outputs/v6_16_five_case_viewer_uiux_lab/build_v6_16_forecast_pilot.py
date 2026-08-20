"""Build the bounded V6.16 forward Forecast pilot from existing local artifacts."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "V6" / "outputs" / "v6_16_five_case_viewer_uiux_lab"
OUTPUT_PATH = OUTPUT_DIR / "forecast_forward_outputs_v6_16_pilot.csv"
MANIFEST_PATH = OUTPUT_DIR / "v6_16_forecast_pilot_manifest.csv"
SUMMARY_PATH = OUTPUT_DIR / "v6_16_forecast_pilot_summary.json"

HDD_FORECASTS = ROOT / "V6" / "data" / "processed" / "forecasts.csv"
HDD_ACTUALS = ROOT / "V6" / "data" / "processed" / "actuals.csv"
SSD_FORECASTS = (
    ROOT
    / "V6"
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_forecast_ssd_phoenix.csv"
)

OUTPUT_COLUMNS = [
    "metric",
    "scenario",
    "granularity",
    "series_key",
    "date",
    "record_type",
    "value",
    "model_name",
    "forecast_version",
    "has_actuals",
    "forecast_only",
    "value_type",
    "source_table",
    "source_artifact",
    "extraction_run_id",
]


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def require_columns(path: Path, required: set[str]) -> None:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        names = set(csv.DictReader(handle).fieldnames or [])
    missing = required - names
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")


def write_row(writer: csv.DictWriter, stats: dict, row: dict[str, str]) -> None:
    writer.writerow(row)
    key = (row["metric"], row["scenario"], row["granularity"])
    group = stats[key]
    group["keys"].add(row["series_key"])
    group["versions"].add(row["forecast_version"])
    group[f"{row['record_type']}_rows"] += 1
    group["dates"].append(row["date"])


def build() -> dict:
    require_columns(
        HDD_FORECASTS,
        {"entity_key", "date", "forecast_value", "model_version",
         "forecast_version", "scenario", "value_type", "source_file"},
    )
    require_columns(
        HDD_ACTUALS,
        {"entity_key", "date", "actual_value", "forecast_version",
         "scenario", "source_file"},
    )
    require_columns(
        SSD_FORECASTS,
        {"scenario_ui_label", "key", "forecast_date", "forecast_value",
         "forecast_version", "value_type", "source_table", "extraction_run_id"},
    )

    hdd_forecast_start: dict[str, date] = {}
    hdd_keys: set[str] = set()
    with HDD_FORECASTS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = row["entity_key"].strip()
            row_date = parse_date(row["date"])
            hdd_keys.add(key)
            hdd_forecast_start[key] = min(
                hdd_forecast_start.get(key, row_date), row_date
            )

    hdd_actual_end: dict[str, date] = {}
    with HDD_ACTUALS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            key = row["entity_key"].strip()
            if key not in hdd_keys:
                continue
            row_date = parse_date(row["date"])
            hdd_actual_end[key] = max(hdd_actual_end.get(key, row_date), row_date)

    ssd_latest_version: dict[tuple[str, str], str] = {}
    with SSD_FORECASTS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            group = (row["scenario_ui_label"].strip(), row["key"].strip())
            version = row["forecast_version"].strip()
            ssd_latest_version[group] = max(
                ssd_latest_version.get(group, version), version
            )

    ssd_forecast_start: dict[tuple[str, str], date] = {}
    with SSD_FORECASTS.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            group = (row["scenario_ui_label"].strip(), row["key"].strip())
            if row["forecast_version"].strip() != ssd_latest_version[group]:
                continue
            row_date = parse_date(row["forecast_date"])
            ssd_forecast_start[group] = min(
                ssd_forecast_start.get(group, row_date), row_date
            )

    stats = defaultdict(
        lambda: {
            "keys": set(),
            "versions": set(),
            "actual_rows": 0,
            "forecast_rows": 0,
            "dates": [],
        }
    )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        with HDD_ACTUALS.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                key = row["entity_key"].strip()
                if key not in hdd_keys:
                    continue
                row_date = parse_date(row["date"])
                if row_date < hdd_actual_end[key] - timedelta(days=364):
                    continue
                write_row(
                    writer,
                    stats,
                    {
                        "metric": "HDD - EDB",
                        "scenario": row["scenario"].strip(),
                        "granularity": "Region",
                        "series_key": key,
                        "date": row_date.isoformat(),
                        "record_type": "actual",
                        "value": row["actual_value"],
                        "model_name": "",
                        "forecast_version": row["forecast_version"].strip(),
                        "has_actuals": "TRUE",
                        "forecast_only": "FALSE",
                        "value_type": "Actual",
                        "source_table": row["source_file"].strip(),
                        "source_artifact": "V6/data/processed/actuals.csv",
                        "extraction_run_id": "LEGACY_PROCESSED_FORWARD",
                    },
                )

        with HDD_FORECASTS.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                key = row["entity_key"].strip()
                row_date = parse_date(row["date"])
                if row_date > hdd_forecast_start[key] + timedelta(days=179):
                    continue
                write_row(
                    writer,
                    stats,
                    {
                        "metric": "HDD - EDB",
                        "scenario": row["scenario"].strip(),
                        "granularity": "Region",
                        "series_key": key,
                        "date": row_date.isoformat(),
                        "record_type": "forecast",
                        "value": row["forecast_value"],
                        "model_name": row["model_version"].strip(),
                        "forecast_version": row["forecast_version"].strip(),
                        "has_actuals": "TRUE",
                        "forecast_only": "FALSE",
                        "value_type": row["value_type"].strip(),
                        "source_table": row["source_file"].strip(),
                        "source_artifact": "V6/data/processed/forecasts.csv",
                        "extraction_run_id": "LEGACY_PROCESSED_FORWARD",
                    },
                )

        with SSD_FORECASTS.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                scenario = row["scenario_ui_label"].strip()
                key = row["key"].strip()
                group = (scenario, key)
                version = row["forecast_version"].strip()
                if version != ssd_latest_version[group]:
                    continue
                row_date = parse_date(row["forecast_date"])
                if row_date > ssd_forecast_start[group] + timedelta(days=179):
                    continue
                write_row(
                    writer,
                    stats,
                    {
                        "metric": "SSD - Phoenix",
                        "scenario": scenario,
                        "granularity": "Forest",
                        "series_key": key,
                        "date": row_date.isoformat(),
                        "record_type": "forecast",
                        "value": row["forecast_value"],
                        "model_name": "Governed Phoenix source forecast",
                        "forecast_version": version,
                        "has_actuals": "FALSE",
                        "forecast_only": "TRUE",
                        "value_type": row["value_type"].strip(),
                        "source_table": row["source_table"].strip(),
                        "source_artifact": (
                            "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                            "r6_phase1_forecast_ssd_phoenix.csv"
                        ),
                        "extraction_run_id": row["extraction_run_id"].strip(),
                    },
                )

    manifest_columns = [
        "metric",
        "scenario",
        "granularity",
        "key_count",
        "actual_rows",
        "forecast_rows",
        "forecast_versions",
        "has_actuals",
        "forecast_only",
        "date_min",
        "date_max",
        "validation_status",
    ]
    manifest_rows = []
    for (metric, scenario, granularity), group in sorted(stats.items()):
        has_actuals = group["actual_rows"] > 0
        manifest_rows.append(
            {
                "metric": metric,
                "scenario": scenario,
                "granularity": granularity,
                "key_count": len(group["keys"]),
                "actual_rows": group["actual_rows"],
                "forecast_rows": group["forecast_rows"],
                "forecast_versions": len(group["versions"] - {""}),
                "has_actuals": str(has_actuals).upper(),
                "forecast_only": str(not has_actuals).upper(),
                "date_min": min(group["dates"]),
                "date_max": max(group["dates"]),
                "validation_status": "PASS",
            }
        )

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest_columns)
        writer.writeheader()
        writer.writerows(manifest_rows)

    total_rows = sum(
        row["actual_rows"] + row["forecast_rows"] for row in manifest_rows
    )
    summary = {
        "status": "PASS",
        "artifact": OUTPUT_PATH.relative_to(ROOT).as_posix(),
        "rows": total_rows,
        "metrics": len({row["metric"] for row in manifest_rows}),
        "scenario_granularity_combinations": len(manifest_rows),
        "key_combinations": sum(row["key_count"] for row in manifest_rows),
        "hdd_keys": len(hdd_keys),
        "ssd_key_combinations": len(ssd_latest_version),
        "maximum_forecast_window_days": 180,
        "maximum_actual_history_days": 365,
        "models_run": False,
        "tesseract_accessed": False,
        "full_backtest_started": False,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))

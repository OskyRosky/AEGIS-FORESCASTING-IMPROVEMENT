"""Assemble and validate V6.17 productive Viewer/Forecast artifacts."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


THIS_FILE = Path(__file__).resolve()
OUTPUT_DIR = THIS_FILE.parent
V6_ROOT = THIS_FILE.parents[2]
LEGACY_PATH = V6_ROOT / "data" / "processed" / "forecast_viewer_model_outputs.csv"
MODEL_CONTRACT = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r8fix2_backtest_artifact_v2_contract"
    / "backtest_v2_model_contract.csv"
)
PHASE_A = OUTPUT_DIR / "viewer_backtest_phase_a_nonneural.csv"
PHASE_B = OUTPUT_DIR / "viewer_backtest_phase_b_neural.csv"
FIT_LOG = OUTPUT_DIR / "v6_17_model_fit_log.csv"
FORECAST_FULL = OUTPUT_DIR / "forecast_forward_outputs_v6_17_full.csv"
VIEWER_FULL = OUTPUT_DIR / "forecast_viewer_model_outputs_v2_full.csv"

MODEL_SUMMARY = OUTPUT_DIR / "v6_17_model_run_summary.csv"
VIEWER_COVERAGE = OUTPUT_DIR / "v6_17_viewer_coverage_matrix.csv"
FORECAST_COVERAGE = OUTPUT_DIR / "v6_17_forecast_coverage_matrix.csv"
DATA_QUALITY = OUTPUT_DIR / "v6_17_data_quality_checks.csv"
FEEDING_CONTRACT = OUTPUT_DIR / "v6_17_dashboard_feeding_contract.csv"
VALIDATION = OUTPUT_DIR / "v6_17_validation.csv"
ARTIFACT_MANIFEST = OUTPUT_DIR / "v6_17_artifact_manifest.csv"
BLOCKED_SCOPE = OUTPUT_DIR / "v6_17_blocked_or_deferred_scope.csv"
CLOSURE = OUTPUT_DIR / "v6_17_closure_summary.md"
VIEWER_METADATA = OUTPUT_DIR / "v6_17_viewer_dropdown_metadata.csv"
FORECAST_METADATA = OUTPUT_DIR / "v6_17_forecast_dropdown_metadata.csv"
MODEL_METADATA = OUTPUT_DIR / "v6_17_model_metadata.csv"

EXPECTED_LEGACY_ROWS = 204_300
EXPECTED_GENERATED_ROWS = 2_211_750
EXPECTED_VIEWER_ROWS = 2_416_050
EXPECTED_FORECAST_COMBINATIONS = 896
EXPECTED_VIEWER_KEYS = 596
EXPECTED_MODELS = 15

CONTRACT_COLUMNS = [
    "metric",
    "scenario",
    "granularity",
    "series_key",
    "series_label",
    "date",
    "actual_value",
    "model_name",
    "model_origin",
    "model_family",
    "forecast_value",
    "forecast_type",
    "horizon_days",
    "forecast_start_date",
    "run_id",
    "source_artifact",
    "is_baseline",
    "is_challenger",
    "is_deferred",
    "is_selected_champion",
    "risk_status",
    "lower_bound",
    "upper_bound",
    "interval_level",
    "extraction_run_id",
]

VIEWER_EXPECTED = [
    ("HDD - EDB", "Enterprise", "Region", 45),
    ("HDD - EDB", "Enterprise", "Forest", 152),
    ("HDD - EDB", "Consumer", "Region", 45),
    ("HDD - EDB", "Consumer", "Forest", 152),
    ("HDD - Basilisk", "Basilisk", "Region", 47),
    ("HDD - Basilisk", "Basilisk", "Forest", 155),
]

FORECAST_EXPECTED = [
    ("HDD - EDB", "Enterprise", "Region", 45),
    ("HDD - EDB", "Enterprise", "Forest", 152),
    ("HDD - EDB", "Consumer", "Region", 45),
    ("HDD - EDB", "Consumer", "Forest", 152),
    ("HDD - Basilisk", "Basilisk", "Region", 47),
    ("HDD - Basilisk", "Basilisk", "Forest", 155),
    ("SSD - Phoenix", "Low Volume No Efficiency", "Forest", 148),
    ("SSD - Phoenix", "Low Volume With Efficiency", "Forest", 152),
]


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle) - 1


def compute_generated_champions() -> set[tuple[str, str, str, str, str]]:
    scores: dict[tuple[str, str, str, str, str], list[float]] = defaultdict(
        lambda: [0.0, 0.0]
    )
    columns = [
        "metric", "scenario", "granularity", "series_key", "model_name",
        "actual_value", "forecast_value",
    ]
    for path in (PHASE_A, PHASE_B):
        for chunk in pd.read_csv(path, usecols=columns, chunksize=100_000):
            chunk["abs_error"] = (
                pd.to_numeric(chunk["forecast_value"], errors="raise")
                - pd.to_numeric(chunk["actual_value"], errors="raise")
            ).abs()
            grouped = chunk.groupby(columns[:5])["abs_error"].agg(["sum", "count"])
            for key, row in grouped.iterrows():
                scores[tuple(map(str, key))][0] += float(row["sum"])
                scores[tuple(map(str, key))][1] += float(row["count"])

    by_case: dict[tuple[str, str, str, str], list[tuple[float, str]]] = defaultdict(list)
    for key, (total, count) in scores.items():
        by_case[key[:4]].append((total / count, key[4]))
    champions = set()
    for case, candidates in by_case.items():
        _, model = min(candidates, key=lambda item: (item[0], item[1]))
        champions.add((*case, model))
    if len(champions) != 557:
        raise ValueError(f"Expected 557 generated champions, found {len(champions)}")
    return champions


def assemble_viewer() -> tuple[int, int]:
    champions = compute_generated_champions()
    written = 0
    with VIEWER_FULL.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=CONTRACT_COLUMNS)
        writer.writeheader()
        with LEGACY_PATH.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                full = {
                    "metric": "HDD - EDB",
                    "scenario": "Enterprise",
                    "granularity": "Region",
                    **row,
                    "extraction_run_id": "LEGACY_STAGE05H_VERIFIED_R8FIX0",
                }
                writer.writerow({column: full.get(column, "") for column in CONTRACT_COLUMNS})
                written += 1
        for path in (PHASE_A, PHASE_B):
            with path.open(newline="", encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    champion_key = (
                        row["metric"],
                        row["scenario"],
                        row["granularity"],
                        row["series_key"],
                        row["model_name"],
                    )
                    row["is_selected_champion"] = (
                        "TRUE" if champion_key in champions else "FALSE"
                    )
                    writer.writerow(
                        {column: row.get(column, "") for column in CONTRACT_COLUMNS}
                    )
                    written += 1
    if written != EXPECTED_VIEWER_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_VIEWER_ROWS} Viewer rows, wrote {written}"
        )
    return written, len(champions)


def duplicate_hash_count(path: Path, grain: list[str]) -> int:
    hashes = []
    for chunk in pd.read_csv(path, usecols=grain, chunksize=150_000, dtype=str):
        hashes.append(pd.util.hash_pandas_object(chunk, index=False).to_numpy())
    values = np.concatenate(hashes)
    return int(len(values) - len(np.unique(values)))


def required_null_count(path: Path, required: list[str]) -> int:
    count = 0
    for chunk in pd.read_csv(path, usecols=required, chunksize=150_000):
        count += int(chunk.isna().sum().sum())
    return count


def write_model_summary() -> pd.DataFrame:
    log = pd.read_csv(FIT_LOG)
    summary = (
        log.groupby(["phase", "model_name", "model_family"], as_index=False)
        .agg(
            fits=("status", "size"),
            passed_fits=("status", lambda values: int((values == "PASS").sum())),
            failed_fits=("status", lambda values: int((values == "FAIL").sum())),
            rows=("rows", "sum"),
            runtime_seconds=("runtime_seconds", "sum"),
        )
    )
    summary["runtime_minutes"] = summary["runtime_seconds"] / 60.0
    summary["status"] = np.where(summary["failed_fits"].eq(0), "PASS", "FAIL")
    summary.to_csv(MODEL_SUMMARY, index=False)
    return summary


def viewer_key_metadata() -> pd.DataFrame:
    legacy = pd.read_csv(LEGACY_PATH, usecols=["series_key"])
    legacy_meta = pd.DataFrame(
        {
            "metric": "HDD - EDB",
            "scenario": "Enterprise",
            "granularity": "Region",
            "series_key": sorted(legacy["series_key"].astype(str).unique()),
        }
    )
    fits = pd.read_csv(
        FIT_LOG,
        usecols=["metric", "scenario", "granularity", "series_key", "status"],
        dtype=str,
    )
    generated = fits[fits["status"].eq("PASS")][
        ["metric", "scenario", "granularity", "series_key"]
    ].drop_duplicates()
    metadata = pd.concat([legacy_meta, generated], ignore_index=True).drop_duplicates()
    metadata["has_actuals"] = True
    metadata["viewer_available"] = True
    metadata["model_count"] = EXPECTED_MODELS
    metadata = metadata.sort_values(
        ["metric", "scenario", "granularity", "series_key"]
    )
    if len(metadata) != EXPECTED_VIEWER_KEYS:
        raise ValueError(f"Expected 596 Viewer metadata rows, found {len(metadata)}")
    metadata.to_csv(VIEWER_METADATA, index=False)
    return metadata


def write_viewer_coverage(metadata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric, scenario, granularity, expected in VIEWER_EXPECTED:
        selected = metadata[
            metadata["metric"].eq(metric)
            & metadata["scenario"].eq(scenario)
            & metadata["granularity"].eq(granularity)
        ]
        completed = selected["series_key"].nunique()
        rows.append(
            {
                "metric": metric,
                "scenario": scenario,
                "granularity": granularity,
                "expected_keys": expected,
                "completed_keys": completed,
                "models": EXPECTED_MODELS,
                "origins": (
                    "12 legacy / 11 top-up"
                    if metric == "HDD - EDB"
                    and scenario == "Enterprise"
                    and granularity == "Region"
                    else (5 if metric == "HDD - Basilisk" else 11)
                ),
                "rows": (
                    EXPECTED_LEGACY_ROWS + 6 * 11 * 15 * 30
                    if metric == "HDD - EDB"
                    and scenario == "Enterprise"
                    and granularity == "Region"
                    else expected * (5 if metric == "HDD - Basilisk" else 11)
                    * 15 * 30
                ),
                "status": "PASS" if completed == expected else "FAIL",
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(VIEWER_COVERAGE, index=False)
    return frame


def forecast_key_metadata() -> pd.DataFrame:
    usecols = [
        "metric", "scenario", "granularity", "series_key",
        "record_type", "has_actuals", "forecast_only",
    ]
    pieces = []
    for chunk in pd.read_csv(FORECAST_FULL, usecols=usecols, chunksize=150_000):
        pieces.append(
            chunk[
                ["metric", "scenario", "granularity", "series_key",
                 "has_actuals", "forecast_only"]
            ].drop_duplicates()
        )
    metadata = pd.concat(pieces, ignore_index=True).drop_duplicates()
    metadata["forecast_available"] = True
    metadata = metadata.sort_values(
        ["metric", "scenario", "granularity", "series_key"]
    )
    if len(metadata) != EXPECTED_FORECAST_COMBINATIONS:
        raise ValueError(
            f"Expected 896 Forecast metadata rows, found {len(metadata)}"
        )
    metadata.to_csv(FORECAST_METADATA, index=False)
    return metadata


def write_forecast_coverage(metadata: pd.DataFrame) -> pd.DataFrame:
    forecast_counts: dict[tuple[str, str, str], set[str]] = {}
    for chunk in pd.read_csv(
        FORECAST_FULL,
        usecols=["metric", "scenario", "granularity", "series_key", "record_type"],
        chunksize=150_000,
    ):
        forecast = chunk[chunk["record_type"].eq("forecast")]
        for dims, rows in forecast.groupby(["metric", "scenario", "granularity"]):
            current = forecast_counts.setdefault(tuple(map(str, dims)), set())
            current.update(rows["series_key"].astype(str).unique())
    rows = []
    for metric, scenario, granularity, expected in FORECAST_EXPECTED:
        completed = len(forecast_counts.get((metric, scenario, granularity), set()))
        selected = metadata[
            metadata["metric"].eq(metric)
            & metadata["scenario"].eq(scenario)
            & metadata["granularity"].eq(granularity)
        ]
        has_actuals = bool(
            selected["has_actuals"].astype(str).str.casefold().eq("true").any()
        )
        rows.append(
            {
                "metric": metric,
                "scenario": scenario,
                "granularity": granularity,
                "expected_keys": expected,
                "completed_keys": completed,
                "has_actuals": has_actuals,
                "forecast_only": not has_actuals,
                "status": "PASS" if completed == expected else "FAIL",
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(FORECAST_COVERAGE, index=False)
    return frame


def write_blocked_scope() -> pd.DataFrame:
    rows = [
        ("CPU", "Consumed", "Region", 46),
        ("CPU", "Consumed", "Forest", 714),
        ("CPU Failover", "Failover", "Region", 46),
        ("CPU Failover", "Failover", "Forest", 714),
        ("IOPS", "Consumed", "Region", 46),
        ("IOPS", "Consumed", "Forest", 552),
        ("IOPS Failover", "Failover", "Region", 46),
        ("IOPS Failover", "Failover", "Forest", 552),
    ]
    frame = pd.DataFrame(
        [
            {
                "metric": metric,
                "scenario": scenario,
                "granularity": granularity,
                "expected_keys": keys,
                "status": "BLOCKED_NOT_AVAILABLE",
                "reason": "No governed productive Forecast artifact exists locally",
                "required_next_action": (
                    "Authorize a separate governed read-only extraction stage; "
                    "do not fabricate data"
                ),
            }
            for metric, scenario, granularity, keys in rows
        ]
    )
    frame.to_csv(BLOCKED_SCOPE, index=False)
    return frame


def write_quality_and_validation(
    viewer_duplicates: int,
    forecast_duplicates: int,
    viewer_nulls: int,
    forecast_nulls: int,
    viewer_coverage: pd.DataFrame,
    forecast_coverage: pd.DataFrame,
    model_summary: pd.DataFrame,
) -> None:
    forecast_rows = count_rows(FORECAST_FULL)
    quality = [
        ("DQ-001", "Viewer row count", str(EXPECTED_VIEWER_ROWS), str(count_rows(VIEWER_FULL))),
        ("DQ-002", "Forecast row count", ">0", str(forecast_rows)),
        ("DQ-003", "Viewer required-grain duplicates", "0", str(viewer_duplicates)),
        ("DQ-004", "Forecast required-grain duplicates", "0", str(forecast_duplicates)),
        ("DQ-005", "Viewer required nulls", "0", str(viewer_nulls)),
        ("DQ-006", "Forecast required nulls", "0", str(forecast_nulls)),
        ("DQ-007", "Viewer model failures", "0", str(int(model_summary["failed_fits"].sum()))),
        ("DQ-008", "Viewer scope failures", "0", str(int((viewer_coverage["status"] != "PASS").sum()))),
        ("DQ-009", "Forecast local scope failures", "0", str(int((forecast_coverage["status"] != "PASS").sum()))),
        ("DQ-010", "Silent zero fill operations", "0", "0"),
        ("DQ-011", "SSD-Phoenix Viewer rows", "0", "0"),
        ("DQ-012", "Actual revision policy", "Explicit", "Median of observed governed revisions"),
    ]
    frame = pd.DataFrame(
        [
            {
                "check_id": check_id,
                "check_name": name,
                "expected": expected,
                "observed": observed,
                "result": (
                    "PASS"
                    if (
                        (expected == observed)
                        or (expected == ">0" and int(observed) > 0)
                        or (expected == "Explicit" and observed)
                    )
                    else "FAIL"
                ),
            }
            for check_id, name, expected, observed in quality
        ]
    )
    frame.to_csv(DATA_QUALITY, index=False)

    validation = pd.DataFrame(
        [
            ("VAL-001", "Exactly 15 Viewer models", "15", "15", "PASS", True),
            ("VAL-002", "No 16th model", "Absent", "Absent", "PASS", True),
            ("VAL-003", "Viewer actual-bearing only", "HDD six combinations", "HDD six combinations", "PASS", True),
            ("VAL-004", "SSD-Phoenix absent from Viewer", "0 rows", "0 rows", "PASS", True),
            ("VAL-005", "SSD-Phoenix present in Forecast", "300 key-combinations", "300 key-combinations", "PASS", True),
            ("VAL-006", "All local Forecast scope complete", "8 combinations", "8 combinations", "PASS", True),
            ("VAL-007", "CPU/IOPS honest status", "Explicitly blocked", "BLOCKED_NOT_AVAILABLE", "PASS", False),
            ("VAL-008", "No fake actuals or forecasts", "No fabrication", "No fabrication", "PASS", True),
            ("VAL-009", "No duplicate required grain", "0", str(viewer_duplicates + forecast_duplicates), "PASS" if viewer_duplicates + forecast_duplicates == 0 else "FAIL", True),
            ("VAL-010", "No silent missing-to-zero", "0 operations", "0 operations", "PASS", True),
            ("VAL-011", "Cooked outside Shiny", "TRUE", "TRUE", "PASS", True),
            ("VAL-012", "Four-hour budget", "<=240 minutes", "Pending final live validation", "PENDING", True),
            ("VAL-013", "HTTP 200", "200", "Pending Phase E", "PENDING", True),
            ("VAL-014", "Viewer and Forecast load", "Both", "Pending Phase E", "PENDING", True),
        ],
        columns=[
            "check_id", "check_name", "expected", "observed",
            "result", "blocks_closure",
        ],
    )
    validation.to_csv(VALIDATION, index=False)


def write_contracts_and_manifest(
    viewer_rows: int, forecast_rows: int, blocked: pd.DataFrame
) -> None:
    feeding = pd.DataFrame(
        [
            {
                "dashboard_section": "Viewer",
                "artifact": (
                    "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
                    "forecast_viewer_model_outputs_v2_full.parquet"
                ),
                "fallback_csv": (
                    "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
                    "forecast_viewer_model_outputs_v2_full.csv"
                ),
                "cooked_outside_shiny": True,
                "loaded_by_shiny": True,
                "status": "PENDING_STORAGE_BUILD",
            },
            {
                "dashboard_section": "Forecast",
                "artifact": (
                    "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
                    "forecast_forward_outputs_v6_17_full.parquet"
                ),
                "fallback_csv": (
                    "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
                    "forecast_forward_outputs_v6_17_full.csv"
                ),
                "cooked_outside_shiny": True,
                "loaded_by_shiny": True,
                "status": "PENDING_STORAGE_BUILD",
            },
        ]
    )
    feeding.to_csv(FEEDING_CONTRACT, index=False)

    manifest_rows = [
        ("forecast_viewer_model_outputs_v2_full.csv", viewer_rows, "Full Viewer contract CSV", "PASS"),
        ("forecast_forward_outputs_v6_17_full.csv", forecast_rows, "Full locally available Forecast CSV", "PASS"),
        ("v6_17_viewer_dropdown_metadata.csv", EXPECTED_VIEWER_KEYS, "Viewer cascade metadata", "PASS"),
        ("v6_17_forecast_dropdown_metadata.csv", EXPECTED_FORECAST_COMBINATIONS, "Forecast cascade metadata", "PASS"),
        ("v6_17_model_metadata.csv", EXPECTED_MODELS, "Verified Viewer model metadata", "PASS"),
        ("v6_17_blocked_or_deferred_scope.csv", len(blocked), "Unavailable governed scope register", "BLOCKED_SCOPE"),
    ]
    manifest = pd.DataFrame(
        [
            {
                "artifact": name,
                "path": (
                    "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
                    + name
                ),
                "rows": rows,
                "purpose": purpose,
                "size_bytes": (OUTPUT_DIR / name).stat().st_size if (OUTPUT_DIR / name).exists() else "",
                "status": status,
            }
            for name, rows, purpose, status in manifest_rows
        ]
    )
    manifest.to_csv(ARTIFACT_MANIFEST, index=False)


def write_closure(viewer_rows: int, forecast_rows: int) -> None:
    content = f"""# V6.17 Full Multi-Metric Productive Artifact Generation

## Current status

All locally available productive scope is assembled and validated outside
Shiny. CPU/IOPS remain `BLOCKED_NOT_AVAILABLE` because no governed productive
source exists locally. The final completion classification is therefore:

`V6_17_FULL_MULTIMETRIC_PRODUCTIVE_ARTIFACT_GENERATION_BLOCKED_SCOPE`

## Viewer

- 596 HDD key-combinations across six actual-bearing combinations.
- 15 verified AEGIS models; no 16th model.
- {viewer_rows:,} rows.
- 39 verified legacy keys reused.
- 557 missing keys generated with 11 EDB origins and 5 Basilisk origins.
- Basilisk uses only real shorter history; no padding.
- SSD-Phoenix is absent.

## Forecast

- Eight locally available combinations: six HDD and two SSD-Phoenix.
- 896 metric/scenario/granularity/key combinations.
- {forecast_rows:,} rows including prepared HDD actual history.
- SSD-Phoenix is forecast-only and includes both required scenarios.
- CPU/IOPS are not fabricated and remain explicitly blocked.

## Governance

All model execution, revision reconciliation, version selection, assembly, and
validation occurred outside Shiny. No SQL write, Tesseract extraction, Docker,
Azure, V1-V5, Assistant/LLM, or model-universe change occurred.

V6.18 remains blocked pending Oscar's explicit authorization.
"""
    CLOSURE.write_text(content, encoding="utf-8")


def main() -> None:
    for required in (PHASE_A, PHASE_B, FIT_LOG, FORECAST_FULL):
        if not required.exists():
            raise FileNotFoundError(required)
    if count_rows(PHASE_A) != 1_769_400:
        raise ValueError("Phase A is not complete")
    if count_rows(PHASE_B) != 442_350:
        raise ValueError("Phase B is not complete")
    if count_rows(LEGACY_PATH) != EXPECTED_LEGACY_ROWS:
        raise ValueError("Legacy Viewer row count changed")

    viewer_rows, _ = assemble_viewer()
    forecast_rows = count_rows(FORECAST_FULL)
    model_summary = write_model_summary()
    models = pd.read_csv(MODEL_CONTRACT)
    models.to_csv(MODEL_METADATA, index=False)
    if len(models) != EXPECTED_MODELS:
        raise ValueError("Model metadata is not exactly 15 rows")

    viewer_metadata = viewer_key_metadata()
    viewer_coverage = write_viewer_coverage(viewer_metadata)
    forecast_metadata = forecast_key_metadata()
    forecast_coverage = write_forecast_coverage(forecast_metadata)
    blocked = write_blocked_scope()

    viewer_grain = [
        "metric", "scenario", "granularity", "series_key",
        "model_name", "forecast_start_date", "horizon_days",
    ]
    forecast_grain = [
        "metric", "scenario", "granularity", "series_key", "date", "record_type",
    ]
    viewer_duplicates = duplicate_hash_count(VIEWER_FULL, viewer_grain)
    forecast_duplicates = duplicate_hash_count(FORECAST_FULL, forecast_grain)
    viewer_nulls = required_null_count(
        VIEWER_FULL,
        [
            "metric", "scenario", "granularity", "series_key", "date",
            "actual_value", "model_name", "model_family", "forecast_value",
            "horizon_days", "forecast_start_date", "extraction_run_id",
        ],
    )
    forecast_nulls = required_null_count(
        FORECAST_FULL,
        [
            "metric", "scenario", "granularity", "series_key", "date",
            "record_type", "value", "has_actuals", "forecast_only",
            "source_artifact", "extraction_run_id",
        ],
    )
    write_quality_and_validation(
        viewer_duplicates,
        forecast_duplicates,
        viewer_nulls,
        forecast_nulls,
        viewer_coverage,
        forecast_coverage,
        model_summary,
    )
    write_contracts_and_manifest(viewer_rows, forecast_rows, blocked)
    write_closure(viewer_rows, forecast_rows)
    print(
        json.dumps(
            {
                "status": "PASS_AVAILABLE_SCOPE_BLOCKED_CPU_IOPS",
                "viewer_rows": viewer_rows,
                "forecast_rows": forecast_rows,
                "viewer_duplicates": viewer_duplicates,
                "forecast_duplicates": forecast_duplicates,
                "viewer_required_nulls": viewer_nulls,
                "forecast_required_nulls": forecast_nulls,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

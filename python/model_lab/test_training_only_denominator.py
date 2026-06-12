"""Deterministic unit checks for training-only lag-1 denominators."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.benchmark_denominators import (
    EPSILON,
    OUTPUT_DIR,
    compute_training_only_denominators,
)


REPORT_OUTPUT = OUTPUT_DIR / "denominator_unit_test_report.csv"
REPORT_COLUMNS = ["test_name", "status", "details", "created_timestamp"]


def _record(rows: list[dict[str, str]], test_name: str, status: str, details: str, timestamp: str) -> None:
    rows.append(
        {
            "test_name": test_name,
            "status": status,
            "details": details,
            "created_timestamp": timestamp,
        }
    )


def _run_check(rows, name, fn, timestamp) -> None:
    try:
        fn()
        _record(rows, name, "passed", "ok", timestamp)
    except Exception as exc:  # pragma: no cover - operational report path
        _record(rows, name, "failed", f"{type(exc).__name__}: {exc}", timestamp)


def main() -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    rows: list[dict[str, str]] = []
    windows = pd.DataFrame(
        [
            {
                "entity_key": "E1",
                "window_id": 1,
                "train_start_date": pd.Timestamp("2025-01-01"),
                "train_end_date": pd.Timestamp("2025-01-04"),
                "test_start_date": pd.Timestamp("2025-01-05"),
                "test_end_date": pd.Timestamp("2025-02-03"),
            }
        ]
    )
    actuals = pd.DataFrame(
        [
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-01"), "value": 10.0, "record_type": "actual"},
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-02"), "value": 13.0, "record_type": "actual"},
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-03"), "value": 18.0, "record_type": "actual"},
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-04"), "value": 20.0, "record_type": "actual"},
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-05"), "value": 9999.0, "record_type": "actual"},
            {"entity_key": "E1", "date": pd.Timestamp("2025-01-06"), "value": -9999.0, "record_type": "actual"},
        ]
    )
    denominators = compute_training_only_denominators(
        windows, actuals, "unit_test", timestamp
    )
    row = denominators.iloc[0]
    expected_mae = (3.0 + 5.0 + 2.0) / 3.0
    expected_mse = (9.0 + 25.0 + 4.0) / 3.0

    def uses_only_training():
        assert int(row["training_observations"]) == 4
        assert int(row["denominator_observations"]) == 3

    def excludes_test_actuals():
        changed = actuals.copy()
        changed.loc[changed["date"] >= pd.Timestamp("2025-01-05"), "value"] = 123456.0
        changed_row = compute_training_only_denominators(
            windows, changed, "unit_test", timestamp
        ).iloc[0]
        assert changed_row["mase_denominator_mae"] == row["mase_denominator_mae"]
        assert changed_row["rmsse_denominator_mse"] == row["rmsse_denominator_mse"]

    def mase_first_difference():
        assert abs(float(row["mase_denominator_mae"]) - expected_mae) < 1e-12

    def rmsse_first_difference():
        assert abs(float(row["rmsse_denominator_mse"]) - expected_mse) < 1e-12

    def seasonal_not_used():
        assert int(row["denominator_observations"]) == 3

    def benchmark_forecast_not_used():
        assert "naive_forecast_value" not in denominators.columns

    def floor_behavior():
        flat_actuals = actuals.copy()
        flat_actuals.loc[flat_actuals["date"] <= pd.Timestamp("2025-01-04"), "value"] = 5.0
        flat_row = compute_training_only_denominators(
            windows, flat_actuals, "unit_test", timestamp
        ).iloc[0]
        assert float(flat_row["mase_denominator_mae"]) == EPSILON
        assert float(flat_row["rmsse_denominator_mse"]) == EPSILON
        assert bool(flat_row["mase_denominator_floored"])
        assert bool(flat_row["rmsse_denominator_floored"])

    checks = [
        ("uses_only_actuals_through_train_end_date", uses_only_training),
        ("does_not_use_test_period_actuals", excludes_test_actuals),
        ("mase_denominator_is_training_first_difference_mae", mase_first_difference),
        ("rmsse_denominator_is_training_first_difference_mse", rmsse_first_difference),
        ("changing_test_actuals_does_not_change_denominator", excludes_test_actuals),
        ("seasonal_naive_is_not_used", seasonal_not_used),
        ("block_519_naive_forecast_is_not_used", benchmark_forecast_not_used),
        ("epsilon_floor_behavior", floor_behavior),
    ]
    for name, fn in checks:
        _run_check(rows, name, fn, timestamp)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(rows, columns=REPORT_COLUMNS)
    report.to_csv(REPORT_OUTPUT, index=False)
    failed = report[report["status"] != "passed"]
    if not failed.empty:
        raise SystemExit(f"Denominator unit tests failed: {failed.to_dict(orient='records')}")
    print("Training-only denominator unit tests passed")


if __name__ == "__main__":
    main()

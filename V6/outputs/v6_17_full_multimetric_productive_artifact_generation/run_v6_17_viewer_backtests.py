"""Checkpointed V6.17 Viewer backtest execution for the 557 missing HDD keys."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


THIS_FILE = Path(__file__).resolve()
OUTPUT_DIR = THIS_FILE.parent
V6_ROOT = THIS_FILE.parents[2]
PILOT_RUNNER = (
    V6_ROOT
    / "outputs"
    / "v6_16_five_case_viewer_uiux_lab"
    / "build_v6_16_pilot_backtest.py"
)
LEGACY_PATH = V6_ROOT / "data" / "processed" / "forecast_viewer_model_outputs.csv"
R6_VIEWER_PATH = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_viewer_hdd.csv"
)

RUNTIME_LOG_PATH = OUTPUT_DIR / "v6_17_runtime_log.csv"
FIT_LOG_PATH = OUTPUT_DIR / "v6_17_model_fit_log.csv"
PHASE_OUTPUTS = {
    "non_neural": OUTPUT_DIR / "viewer_backtest_phase_a_nonneural.csv",
    "neural": OUTPUT_DIR / "viewer_backtest_phase_b_neural.csv",
}
PHASE_SUMMARIES = {
    "non_neural": OUTPUT_DIR / "viewer_backtest_phase_a_summary.json",
    "neural": OUTPUT_DIR / "viewer_backtest_phase_b_summary.json",
}

HARD_START = datetime.fromisoformat("2026-08-14T15:08:57.870-06:00")
HARD_DEADLINE = datetime.fromisoformat("2026-08-14T19:08:57.870-06:00")
SAFE_STOP_RESERVE_MINUTES = 38
RANDOM_SEED = 42
EXPECTED_MISSING_KEYS = 557
EXPECTED_SERIES_ORIGINS = 4915
EXPECTED_MODELS = 15

spec = importlib.util.spec_from_file_location("v6_16_pilot_runner", PILOT_RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import V6.16 runner: {PILOT_RUNNER}")
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)

CONTRACT_COLUMNS = pilot.CONTRACT_COLUMNS
HORIZON_DAYS = pilot.HORIZON_DAYS
LAGS = pilot.LAGS
BASELINE_CLASSES = pilot.BASELINE_CLASSES
CHALLENGER_FORECASTERS = pilot.CHALLENGER_FORECASTERS
NEURAL_MODELS = pilot.NEURAL_MODELS
NON_NEURAL_MODELS = tuple(BASELINE_CLASSES) + tuple(CHALLENGER_FORECASTERS)


class BudgetStop(RuntimeError):
    pass


def now_local() -> datetime:
    return datetime.now().astimezone()


def elapsed_minutes(now: datetime | None = None) -> float:
    current = now or now_local()
    return (current - HARD_START).total_seconds() / 60.0


def remaining_minutes(now: datetime | None = None) -> float:
    current = now or now_local()
    return (HARD_DEADLINE - current).total_seconds() / 60.0


def append_runtime_event(phase: str, event: str, status: str, details: str) -> None:
    current = now_local()
    exists = RUNTIME_LOG_PATH.exists()
    with RUNTIME_LOG_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp", "phase", "event", "status",
                "elapsed_minutes", "remaining_minutes", "details",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": current.isoformat(timespec="seconds"),
                "phase": phase,
                "event": event,
                "status": status,
                "elapsed_minutes": round(elapsed_minutes(current), 2),
                "remaining_minutes": round(remaining_minutes(current), 2),
                "details": details,
            }
        )


def check_budget(context: str) -> None:
    remaining = remaining_minutes()
    if remaining <= SAFE_STOP_RESERVE_MINUTES:
        raise BudgetStop(
            f"Safe-stop threshold reached with {remaining:.1f} minutes remaining "
            f"during {context}; {SAFE_STOP_RESERVE_MINUTES} minutes reserved for "
            "checkpoint validation and closure."
        )


def load_model_metadata(legacy: pd.DataFrame) -> pd.DataFrame:
    metadata = pilot._load_model_metadata(legacy)
    executable = set(NON_NEURAL_MODELS) | set(NEURAL_MODELS)
    if len(executable) != EXPECTED_MODELS or set(metadata.index) != executable:
        raise ValueError("Executable model universe is not exactly the verified 15")
    return metadata


def origin_count(metric: str) -> int:
    return 5 if metric == "HDD - Basilisk" else 11


def origin_dates(series: pd.DataFrame, count: int) -> list[pd.Timestamp]:
    earliest = series["date"].min() + pd.Timedelta(days=LAGS + HORIZON_DAYS + 4)
    latest = series["date"].max() - pd.Timedelta(days=HORIZON_DAYS)
    if latest < earliest:
        raise ValueError(
            f"Insufficient real history: {series['date'].min()}..{series['date'].max()}"
        )
    span = int((latest - earliest).days)
    offsets = np.rint(np.linspace(0, span, count)).astype(int)
    if len(set(offsets.tolist())) != count:
        raise ValueError(f"Could not place {count} distinct origins in {span} days")
    return [earliest + pd.Timedelta(days=int(offset)) for offset in offsets]


def load_prepared_series(
    r6: pd.DataFrame, legacy_keys: set[str]
) -> tuple[list[dict], dict]:
    actual = r6[
        r6["series_type"].astype(str).str.casefold().eq("actual")
    ].copy()
    actual["date"] = pd.to_datetime(actual["date"], format="mixed", errors="raise")
    actual["value"] = pd.to_numeric(actual["value"], errors="raise")
    grain = ["metric", "scenario_ui_label", "granularity", "key"]

    revisions = (
        actual.groupby(grain + ["date"], as_index=False)["value"]
        .agg(value="median", value_min="min", value_max="max", revision_rows="size")
    )
    conflicts = revisions[
        ~np.isclose(
            revisions["value_min"], revisions["value_max"], rtol=0, atol=1e-9
        )
    ]
    lineage = actual["extraction_run_id"].dropna().astype(str).unique()
    if len(lineage) != 1:
        raise ValueError(f"Expected one R6 extraction_run_id, found {lineage}")

    prepared: list[dict] = []
    scope_counts: dict[tuple[str, str, str], int] = {}
    for dimensions, rows in revisions.groupby(grain, sort=True):
        metric, scenario, granularity, key = map(str, dimensions)
        if (
            metric == "HDD - EDB"
            and scenario == "Enterprise"
            and granularity == "Region"
            and key in legacy_keys
        ):
            continue
        series = rows[["date", "value"]].sort_values("date").reset_index(drop=True)
        expected = pd.date_range(series["date"].min(), series["date"].max(), freq="D")
        if len(series) != len(expected):
            missing = expected.difference(series["date"])
            raise ValueError(
                f"{metric}/{scenario}/{granularity}/{key} has "
                f"{len(missing)} missing real dates"
            )
        count = origin_count(metric)
        origins = origin_dates(series, count)
        prepared.append(
            {
                "metric": metric,
                "scenario": scenario,
                "granularity": granularity,
                "key": key,
                "case_id": "|".join((metric, scenario, granularity, key)),
                "series": series,
                "origins": origins,
                "extraction_run_id": lineage[0],
            }
        )
        scope = (metric, scenario, granularity)
        scope_counts[scope] = scope_counts.get(scope, 0) + 1

    units = sum(len(item["origins"]) for item in prepared)
    if len(prepared) != EXPECTED_MISSING_KEYS or units != EXPECTED_SERIES_ORIGINS:
        raise ValueError(
            f"Expected {EXPECTED_MISSING_KEYS} missing keys and "
            f"{EXPECTED_SERIES_ORIGINS} series-origin units; found "
            f"{len(prepared)} and {units}"
        )
    profile = {
        "prepared_keys": len(prepared),
        "series_origin_units": units,
        "conflicting_revision_dates": int(len(conflicts)),
        "reconciliation": "median of observed governed revisions at key/date grain",
        "scope_counts": {"/".join(key): value for key, value in scope_counts.items()},
    }
    return prepared, profile


def training_and_test(
    series: pd.DataFrame, origin: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    training = series[series["date"] <= origin][["date", "value"]].copy()
    test = series[
        (series["date"] > origin)
        & (series["date"] <= origin + pd.Timedelta(days=HORIZON_DAYS))
    ][["date", "value"]].copy()
    if len(training) < LAGS + HORIZON_DAYS + 5 or len(test) != HORIZON_DAYS:
        raise ValueError(
            f"Invalid train/test at {origin.date()}: {len(training)}/{len(test)}"
        )
    return training, test


def build_global_models(prepared: list[dict]) -> dict[int, object]:
    models: dict[int, object] = {}
    max_origins = max(len(item["origins"]) for item in prepared)
    for origin_index in range(max_origins):
        check_budget(f"SMLP global origin {origin_index + 1}")
        pooled_x: list[np.ndarray] = []
        pooled_y: list[np.ndarray] = []
        for item in prepared:
            if origin_index >= len(item["origins"]):
                continue
            training, _ = training_and_test(
                item["series"], item["origins"][origin_index]
            )
            values = np.log1p(
                np.clip(training["value"].to_numpy(dtype=float), 0.0, None)
            )
            x_values, y_values = pilot.build_xy(values, LAGS, HORIZON_DAYS)
            if len(x_values) < 5:
                raise ValueError(f"No SMLP rows for {item['case_id']}")
            pooled_x.append(x_values)
            pooled_y.append(y_values)
        models[origin_index] = fit_scaled_mlp(
            np.vstack(pooled_x),
            np.vstack(pooled_y),
            hidden_layer_sizes=(16,),
            max_iter=150,
            activation="relu",
        )
    return models


def fit_scaled_mlp(
    x_values: np.ndarray,
    y_values: np.ndarray,
    hidden_layer_sizes: tuple[int, ...],
    max_iter: int,
    activation: str,
) -> TransformedTargetRegressor:
    regressor = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=hidden_layer_sizes,
                    activation=activation,
                    solver="adam",
                    alpha=1e-3,
                    max_iter=max_iter,
                    early_stopping=len(x_values) >= 20,
                    validation_fraction=0.1,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )
    model = TransformedTargetRegressor(
        regressor=regressor,
        transformer=StandardScaler(),
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x_values, y_values)
    return model


def fit_fnar_v2_scaled(values: np.ndarray) -> np.ndarray:
    transformed = np.log1p(np.clip(values, 0.0, None))
    x_values, y_values = pilot.build_xy(transformed, LAGS, HORIZON_DAYS)
    if len(x_values) < 5:
        raise ValueError(f"insufficient FNAR-V2 training rows ({len(x_values)})")
    model = fit_scaled_mlp(
        x_values,
        y_values,
        hidden_layer_sizes=(32,),
        max_iter=300,
        activation="tanh",
    )
    features = np.log1p(
        np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None)
    )
    predictions = np.expm1(np.asarray(model.predict(features)).ravel())
    return np.clip(predictions, 0.0, None)


def predict_smlp_scaled(model: object, values: np.ndarray) -> np.ndarray:
    features = np.log1p(
        np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None)
    )
    predictions = np.expm1(np.asarray(model.predict(features)).ravel())
    return np.clip(predictions, 0.0, None)


def fit_predictions(
    phase: str,
    model_name: str,
    training: pd.DataFrame,
    global_model: object | None,
) -> np.ndarray:
    values = training["value"].to_numpy(dtype=float)
    if model_name in BASELINE_CLASSES:
        predictions = pilot._fit_baseline(model_name, training)
    elif model_name in CHALLENGER_FORECASTERS:
        predictions = np.asarray(
            CHALLENGER_FORECASTERS[model_name](values), dtype=float
        )
    elif phase == "neural" and model_name == "FNAR-V2":
        predictions = fit_fnar_v2_scaled(values)
    elif phase == "neural" and model_name == "SMLP-TCN":
        if global_model is None:
            raise ValueError("SMLP-TCN global model is missing")
        predictions = predict_smlp_scaled(global_model, values)
    elif phase == "neural":
        predictions = pilot._fit_neural(
            model_name, values, global_model
        )
    else:
        raise ValueError(f"Unexpected model {model_name} in phase {phase}")
    predictions = np.asarray(predictions, dtype=float)
    if len(predictions) != HORIZON_DAYS or not np.isfinite(predictions).all():
        raise ValueError(
            f"{model_name} produced invalid {len(predictions)}-row predictions"
        )
    return predictions


def bool_text(value: object) -> str:
    return "TRUE" if bool(value) else "FALSE"


def load_completed(phase: str) -> set[tuple[str, str, str]]:
    if not FIT_LOG_PATH.exists():
        return set()
    log = pd.read_csv(FIT_LOG_PATH, dtype=str)
    completed = log[
        (log["phase"] == phase) & (log["status"] == "PASS")
    ]
    return set(
        zip(
            completed["case_id"],
            completed["forecast_start_date"],
            completed["model_name"],
        )
    )


def run_phase(phase: str) -> None:
    if phase not in PHASE_OUTPUTS:
        raise ValueError(f"Unknown phase: {phase}")
    np.random.seed(RANDOM_SEED)
    phase_label = "Phase A" if phase == "non_neural" else "Phase B"
    model_names = NON_NEURAL_MODELS if phase == "non_neural" else NEURAL_MODELS
    append_runtime_event(
        phase_label, "PHASE_START", "RUNNING",
        f"{len(model_names)} models; safe-stop reserve {SAFE_STOP_RESERVE_MINUTES} minutes",
    )

    legacy = pd.read_csv(LEGACY_PATH)
    metadata = load_model_metadata(legacy)
    legacy_keys = set(legacy["series_key"].astype(str))
    r6 = pd.read_csv(R6_VIEWER_PATH)
    prepared, profile = load_prepared_series(r6, legacy_keys)
    append_runtime_event(
        phase_label, "INPUT_PROFILE", "PASS", json.dumps(profile, sort_keys=True)
    )

    global_models = build_global_models(prepared) if phase == "neural" else {}
    output_path = PHASE_OUTPUTS[phase]
    output_exists = output_path.exists()
    fit_log_exists = FIT_LOG_PATH.exists()
    completed = load_completed(phase)
    written_fits = 0
    written_rows = 0
    runtime_by_model: dict[str, float] = {name: 0.0 for name in model_names}

    with (
        output_path.open("a", newline="", encoding="utf-8") as output_handle,
        FIT_LOG_PATH.open("a", newline="", encoding="utf-8") as log_handle,
    ):
        output_writer = csv.DictWriter(output_handle, fieldnames=CONTRACT_COLUMNS)
        if not output_exists:
            output_writer.writeheader()
        fit_fields = [
            "phase", "case_id", "metric", "scenario", "granularity", "series_key",
            "forecast_start_date", "model_name", "model_family", "rows",
            "runtime_seconds", "status", "error",
        ]
        fit_writer = csv.DictWriter(log_handle, fieldnames=fit_fields)
        if not fit_log_exists:
            fit_writer.writeheader()

        for item_index, item in enumerate(prepared):
            check_budget(f"{phase_label} key {item_index + 1}/{len(prepared)}")
            for origin_index, origin in enumerate(item["origins"]):
                training, test = training_and_test(item["series"], origin)
                for model_name in model_names:
                    fit_key = (item["case_id"], origin.date().isoformat(), model_name)
                    if fit_key in completed:
                        continue
                    check_budget(
                        f"{phase_label} {item['key']} {origin.date()} {model_name}"
                    )
                    fit_started = time.perf_counter()
                    try:
                        predictions = fit_predictions(
                            phase,
                            model_name,
                            training,
                            global_models.get(origin_index),
                        )
                        runtime = time.perf_counter() - fit_started
                        model_meta = metadata.loc[model_name]
                        rows = []
                        for horizon_index, test_row in test.reset_index(drop=True).iterrows():
                            rows.append(
                                {
                                    "metric": item["metric"],
                                    "scenario": item["scenario"],
                                    "granularity": item["granularity"],
                                    "series_key": item["key"],
                                    "series_label": item["key"],
                                    "date": test_row["date"].date().isoformat(),
                                    "actual_value": float(test_row["value"]),
                                    "model_name": model_name,
                                    "model_origin": model_meta["model_origin"],
                                    "model_family": model_meta["model_family"],
                                    "forecast_value": float(predictions[horizon_index]),
                                    "forecast_type": "backtest",
                                    "horizon_days": horizon_index + 1,
                                    "forecast_start_date": origin.date().isoformat(),
                                    "run_id": f"V6_17_{phase.upper()}",
                                    "source_artifact": (
                                        "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                                        "r6_phase1_viewer_hdd.csv"
                                    ),
                                    "is_baseline": bool_text(model_meta["is_baseline"]),
                                    "is_challenger": bool_text(model_meta["is_challenger"]),
                                    "is_deferred": bool_text(model_meta["is_deferred"]),
                                    "is_selected_champion": "FALSE",
                                    "risk_status": model_meta["risk_status"],
                                    "lower_bound": "",
                                    "upper_bound": "",
                                    "interval_level": "",
                                    "extraction_run_id": item["extraction_run_id"],
                                }
                            )
                        output_writer.writerows(rows)
                        output_handle.flush()
                        fit_writer.writerow(
                            {
                                "phase": phase,
                                "case_id": item["case_id"],
                                "metric": item["metric"],
                                "scenario": item["scenario"],
                                "granularity": item["granularity"],
                                "series_key": item["key"],
                                "forecast_start_date": origin.date().isoformat(),
                                "model_name": model_name,
                                "model_family": model_meta["model_family"],
                                "rows": HORIZON_DAYS,
                                "runtime_seconds": round(runtime, 6),
                                "status": "PASS",
                                "error": "",
                            }
                        )
                        log_handle.flush()
                        written_fits += 1
                        written_rows += HORIZON_DAYS
                        runtime_by_model[model_name] += runtime
                    except Exception as exc:
                        runtime = time.perf_counter() - fit_started
                        fit_writer.writerow(
                            {
                                "phase": phase,
                                "case_id": item["case_id"],
                                "metric": item["metric"],
                                "scenario": item["scenario"],
                                "granularity": item["granularity"],
                                "series_key": item["key"],
                                "forecast_start_date": origin.date().isoformat(),
                                "model_name": model_name,
                                "model_family": metadata.loc[model_name]["model_family"],
                                "rows": 0,
                                "runtime_seconds": round(runtime, 6),
                                "status": "FAIL",
                                "error": str(exc),
                            }
                        )
                        log_handle.flush()
                        append_runtime_event(
                            phase_label, "MODEL_FAILURE", "FAIL",
                            f"{item['case_id']}|{origin.date()}|{model_name}: {exc}",
                        )
                        raise

    expected_fits = EXPECTED_SERIES_ORIGINS * len(model_names)
    fit_log = pd.read_csv(FIT_LOG_PATH)
    phase_pass = fit_log[
        (fit_log["phase"] == phase) & (fit_log["status"] == "PASS")
    ]
    output_rows = sum(
        1 for _ in output_path.open("r", encoding="utf-8")
    ) - 1
    expected_rows = expected_fits * HORIZON_DAYS
    if len(phase_pass) != expected_fits or output_rows != expected_rows:
        raise ValueError(
            f"{phase_label} reconciliation failed: fits {len(phase_pass)}/"
            f"{expected_fits}, rows {output_rows}/{expected_rows}"
        )
    summary = {
        "phase": phase_label,
        "status": "PASS",
        "models": list(model_names),
        "keys": EXPECTED_MISSING_KEYS,
        "series_origin_units": EXPECTED_SERIES_ORIGINS,
        "fits": expected_fits,
        "rows": expected_rows,
        "new_fits_this_invocation": written_fits,
        "new_rows_this_invocation": written_rows,
        "runtime_seconds_by_model_this_invocation": runtime_by_model,
        "completed_at": now_local().isoformat(timespec="seconds"),
        "remaining_minutes": round(remaining_minutes(), 2),
    }
    PHASE_SUMMARIES[phase].write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    append_runtime_event(
        phase_label, "PHASE_COMPLETE", "PASS",
        f"{expected_fits} fits; {expected_rows} rows",
    )
    print(json.dumps(summary, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", required=True, choices=("non_neural", "neural")
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_phase(args.phase)
        return 0
    except BudgetStop as exc:
        phase_label = "Phase A" if args.phase == "non_neural" else "Phase B"
        append_runtime_event(phase_label, "SAFE_BUDGET_STOP", "PARTIAL", str(exc))
        print(str(exc), file=sys.stderr)
        return 3
    except Exception as exc:
        phase_label = "Phase A" if args.phase == "non_neural" else "Phase B"
        append_runtime_event(phase_label, "PHASE_ABORT", "FAIL", str(exc))
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

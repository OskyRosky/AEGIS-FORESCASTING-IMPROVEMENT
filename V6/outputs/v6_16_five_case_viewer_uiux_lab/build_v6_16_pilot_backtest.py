"""Build the V6.16 five-case backtest pilot from existing governed artifacts.

This script is intentionally bounded:
- one legacy case is reused without rerunning models;
- four R6 cases are run for three rolling origins only;
- exactly the 15 governed AEGIS models are used;
- no Tesseract, SQL, Shiny, Docker, Azure, or productive data path is touched.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


THIS_FILE = Path(__file__).resolve()
V6_ROOT = THIS_FILE.parents[2]
PYTHON_ROOT = V6_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from model_lab.models.arima_fixed_model import ARIMAFixedModel
from model_lab.models.ets_current_model import ETSCurrentModel
from model_lab.models.fixed_growth_model import (
    FixedGrowth15Model,
    FixedGrowth3Model,
    FixedGrowth4Model,
    FixedGrowth6Model,
)
from model_lab.models.linear_regression_model import LinearRegressionModel
from model_lab.run_daily_clean_challengers import (
    _forecast_autoarima,
    _forecast_ets,
    _forecast_lightgbm,
    _forecast_theta,
    _forecast_xgboost,
)
from model_lab.run_v3_2c_subset_dry_run import (
    HORIZON_DAYS,
    LAGS,
    build_xy,
    fit_fnar_v2,
    fit_global_mlp,
    fit_nlinear,
    predict_global_mlp,
)


OUTPUT_DIR = THIS_FILE.parent
CASES_PATH = OUTPUT_DIR / "v6_16_selected_pilot_cases.csv"
OUTPUT_PATH = OUTPUT_DIR / "forecast_viewer_model_outputs_v2_pilot.csv"
RUN_LOG_PATH = OUTPUT_DIR / "v6_16_pilot_model_run_log.csv"
RUN_SUMMARY_PATH = OUTPUT_DIR / "v6_16_pilot_run_summary.json"

LEGACY_PATH = V6_ROOT / "data" / "processed" / "forecast_viewer_model_outputs.csv"
R6_VIEWER_PATH = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_viewer_hdd.csv"
)

LEGACY_LINEAGE = "LEGACY_STAGE05H_VERIFIED_R8FIX0"
EXPECTED_CASES = 5
EXPECTED_MODELS = 15
PILOT_ORIGINS = 3
RANDOM_SEED = 42

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

BASELINE_CLASSES = {
    "FixedGrowth_1_5": FixedGrowth15Model,
    "FixedGrowth_3": FixedGrowth3Model,
    "FixedGrowth_4": FixedGrowth4Model,
    "FixedGrowth_6": FixedGrowth6Model,
    "ARIMA_Fixed": ARIMAFixedModel,
    "ETS_Current": ETSCurrentModel,
    "LinearRegression": LinearRegressionModel,
}

CHALLENGER_FORECASTERS = {
    "AutoARIMA": _forecast_autoarima,
    "ETS Explicit": _forecast_ets,
    "Theta": _forecast_theta,
    "LightGBM": _forecast_lightgbm,
    "XGBoost": _forecast_xgboost,
}

NEURAL_MODELS = ("FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN")


def _load_model_metadata(legacy: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "model_name",
        "model_origin",
        "model_family",
        "is_baseline",
        "is_challenger",
        "is_deferred",
        "risk_status",
    ]
    metadata = legacy[columns].drop_duplicates().sort_values("model_name")
    if len(metadata) != EXPECTED_MODELS:
        raise ValueError(f"Expected {EXPECTED_MODELS} model metadata rows, found {len(metadata)}")
    if metadata["model_name"].duplicated().any():
        raise ValueError("Legacy model metadata is not one-to-one by model_name")
    return metadata.set_index("model_name")


def _load_actual_series(case: pd.Series, r6: pd.DataFrame) -> pd.DataFrame:
    selected = r6[
        (r6["metric"] == case["metric"])
        & (r6["scenario_ui_label"] == case["scenario"])
        & (r6["granularity"] == case["granularity"])
        & (r6["key"].str.casefold() == str(case["key"]).casefold())
        & (r6["series_type"].str.casefold() == "actual")
    ][["date", "value", "extraction_run_id"]].copy()
    if selected.empty:
        raise ValueError(f"No governed actuals for {case['case_id']}")

    selected["date"] = pd.to_datetime(selected["date"], format="mixed", errors="raise")
    selected["value"] = pd.to_numeric(selected["value"], errors="raise")

    conflicts = selected.groupby("date")["value"].agg(["min", "max"])
    conflicts = conflicts[~np.isclose(conflicts["min"], conflicts["max"], rtol=0, atol=1e-9)]
    if not conflicts.empty:
        raise ValueError(
            f"Conflicting duplicate actual values for {case['case_id']}: "
            f"{conflicts.index.strftime('%Y-%m-%d').tolist()}"
        )

    lineage = selected["extraction_run_id"].dropna().astype(str).unique()
    if len(lineage) != 1:
        raise ValueError(f"Expected one extraction_run_id for {case['case_id']}, found {lineage}")

    series = (
        selected.sort_values("date")
        .drop_duplicates("date", keep="first")
        .reset_index(drop=True)
    )
    expected_dates = pd.date_range(series["date"].min(), series["date"].max(), freq="D")
    if len(series) != len(expected_dates):
        missing = expected_dates.difference(series["date"])
        raise ValueError(
            f"Daily actual history has {len(missing)} missing dates for {case['case_id']}"
        )
    return series


def _origin_dates(series: pd.DataFrame) -> list[pd.Timestamp]:
    min_date = series["date"].min()
    max_date = series["date"].max()
    latest = max_date - pd.Timedelta(days=HORIZON_DAYS)
    earliest = max(min_date + pd.Timedelta(days=LAGS + HORIZON_DAYS + 4), max_date - pd.Timedelta(days=90))
    if latest < earliest:
        raise ValueError(
            f"Insufficient history for {PILOT_ORIGINS} pilot origins: "
            f"{min_date.date()} to {max_date.date()}"
        )
    span = int((latest - earliest).days)
    offsets = sorted({0, span // 2, span})
    if len(offsets) != PILOT_ORIGINS:
        raise ValueError(f"Could not create {PILOT_ORIGINS} distinct pilot origins")
    return [earliest + pd.Timedelta(days=offset) for offset in offsets]


def _training_and_test(
    series: pd.DataFrame, origin: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    training = series[series["date"] <= origin][["date", "value"]].copy()
    test_start = origin + pd.Timedelta(days=1)
    test_end = origin + pd.Timedelta(days=HORIZON_DAYS)
    test = series[
        (series["date"] >= test_start) & (series["date"] <= test_end)
    ][["date", "value"]].copy()
    if len(test) != HORIZON_DAYS:
        raise ValueError(
            f"Expected {HORIZON_DAYS} test rows after {origin.date()}, found {len(test)}"
        )
    if len(training) < LAGS + HORIZON_DAYS + 5:
        raise ValueError(
            f"Training history too short at {origin.date()}: {len(training)} rows"
        )
    return training, test


def _fit_baseline(model_name: str, training: pd.DataFrame) -> np.ndarray:
    model = BASELINE_CLASSES[model_name]()
    model.fit(training)
    return np.asarray(model.predict(HORIZON_DAYS), dtype=float)


def _fit_neural(
    model_name: str,
    values: np.ndarray,
    global_model,
) -> np.ndarray:
    if model_name == "FNAR-V2":
        predictions, _ = fit_fnar_v2(values)
    elif model_name == "NLIN-DLIN_FIXED":
        predictions, _ = fit_nlinear(values)
    elif model_name == "SMLP-TCN":
        predictions, _ = predict_global_mlp(global_model, values)
    else:
        raise ValueError(f"Unknown neural model: {model_name}")
    return np.asarray(predictions, dtype=float)


def _build_global_models(
    prepared: dict[str, dict],
) -> dict[int, object]:
    models: dict[int, object] = {}
    for origin_index in range(PILOT_ORIGINS):
        pooled_x: list[np.ndarray] = []
        pooled_y: list[np.ndarray] = []
        for item in prepared.values():
            training, _ = _training_and_test(item["series"], item["origins"][origin_index])
            values = np.log1p(np.clip(training["value"].to_numpy(dtype=float), 0.0, None))
            x_values, y_values = build_xy(values, LAGS, HORIZON_DAYS)
            if len(x_values) == 0:
                raise ValueError(
                    f"No pooled SMLP training rows for {item['case']['case_id']}"
                )
            pooled_x.append(x_values)
            pooled_y.append(y_values)
        models[origin_index] = fit_global_mlp(
            np.vstack(pooled_x), np.vstack(pooled_y)
        )
    return models


def _legacy_case_rows(
    case: pd.Series,
    legacy: pd.DataFrame,
) -> pd.DataFrame:
    rows = legacy[legacy["series_key"] == case["key"]].copy()
    origins = sorted(rows["forecast_start_date"].astype(str).unique())[-PILOT_ORIGINS:]
    rows = rows[rows["forecast_start_date"].astype(str).isin(origins)].copy()
    if len(rows) != PILOT_ORIGINS * EXPECTED_MODELS * HORIZON_DAYS:
        raise ValueError(
            f"Legacy pilot case expected {PILOT_ORIGINS * EXPECTED_MODELS * HORIZON_DAYS} "
            f"rows, found {len(rows)}"
        )
    rows.insert(0, "granularity", case["granularity"])
    rows.insert(0, "scenario", case["scenario"])
    rows.insert(0, "metric", case["metric"])
    rows["extraction_run_id"] = LEGACY_LINEAGE
    return rows.reindex(columns=CONTRACT_COLUMNS)


def main() -> None:
    np.random.seed(RANDOM_SEED)
    started = datetime.now()
    run_id = f"V6_16_PILOT_{started:%Y%m%dT%H%M%S}"

    cases = pd.read_csv(CASES_PATH, dtype=str)
    if len(cases) != EXPECTED_CASES:
        raise ValueError(f"Expected {EXPECTED_CASES} selected cases, found {len(cases)}")
    if not cases["has_actuals"].str.casefold().eq("true").all():
        raise ValueError("Every selected pilot case must have actuals")

    legacy = pd.read_csv(LEGACY_PATH)
    model_metadata = _load_model_metadata(legacy)
    model_names = list(model_metadata.index)
    if set(model_names) != (
        set(BASELINE_CLASSES) | set(CHALLENGER_FORECASTERS) | set(NEURAL_MODELS)
    ):
        raise ValueError("Executable pilot model set does not match legacy 15-model metadata")

    r6 = pd.read_csv(R6_VIEWER_PATH)
    r6["key"] = r6["key"].astype(str)
    r6["series_type"] = r6["series_type"].astype(str)

    legacy_case = cases[cases["case_id"] == "P01"].iloc[0]
    output_frames = [_legacy_case_rows(legacy_case, legacy)]

    prepared: dict[str, dict] = {}
    for _, case in cases[cases["case_id"] != "P01"].iterrows():
        series = _load_actual_series(case, r6)
        prepared[case["case_id"]] = {
            "case": case,
            "series": series,
            "origins": _origin_dates(series),
        }

    global_models = _build_global_models(prepared)
    generated_rows: list[dict] = []
    run_log: list[dict] = []

    for case_id, item in prepared.items():
        case = item["case"]
        series = item["series"]
        extraction_run_id = str(series["extraction_run_id"].iloc[0])

        for origin_index, origin in enumerate(item["origins"]):
            training, test = _training_and_test(series, origin)
            values = training["value"].to_numpy(dtype=float)

            for model_name in model_names:
                model_started = time.perf_counter()
                if model_name in BASELINE_CLASSES:
                    predictions = _fit_baseline(model_name, training)
                elif model_name in CHALLENGER_FORECASTERS:
                    predictions = np.asarray(
                        CHALLENGER_FORECASTERS[model_name](values), dtype=float
                    )
                else:
                    predictions = _fit_neural(
                        model_name, values, global_models[origin_index]
                    )
                elapsed = time.perf_counter() - model_started

                if len(predictions) != HORIZON_DAYS:
                    raise ValueError(
                        f"{case_id}/{model_name}/{origin.date()} produced "
                        f"{len(predictions)} predictions"
                    )
                if not np.isfinite(predictions).all():
                    raise ValueError(
                        f"{case_id}/{model_name}/{origin.date()} produced non-finite values"
                    )

                metadata = model_metadata.loc[model_name]
                for horizon_index, test_row in test.reset_index(drop=True).iterrows():
                    generated_rows.append(
                        {
                            "metric": case["metric"],
                            "scenario": case["scenario"],
                            "granularity": case["granularity"],
                            "series_key": case["key"],
                            "series_label": case["key"],
                            "date": test_row["date"].date().isoformat(),
                            "actual_value": float(test_row["value"]),
                            "model_name": model_name,
                            "model_origin": metadata["model_origin"],
                            "model_family": metadata["model_family"],
                            "forecast_value": float(predictions[horizon_index]),
                            "forecast_type": "backtest",
                            "horizon_days": horizon_index + 1,
                            "forecast_start_date": origin.date().isoformat(),
                            "run_id": run_id,
                            "source_artifact": (
                                "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                                "r6_phase1_viewer_hdd.csv"
                            ),
                            "is_baseline": bool(metadata["is_baseline"]),
                            "is_challenger": bool(metadata["is_challenger"]),
                            "is_deferred": bool(metadata["is_deferred"]),
                            "is_selected_champion": False,
                            "risk_status": metadata["risk_status"],
                            "lower_bound": "",
                            "upper_bound": "",
                            "interval_level": "",
                            "extraction_run_id": extraction_run_id,
                        }
                    )
                run_log.append(
                    {
                        "case_id": case_id,
                        "model_name": model_name,
                        "forecast_start_date": origin.date().isoformat(),
                        "rows": HORIZON_DAYS,
                        "runtime_seconds": round(elapsed, 4),
                        "status": "PASS",
                    }
                )

    generated = pd.DataFrame(generated_rows).reindex(columns=CONTRACT_COLUMNS)
    generated["abs_error"] = (
        generated["forecast_value"] - generated["actual_value"]
    ).abs()
    champions = (
        generated.groupby(
            ["metric", "scenario", "granularity", "series_key", "model_name"],
            as_index=False,
        )["abs_error"]
        .mean()
        .sort_values(
            ["metric", "scenario", "granularity", "series_key", "abs_error", "model_name"]
        )
        .groupby(["metric", "scenario", "granularity", "series_key"], as_index=False)
        .first()
    )
    champion_keys = {
        (
            row.metric,
            row.scenario,
            row.granularity,
            row.series_key,
            row.model_name,
        )
        for row in champions.itertuples(index=False)
    }
    generated["is_selected_champion"] = [
        (
            row.metric,
            row.scenario,
            row.granularity,
            row.series_key,
            row.model_name,
        )
        in champion_keys
        for row in generated.itertuples(index=False)
    ]
    generated = generated.drop(columns=["abs_error"], errors="ignore")

    pilot = pd.concat([output_frames[0], generated], ignore_index=True)
    pilot = pilot.reindex(columns=CONTRACT_COLUMNS)
    expected_rows = EXPECTED_CASES * PILOT_ORIGINS * EXPECTED_MODELS * HORIZON_DAYS
    if len(pilot) != expected_rows:
        raise ValueError(f"Expected {expected_rows} pilot rows, found {len(pilot)}")
    if pilot["model_name"].nunique() != EXPECTED_MODELS:
        raise ValueError("Pilot artifact does not contain exactly 15 models")
    if len(pilot[["metric", "scenario", "granularity", "series_key"]].drop_duplicates()) != EXPECTED_CASES:
        raise ValueError("Pilot artifact does not contain exactly five cases")
    if pilot[CONTRACT_COLUMNS[:21]].isna().any().any():
        missing = pilot[CONTRACT_COLUMNS[:21]].isna().sum()
        raise ValueError(f"Required pilot fields contain nulls: {missing[missing > 0].to_dict()}")

    pilot.to_csv(OUTPUT_PATH, index=False)
    pd.DataFrame(run_log).to_csv(RUN_LOG_PATH, index=False)

    summary = {
        "status_token": "V6_16_PILOT_BACKTEST_BUILD_COMPLETED",
        "run_id": run_id,
        "started_at": started.isoformat(timespec="seconds"),
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "cases": EXPECTED_CASES,
        "origins_per_case": PILOT_ORIGINS,
        "models": EXPECTED_MODELS,
        "horizons": HORIZON_DAYS,
        "rows": len(pilot),
        "legacy_rows_reused": len(output_frames[0]),
        "new_rows_generated": len(generated),
        "full_557_key_run_started": False,
        "tesseract_accessed": False,
    }
    RUN_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

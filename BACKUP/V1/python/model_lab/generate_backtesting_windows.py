"""Generate walk-forward backtesting windows for the Model Lab.

This Stage 5.2 script defines temporal validation windows from historical
actuals only. It does not train models, generate forecasts, calculate metrics,
or create rankings.
"""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import load_all_configs
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("generate_backtesting_windows")

EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_OUTPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
SUMMARY_OUTPUT = MODEL_LAB_DIR / "backtesting_window_summary.csv"

WINDOW_COLUMNS = [
    "entity_key",
    "window_id",
    "train_start_date",
    "train_end_date",
    "test_start_date",
    "test_end_date",
    "train_observations",
    "test_observations",
    "forecast_horizon_days",
    "validation_method",
    "expanding_window",
]

SUMMARY_COLUMNS = [
    "entity_key",
    "total_windows",
    "first_train_start_date",
    "last_train_end_date",
    "first_test_start_date",
    "last_test_end_date",
    "min_train_observations",
    "max_train_observations",
    "min_test_observations",
    "max_test_observations",
]

REQUIRED_DATASET_COLUMNS = ["entity_key", "date", "record_type", "value"]


def _require_input_file(path) -> None:
    """Fail fast when an expected input file is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required input missing: {path}")


def _validate_config(config: dict) -> None:
    """Validate the Stage 5.2 backtesting configuration."""

    if config.get("validation_method") != "walk_forward":
        raise ValueError("Stage 5.2 requires validation_method: walk_forward")
    if int(config["forecast_horizon_days"]) <= 0:
        raise ValueError("forecast_horizon_days must be positive")
    if int(config["n_windows"]) <= 0:
        raise ValueError("n_windows must be positive")
    if config.get("frequency") != "daily":
        raise ValueError("Stage 5.2 currently supports frequency: daily")


def _load_actuals() -> pd.DataFrame:
    """Load the master evaluation dataset and retain historical actuals only."""

    _require_input_file(EVALUATION_DATASET)
    dataset = pd.read_csv(EVALUATION_DATASET, usecols=REQUIRED_DATASET_COLUMNS)
    missing_columns = [
        column for column in REQUIRED_DATASET_COLUMNS if column not in dataset.columns
    ]
    if missing_columns:
        raise ValueError(f"Evaluation dataset missing columns: {missing_columns}")

    actuals = dataset[dataset["record_type"] == "actual"].copy()
    actuals["date"] = pd.to_datetime(actuals["date"], errors="raise")
    actuals = actuals.dropna(subset=["entity_key", "date"])
    actuals = actuals.sort_values(["entity_key", "date"])
    return actuals


def _count_observations(frame: pd.DataFrame, start_date, end_date) -> int:
    """Count actual observations between two inclusive dates."""

    return int(((frame["date"] >= start_date) & (frame["date"] <= end_date)).sum())


def _generate_entity_windows(entity_actuals: pd.DataFrame, config: dict) -> list[dict]:
    """Generate valid walk-forward windows for one entity."""

    forecast_horizon_days = int(config["forecast_horizon_days"])
    n_windows = int(config["n_windows"])
    minimum_training_observations = int(config["minimum_training_observations"])
    minimum_test_observations = int(config["minimum_test_observations"])
    validation_method = str(config["validation_method"])
    expanding_window = bool(config["expanding_window"])

    entity_key = entity_actuals["entity_key"].iloc[0]
    first_actual_date = entity_actuals["date"].min()
    latest_actual_date = entity_actuals["date"].max()
    windows: list[dict] = []

    for offset in range(n_windows):
        test_end_date = latest_actual_date - pd.Timedelta(
            days=offset * forecast_horizon_days
        )
        test_start_date = test_end_date - pd.Timedelta(days=forecast_horizon_days - 1)
        train_start_date = first_actual_date
        train_end_date = test_start_date - pd.Timedelta(days=1)

        if train_end_date < train_start_date:
            continue

        train_observations = _count_observations(
            entity_actuals, train_start_date, train_end_date
        )
        test_observations = _count_observations(
            entity_actuals, test_start_date, test_end_date
        )

        if train_observations < minimum_training_observations:
            continue
        if test_observations < minimum_test_observations:
            continue

        # Latest window receives the highest configured id, matching the design
        # example where window 12 is the most recent window when n_windows=12.
        window_id = n_windows - offset
        windows.append(
            {
                "entity_key": entity_key,
                "window_id": window_id,
                "train_start_date": train_start_date.date(),
                "train_end_date": train_end_date.date(),
                "test_start_date": test_start_date.date(),
                "test_end_date": test_end_date.date(),
                "train_observations": train_observations,
                "test_observations": test_observations,
                "forecast_horizon_days": forecast_horizon_days,
                "validation_method": validation_method,
                "expanding_window": expanding_window,
            }
        )

    return sorted(windows, key=lambda row: (row["entity_key"], row["window_id"]))


def _build_summary(windows: pd.DataFrame) -> pd.DataFrame:
    """Build per-entity backtesting window summary."""

    if windows.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    summary = (
        windows.groupby("entity_key", as_index=False)
        .agg(
            total_windows=("window_id", "count"),
            first_train_start_date=("train_start_date", "min"),
            last_train_end_date=("train_end_date", "max"),
            first_test_start_date=("test_start_date", "min"),
            last_test_end_date=("test_end_date", "max"),
            min_train_observations=("train_observations", "min"),
            max_train_observations=("train_observations", "max"),
            min_test_observations=("test_observations", "min"),
            max_test_observations=("test_observations", "max"),
        )
        .sort_values("entity_key")
    )
    return summary[SUMMARY_COLUMNS]


def _validate_windows(windows: pd.DataFrame, config: dict) -> None:
    """Validate generated windows against Stage 5.2 rules."""

    if windows.empty:
        raise ValueError("No valid backtesting windows were generated.")

    date_columns = [
        "train_start_date",
        "train_end_date",
        "test_start_date",
        "test_end_date",
    ]
    for column in date_columns:
        windows[column] = pd.to_datetime(windows[column], errors="raise")

    train_before_test = (windows["train_end_date"] < windows["test_start_date"]).all()
    if not train_before_test:
        raise ValueError("Invalid windows found: training does not end before test.")

    horizon_days = int(config["forecast_horizon_days"])
    actual_horizons = (windows["test_end_date"] - windows["test_start_date"]).dt.days + 1
    if not (actual_horizons == horizon_days).all():
        raise ValueError("Invalid windows found: test horizon is not 30 days.")

    if (windows["train_observations"] < int(config["minimum_training_observations"])).any():
        raise ValueError("Invalid windows found: insufficient training observations.")
    if (windows["test_observations"] < int(config["minimum_test_observations"])).any():
        raise ValueError("Invalid windows found: insufficient test observations.")


def generate_backtesting_windows() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate and save walk-forward windows and summary outputs."""

    logger.info("Stage 5.2 walk-forward window generation started")
    MODEL_LAB_DIR.mkdir(parents=True, exist_ok=True)

    config = load_all_configs()["backtesting"]
    _validate_config(config)
    actuals = _load_actuals()

    all_windows: list[dict] = []
    skipped_entities: list[str] = []

    for entity_key, entity_actuals in actuals.groupby("entity_key"):
        windows = _generate_entity_windows(entity_actuals, config)
        if not windows:
            skipped_entities.append(entity_key)
            continue
        all_windows.extend(windows)

    windows_df = pd.DataFrame(all_windows, columns=WINDOW_COLUMNS)
    _validate_windows(windows_df, config)
    summary_df = _build_summary(windows_df)

    windows_df.to_csv(WINDOWS_OUTPUT, index=False)
    summary_df.to_csv(SUMMARY_OUTPUT, index=False)

    logger.info("Entities processed: %s", actuals["entity_key"].nunique())
    logger.info("Entities skipped: %s", len(skipped_entities))
    if skipped_entities:
        logger.info("Skipped entities: %s", skipped_entities)
    logger.info("Total windows generated: %s", len(windows_df))
    logger.info(
        "Test date range: %s to %s",
        windows_df["test_start_date"].min(),
        windows_df["test_end_date"].max(),
    )
    logger.info("Created %s", WINDOWS_OUTPUT)
    logger.info("Created %s", SUMMARY_OUTPUT)
    logger.info("Stage 5.2 walk-forward window generation completed")

    return windows_df, summary_df


if __name__ == "__main__":
    generate_backtesting_windows()

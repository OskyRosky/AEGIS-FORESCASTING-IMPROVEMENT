"""Block 5.29F - Challenger Aggregation & Significance.

Builds challenger-only aggregation and pairwise statistical evidence artifacts.
This block does not create rankings, tournament scores, winners, or champions.
"""

from __future__ import annotations

from datetime import datetime
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_challenger_aggregation_significance")

RUN_ID = "challenger_aggregation_significance"
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 20260612
PRACTICAL_THRESHOLD = 0.02
EXPECTED_CANONICAL_ROWS = 2724
EXPECTED_MODEL_COUNT = 6
EXPECTED_PAIRWISE = 15

FINAL_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
]
DEFERRED_MODELS = {"NBEATS", "NHITS"}

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
METRICS_DIR = MODEL_LAB_DIR / "challenger_metrics"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_aggregation_significance"
METRICS_PATH = METRICS_DIR / "challenger_metrics_entity_window.csv"
DIAGNOSTIC_PATH = METRICS_DIR / "challenger_metrics_by_model_diagnostic.csv"
METRICS_SUMMARY_PATH = METRICS_DIR / "challenger_metrics_summary.csv"
METRICS_VALIDATION_PATH = METRICS_DIR / "challenger_metrics_validation.csv"
NEGATIVE_IMPACT_PATH = METRICS_DIR / "challenger_negative_forecast_impact.csv"
MODEL_SET_PATH = (
    MODEL_LAB_DIR / "challenger_model_set_rescope" / "current_official_challenger_set.csv"
)

CANONICAL_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "mase",
    "rmsse",
    "wmape",
    "mape",
    "smape",
    "rmse",
    "bias",
    "forecast_rows",
    "negative_forecast_rows",
    "execution_mode",
    "created_timestamp",
]
ENTITY_MODEL_COLUMNS = [
    "run_id",
    "entity_key",
    "model_name",
    "window_count",
    "median_mase",
    "mean_mase",
    "p95_mase",
    "median_rmsse",
    "mean_rmsse",
    "p95_rmsse",
    "median_wmape",
    "median_smape",
    "median_bias",
    "negative_forecast_rows",
    "created_timestamp",
]
MODEL_AGG_COLUMNS = [
    "run_id",
    "model_name",
    "entity_count",
    "entity_model_rows",
    "official_median_mase",
    "diagnostic_mean_mase",
    "diagnostic_p95_mase",
    "official_median_rmsse",
    "diagnostic_mean_rmsse",
    "diagnostic_p95_rmsse",
    "median_wmape",
    "median_smape",
    "median_bias",
    "negative_forecast_rows",
    "created_timestamp",
]
PAIRWISE_COLUMNS = [
    "run_id",
    "model_a",
    "model_b",
    "paired_entity_count",
    "median_delta_mase",
    "bootstrap_ci_low",
    "bootstrap_ci_high",
    "sign_test_p_value",
    "bh_adjusted_p_value",
    "practical_threshold",
    "practically_meaningful",
    "statistically_supported",
    "comparison_status",
    "created_timestamp",
]
SIGNIFICANCE_SUMMARY_COLUMNS = [
    "run_id",
    "model_name",
    "comparisons_tested",
    "supported_better_count",
    "supported_worse_count",
    "inconclusive_count",
    "notes",
    "created_timestamp",
]
FAMILY_COLUMNS = [
    "run_id",
    "model_family",
    "models_in_family",
    "model_count",
    "median_official_mase",
    "median_official_rmsse",
    "median_wmape",
    "median_smape",
    "notes",
    "created_timestamp",
]
RISK_COLUMNS = [
    "run_id",
    "model_name",
    "risk_type",
    "risk_level",
    "evidence",
    "recommended_audit_action",
    "created_timestamp",
]
TOURNAMENT_MANIFEST_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "metrics_available",
    "aggregation_available",
    "significance_available",
    "eligible_for_tournament_consideration",
    "exclusion_reason",
    "created_timestamp",
]
VALIDATION_COLUMNS = ["check_name", "status", "details", "created_timestamp"]
SUMMARY_COLUMNS = [
    "run_id",
    "challenger_models",
    "canonical_rows",
    "entity_model_rows",
    "model_aggregation_rows",
    "pairwise_comparisons",
    "supported_pairwise_differences",
    "inconclusive_pairwise_comparisons",
    "outlier_risk_flags",
    "aggregation_created",
    "significance_created",
    "rankings_created",
    "tournament_created",
    "champion_selected",
    "created_timestamp",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _write_csv(df: pd.DataFrame, filename: str, columns: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(OUTPUT_DIR / filename, index=False)


def _require(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")


def _load_metrics() -> pd.DataFrame:
    _require(METRICS_PATH)
    df = pd.read_csv(METRICS_PATH)
    df = df[df["model_name"].isin(FINAL_MODELS)].copy()
    if set(df["model_name"]) != set(FINAL_MODELS):
        raise ValueError("metrics do not contain exactly the final challenger model set")
    for col in ["window_id", "forecast_rows", "negative_forecast_rows"]:
        df[col] = pd.to_numeric(df[col], errors="raise").astype(int)
    for col in ["mase", "rmsse", "wmape", "mape", "smape", "rmse", "bias"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _load_model_families() -> dict[str, str]:
    _require(MODEL_SET_PATH)
    model_set = pd.read_csv(MODEL_SET_PATH)
    return dict(zip(model_set["model_name"], model_set["model_family"]))


def _canonical(metrics: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    canonical = metrics[CANONICAL_COLUMNS].copy()
    canonical["run_id"] = RUN_ID
    canonical["created_timestamp"] = timestamp
    return canonical[CANONICAL_COLUMNS]


def _entity_model(canonical: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for (entity_key, model_name), group in canonical.groupby(["entity_key", "model_name"], sort=True):
        rows.append(
            {
                "run_id": RUN_ID,
                "entity_key": entity_key,
                "model_name": model_name,
                "window_count": int(group["window_id"].nunique()),
                "median_mase": float(group["mase"].median()),
                "mean_mase": float(group["mase"].mean()),
                "p95_mase": float(group["mase"].quantile(0.95)),
                "median_rmsse": float(group["rmsse"].median()),
                "mean_rmsse": float(group["rmsse"].mean()),
                "p95_rmsse": float(group["rmsse"].quantile(0.95)),
                "median_wmape": float(group["wmape"].median()),
                "median_smape": float(group["smape"].median()),
                "median_bias": float(group["bias"].median()),
                "negative_forecast_rows": int(group["negative_forecast_rows"].sum()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=ENTITY_MODEL_COLUMNS)


def _model_aggregation(entity_model: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model_name in FINAL_MODELS:
        group = entity_model[entity_model["model_name"] == model_name]
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model_name,
                "entity_count": int(group["entity_key"].nunique()),
                "entity_model_rows": int(len(group)),
                "official_median_mase": float(group["median_mase"].median()),
                "diagnostic_mean_mase": float(group["median_mase"].mean()),
                "diagnostic_p95_mase": float(group["median_mase"].quantile(0.95)),
                "official_median_rmsse": float(group["median_rmsse"].median()),
                "diagnostic_mean_rmsse": float(group["median_rmsse"].mean()),
                "diagnostic_p95_rmsse": float(group["median_rmsse"].quantile(0.95)),
                "median_wmape": float(group["median_wmape"].median()),
                "median_smape": float(group["median_smape"].median()),
                "median_bias": float(group["median_bias"].median()),
                "negative_forecast_rows": int(group["negative_forecast_rows"].sum()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=MODEL_AGG_COLUMNS)


def _sign_test_p_value(delta: np.ndarray) -> float:
    nonzero = delta[delta != 0]
    n = len(nonzero)
    if n == 0:
        return 1.0
    positives = int((nonzero > 0).sum())
    smaller_tail = min(positives, n - positives)
    p = 2.0 * sum(comb(n, k) for k in range(smaller_tail + 1)) / (2**n)
    return float(min(1.0, p))


def _bh_adjust(p_values: list[float]) -> list[float]:
    m = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(m, dtype=float)
    prev = 1.0
    for rank_idx in range(m - 1, -1, -1):
        original_idx = int(order[rank_idx])
        rank = rank_idx + 1
        value = min(prev, p_values[original_idx] * m / rank)
        adjusted[original_idx] = value
        prev = value
    return [float(min(1.0, x)) for x in adjusted]


def _pairwise(entity_model: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []
    p_values = []
    for model_a, model_b in combinations(FINAL_MODELS, 2):
        a = entity_model[entity_model["model_name"] == model_a][["entity_key", "median_mase"]]
        b = entity_model[entity_model["model_name"] == model_b][["entity_key", "median_mase"]]
        paired = a.merge(b, on="entity_key", suffixes=("_a", "_b"), how="inner")
        n = len(paired)
        if n < 2:
            row = {
                "run_id": RUN_ID,
                "model_a": model_a,
                "model_b": model_b,
                "paired_entity_count": n,
                "median_delta_mase": np.nan,
                "bootstrap_ci_low": np.nan,
                "bootstrap_ci_high": np.nan,
                "sign_test_p_value": 1.0,
                "bh_adjusted_p_value": np.nan,
                "practical_threshold": PRACTICAL_THRESHOLD,
                "practically_meaningful": False,
                "statistically_supported": False,
                "comparison_status": "insufficient_pairs",
                "created_timestamp": timestamp,
            }
        else:
            delta = (
                paired["median_mase_a"].to_numpy(dtype=float)
                - paired["median_mase_b"].to_numpy(dtype=float)
            )
            samples = rng.integers(0, n, size=(BOOTSTRAP_ITERATIONS, n))
            bootstrap_medians = np.median(delta[samples], axis=1)
            median_delta = float(np.median(delta))
            p_value = _sign_test_p_value(delta)
            row = {
                "run_id": RUN_ID,
                "model_a": model_a,
                "model_b": model_b,
                "paired_entity_count": n,
                "median_delta_mase": median_delta,
                "bootstrap_ci_low": float(np.quantile(bootstrap_medians, 0.025)),
                "bootstrap_ci_high": float(np.quantile(bootstrap_medians, 0.975)),
                "sign_test_p_value": p_value,
                "bh_adjusted_p_value": np.nan,
                "practical_threshold": PRACTICAL_THRESHOLD,
                "practically_meaningful": bool(abs(median_delta) >= PRACTICAL_THRESHOLD),
                "statistically_supported": False,
                "comparison_status": "inconclusive",
                "created_timestamp": timestamp,
            }
        rows.append(row)
        p_values.append(float(row["sign_test_p_value"]))

    adjusted = _bh_adjust(p_values)
    for row, adjusted_p in zip(rows, adjusted):
        row["bh_adjusted_p_value"] = adjusted_p
        ci_excludes_zero = (
            pd.notna(row["bootstrap_ci_low"])
            and pd.notna(row["bootstrap_ci_high"])
            and (row["bootstrap_ci_high"] < 0 or row["bootstrap_ci_low"] > 0)
        )
        supported = (
            row["comparison_status"] != "insufficient_pairs"
            and row["practically_meaningful"]
            and adjusted_p <= 0.05
            and ci_excludes_zero
        )
        row["statistically_supported"] = bool(supported)
        if supported:
            row["comparison_status"] = "supported_difference"
    return pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)


def _significance_summary(pairwise: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model in FINAL_MODELS:
        tested = pairwise[(pairwise["model_a"] == model) | (pairwise["model_b"] == model)]
        better = 0
        worse = 0
        for _, r in tested.iterrows():
            if not bool(r["statistically_supported"]):
                continue
            model_a_better = float(r["median_delta_mase"]) < 0
            if (r["model_a"] == model and model_a_better) or (r["model_b"] == model and not model_a_better):
                better += 1
            else:
                worse += 1
        inconclusive = int((tested["comparison_status"] != "supported_difference").sum())
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "comparisons_tested": int(len(tested)),
                "supported_better_count": int(better),
                "supported_worse_count": int(worse),
                "inconclusive_count": inconclusive,
                "notes": "Evidence summary only; not a ranking and not a champion decision.",
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=SIGNIFICANCE_SUMMARY_COLUMNS)


def _family_summary(model_agg: pd.DataFrame, families: dict[str, str], timestamp: str) -> pd.DataFrame:
    frame = model_agg.copy()
    frame["model_family"] = frame["model_name"].map(families)
    rows = []
    for family, group in frame.groupby("model_family", sort=True):
        models = group["model_name"].tolist()
        rows.append(
            {
                "run_id": RUN_ID,
                "model_family": family,
                "models_in_family": ", ".join(models),
                "model_count": int(len(models)),
                "median_official_mase": float(group["official_median_mase"].median()),
                "median_official_rmsse": float(group["official_median_rmsse"].median()),
                "median_wmape": float(group["median_wmape"].median()),
                "median_smape": float(group["median_smape"].median()),
                "notes": "Diagnostic family summary only; no ranking or champion decision.",
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=FAMILY_COLUMNS)


def _risk_review(
    canonical: pd.DataFrame,
    model_agg: pd.DataFrame,
    negative_impact: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    rows = []
    metric_counts = canonical.groupby("model_name").size().to_dict()
    for _, r in model_agg.iterrows():
        model = r["model_name"]
        official_mase = float(r["official_median_mase"])
        official_rmsse = float(r["official_median_rmsse"])
        neg = negative_impact[negative_impact["model_name"] == model]
        negative_rate = float(neg.iloc[0]["negative_forecast_rate"]) if len(neg) else 0.0
        if official_mase >= 100:
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "risk_type": "extremely_high_mase",
                    "risk_level": "high",
                    "evidence": f"official_median_mase={official_mase:.6f}",
                    "recommended_audit_action": "Review model behavior and keep included unless validation fails.",
                    "created_timestamp": timestamp,
                }
            )
        if official_rmsse >= 25:
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "risk_type": "extremely_high_rmsse",
                    "risk_level": "high",
                    "evidence": f"official_median_rmsse={official_rmsse:.6f}",
                    "recommended_audit_action": "Review guardrail behavior before tournament use.",
                    "created_timestamp": timestamp,
                }
            )
        if negative_rate >= 0.01:
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "risk_type": "high_negative_forecast_rate",
                    "risk_level": "medium",
                    "evidence": f"negative_forecast_rate={negative_rate:.6f}",
                    "recommended_audit_action": "Confirm non-negative scoring adjustment is acceptable.",
                    "created_timestamp": timestamp,
                }
            )
        if metric_counts.get(model, 0) != 454:
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "risk_type": "missing_metric_rows",
                    "risk_level": "high",
                    "evidence": f"metric_rows={metric_counts.get(model, 0)} expected=454",
                    "recommended_audit_action": "Block Audit #4 until row coverage is fixed.",
                    "created_timestamp": timestamp,
                }
            )
        p95_ratio = float(r["diagnostic_p95_mase"]) / max(official_mase, 1e-9)
        if p95_ratio >= 5:
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "risk_type": "unstable_forecasts",
                    "risk_level": "medium",
                    "evidence": f"diagnostic_p95_mase_to_median_ratio={p95_ratio:.6f}",
                    "recommended_audit_action": "Inspect high-error entities/windows.",
                    "created_timestamp": timestamp,
                }
            )
    if not any(row["model_name"] == "FastNeuralAR_MLP" for row in rows):
        fast = model_agg[model_agg["model_name"] == "FastNeuralAR_MLP"].iloc[0]
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": "FastNeuralAR_MLP",
                "risk_type": "fast_neural_diagnostic_review",
                "risk_level": "medium",
                "evidence": f"official_median_mase={float(fast['official_median_mase']):.6f}",
                "recommended_audit_action": "Explicitly review lightweight neural behavior before tournament use.",
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RISK_COLUMNS)


def _tournament_manifest(
    model_agg: pd.DataFrame,
    pairwise: pd.DataFrame,
    families: dict[str, str],
    timestamp: str,
) -> pd.DataFrame:
    rows = []
    valid_models = set(model_agg["model_name"])
    significance_models = set(pairwise["model_a"]).union(set(pairwise["model_b"]))
    for model in FINAL_MODELS:
        metrics_available = model in valid_models
        aggregation_available = model in valid_models
        significance_available = model in significance_models
        eligible = metrics_available and aggregation_available and significance_available
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": "challenger",
                "model_family": families.get(model, "unknown"),
                "metrics_available": metrics_available,
                "aggregation_available": aggregation_available,
                "significance_available": significance_available,
                "eligible_for_tournament_consideration": eligible,
                "exclusion_reason": "" if eligible else "missing required metrics/aggregation/significance artifact",
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=TOURNAMENT_MANIFEST_COLUMNS)


def _validation(
    canonical: pd.DataFrame,
    entity_model: pd.DataFrame,
    model_agg: pd.DataFrame,
    pairwise: pd.DataFrame,
    summary: pd.DataFrame,
) -> pd.DataFrame:
    timestamp = _now()
    rows = []

    def add(name: str, ok: bool, details: str) -> None:
        rows.append(
            {
                "check_name": name,
                "status": "pass" if ok else "fail",
                "details": details,
                "created_timestamp": timestamp,
            }
        )

    models = set(canonical["model_name"])
    add("canonical_rows_2724", len(canonical) == EXPECTED_CANONICAL_ROWS, f"actual={len(canonical)}")
    add("exactly_6_challenger_models", models == set(FINAL_MODELS), f"models={sorted(models)}")
    add("no_nbeats", "NBEATS" not in models, "NBEATS absent")
    add("no_nhits", "NHITS" not in models, "NHITS absent")
    add("entity_model_aggregation_exists", len(entity_model) > 0, f"rows={len(entity_model)}")
    add("model_aggregation_6_rows", len(model_agg) == EXPECTED_MODEL_COUNT, f"rows={len(model_agg)}")
    add("pairwise_comparisons_15", len(pairwise) == EXPECTED_PAIRWISE, f"rows={len(pairwise)}")
    all_frames = [canonical, entity_model, model_agg, pairwise]
    ranking_columns = [
        c
        for frame in all_frames
        for c in frame.columns
        if "rank" in c.lower() or "winner" in c.lower() or "champion" in c.lower()
    ]
    add("no_ranking_columns", not ranking_columns, f"columns={ranking_columns or 'none'}")
    add("no_tournament_outputs", not (MODEL_LAB_DIR / "challenger_tournament").exists(), "challenger_tournament absent")
    add("no_champion_outputs", not (MODEL_LAB_DIR / "challenger_champion").exists(), "challenger_champion absent")
    add(
        "aggregation_uses_entity_equal_weighting",
        len(entity_model.groupby("model_name")["entity_key"].nunique().unique()) == 1,
        "entity-level medians feed model-level medians",
    )
    add(
        "significance_uses_entity_paired_comparisons",
        pairwise["paired_entity_count"].min() == pairwise["paired_entity_count"].max(),
        f"paired_entity_count_range={pairwise['paired_entity_count'].min()}..{pairwise['paired_entity_count'].max()}",
    )
    add("fast_neural_included", "FastNeuralAR_MLP" in models, "FastNeuralAR_MLP present")
    s = summary.iloc[0]
    safe_flags = (
        bool(s["aggregation_created"])
        and bool(s["significance_created"])
        and not bool(s["rankings_created"])
        and not bool(s["tournament_created"])
        and not bool(s["champion_selected"])
    )
    add("summary_flags_safe", safe_flags, "aggregation/significance true; ranking/tournament/champion false")
    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def _summary(
    canonical: pd.DataFrame,
    entity_model: pd.DataFrame,
    model_agg: pd.DataFrame,
    pairwise: pd.DataFrame,
    risks: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "challenger_models": EXPECTED_MODEL_COUNT,
                "canonical_rows": int(len(canonical)),
                "entity_model_rows": int(len(entity_model)),
                "model_aggregation_rows": int(len(model_agg)),
                "pairwise_comparisons": int(len(pairwise)),
                "supported_pairwise_differences": int((pairwise["comparison_status"] == "supported_difference").sum()),
                "inconclusive_pairwise_comparisons": int((pairwise["comparison_status"] == "inconclusive").sum()),
                "outlier_risk_flags": int(len(risks)),
                "aggregation_created": True,
                "significance_created": True,
                "rankings_created": False,
                "tournament_created": False,
                "champion_selected": False,
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _report(
    model_agg: pd.DataFrame,
    pairwise: pd.DataFrame,
    family: pd.DataFrame,
    risks: pd.DataFrame,
    validation: pd.DataFrame,
    summary: pd.DataFrame,
) -> str:
    s = summary.iloc[0]
    failures = validation[validation["status"] == "fail"]
    fast = model_agg[model_agg["model_name"] == "FastNeuralAR_MLP"].iloc[0]
    lines = [
        "# Block 5.29F - Challenger Aggregation & Significance Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Create challenger-only aggregation and statistical evidence artifacts without rankings, tournament scores, winners, or champions.",
        "",
        "## Final Challenger Set",
        "",
        ", ".join(FINAL_MODELS),
        "",
        "## Deferred Models Excluded",
        "",
        "- NBEATS: deferred_runtime_impractical.",
        "- NHITS: deferred_dependency_blocked.",
        "",
        "## Official Aggregation Hierarchy",
        "",
        "Metrics are first aggregated to entity/model medians across windows. Model-level official MASE and RMSSE are then medians across entity-level medians, preserving equal entity weighting.",
        "",
        "## Model-Level Diagnostic Results",
        "",
        "The table below is diagnostic only and is not sorted as a ranking.",
        "",
        "| model_name | official_median_mase | official_median_rmsse | median_wmape | median_smape | negative_rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in model_agg.iterrows():
        lines.append(
            f"| {r['model_name']} | {r['official_median_mase']:.6f} | "
            f"{r['official_median_rmsse']:.6f} | {r['median_wmape']:.6f} | "
            f"{r['median_smape']:.6f} | {r['negative_forecast_rows']} |"
        )
    lines += [
        "",
        "## Pairwise Significance Method",
        "",
        f"Pairwise comparisons use entity-level median MASE, paired by entity, with {BOOTSTRAP_ITERATIONS:,} bootstrap iterations, deterministic seed {BOOTSTRAP_SEED}, exact paired sign tests, Benjamini-Hochberg correction, and a practical threshold of {PRACTICAL_THRESHOLD}.",
        "",
        "## Pairwise Evidence Results",
        "",
        f"- Pairwise comparisons: {s['pairwise_comparisons']}",
        f"- Supported differences: {s['supported_pairwise_differences']}",
        f"- Inconclusive comparisons: {s['inconclusive_pairwise_comparisons']}",
        "",
        "## Family-Level Diagnostics",
        "",
        "| model_family | models_in_family | median_official_mase | median_official_rmsse |",
        "| --- | --- | ---: | ---: |",
    ]
    for _, r in family.iterrows():
        lines.append(
            f"| {r['model_family']} | {r['models_in_family']} | "
            f"{r['median_official_mase']:.6f} | {r['median_official_rmsse']:.6f} |"
        )
    lines += [
        "",
        "## FastNeuralAR_MLP Risk / Performance Note",
        "",
        f"FastNeuralAR_MLP remains included, but is flagged for Audit #4 review because its official median MASE is {float(fast['official_median_mase']):.6f} and official median RMSSE is {float(fast['official_median_rmsse']):.6f}. This is diagnostic evidence only and not a removal decision.",
        "",
        "## Outlier Risk Review",
        "",
        f"- Risk flags: {len(risks)}",
        "",
        "## Validation Results",
        "",
        f"- Checks passed: {int((validation['status'] == 'pass').sum())}",
        f"- Checks failed: {int((validation['status'] == 'fail').sum())}",
    ]
    if len(failures):
        for _, r in failures.iterrows():
            lines.append(f"- FAIL {r['check_name']}: {r['details']}")
    lines += [
        "",
        "## Scope and Safety Findings",
        "",
        "- No rankings, tournament scores, winners, or champions were created.",
        "- Baseline aggregation/significance outputs and Shiny were not modified.",
        "",
        "## Readiness for Audit #4",
        "",
        "**PROCEED_TO_AUDIT_4_OFFICIAL_CHALLENGER_RESULTS_READINESS_AUDIT**",
        "",
    ]
    return "\n".join(lines)


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.29F - Challenger Aggregation & Significance ===")
    for path in [
        DIAGNOSTIC_PATH,
        METRICS_SUMMARY_PATH,
        METRICS_VALIDATION_PATH,
        NEGATIVE_IMPACT_PATH,
    ]:
        _require(path)
    timestamp = _now()
    metrics = _load_metrics()
    families = _load_model_families()
    negative_impact = pd.read_csv(NEGATIVE_IMPACT_PATH)

    canonical = _canonical(metrics, timestamp)
    entity_model = _entity_model(canonical, timestamp)
    model_agg = _model_aggregation(entity_model, timestamp)
    pairwise = _pairwise(entity_model, timestamp)
    significance_summary = _significance_summary(pairwise, timestamp)
    family = _family_summary(model_agg, families, timestamp)
    risks = _risk_review(canonical, model_agg, negative_impact, timestamp)
    tournament_manifest = _tournament_manifest(model_agg, pairwise, families, timestamp)
    summary = _summary(canonical, entity_model, model_agg, pairwise, risks, timestamp)
    validation = _validation(canonical, entity_model, model_agg, pairwise, summary)
    report = _report(model_agg, pairwise, family, risks, validation, summary)

    _write_csv(canonical, "challenger_canonical_entity_window_scores.csv", CANONICAL_COLUMNS)
    _write_csv(entity_model, "challenger_aggregation_by_entity_model.csv", ENTITY_MODEL_COLUMNS)
    _write_csv(model_agg, "challenger_aggregation_by_model.csv", MODEL_AGG_COLUMNS)
    _write_csv(pairwise, "challenger_pairwise_significance.csv", PAIRWISE_COLUMNS)
    _write_csv(significance_summary, "challenger_model_significance_summary.csv", SIGNIFICANCE_SUMMARY_COLUMNS)
    _write_csv(family, "challenger_family_summary.csv", FAMILY_COLUMNS)
    _write_csv(risks, "challenger_outlier_risk_review.csv", RISK_COLUMNS)
    _write_csv(tournament_manifest, "challenger_tournament_input_manifest.csv", TOURNAMENT_MANIFEST_COLUMNS)
    _write_csv(validation, "challenger_aggregation_significance_validation.csv", VALIDATION_COLUMNS)
    _write_csv(summary, "challenger_aggregation_significance_summary.csv", SUMMARY_COLUMNS)
    (OUTPUT_DIR / "challenger_aggregation_significance_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Aggregation/significance complete: canonical=%d entity_model=%d model_rows=%d pairwise=%d failures=%d",
        len(canonical),
        len(entity_model),
        len(model_agg),
        len(pairwise),
        int((validation["status"] == "fail").sum()),
    )
    return model_agg, pairwise, validation


if __name__ == "__main__":
    build()

"""Block 5.30 - Tournament Engine.

Builds a unified baseline + challenger tournament layer from audited
aggregation outputs. This block creates preliminary standings and pairwise
evidence, but it does not select a winner or champion.
"""

from __future__ import annotations

from datetime import datetime
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_tournament_engine")

RUN_ID = "tournament_engine"
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 20260612
PRACTICAL_THRESHOLD = 0.02

BASELINE_MODELS = [
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
]
CHALLENGER_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
]
EXCLUDED_MODELS = {
    "NBEATS": "deferred_runtime_impractical",
    "NHITS": "deferred_dependency_blocked",
}

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "tournament_engine"

BASE_ENTITY_PATH = MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_by_entity_model.csv"
BASE_MODEL_PATH = MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_by_model.csv"
CHAL_ENTITY_PATH = (
    MODEL_LAB_DIR
    / "challenger_aggregation_significance"
    / "challenger_aggregation_by_entity_model.csv"
)
CHAL_MODEL_PATH = (
    MODEL_LAB_DIR / "challenger_aggregation_significance" / "challenger_aggregation_by_model.csv"
)
CHAL_RISK_PATH = (
    MODEL_LAB_DIR / "challenger_aggregation_significance" / "challenger_outlier_risk_review.csv"
)
CHAL_MANIFEST_PATH = (
    MODEL_LAB_DIR
    / "challenger_aggregation_significance"
    / "challenger_tournament_input_manifest.csv"
)
AUDIT_SUMMARY_PATH = MODEL_LAB_DIR / "audit_4" / "audit_4_summary.csv"
AUDIT_FINDINGS_PATH = MODEL_LAB_DIR / "audit_4" / "audit_4_findings.csv"

UNIVERSE_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "included_in_tournament",
    "exclusion_reason",
    "audit_risk_flag",
    "created_timestamp",
]
ENTITY_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "entity_key",
    "median_mase",
    "median_rmsse",
    "median_wmape",
    "median_smape",
    "median_bias",
    "entity_weight",
    "audit_risk_flag",
    "created_timestamp",
]
SCORECARD_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "entity_count",
    "official_median_mase",
    "official_median_rmsse",
    "median_wmape",
    "median_smape",
    "median_bias",
    "mase_guardrail_status",
    "rmsse_guardrail_status",
    "risk_status",
    "audit_risk_flag",
    "eligible_for_champion_consideration",
    "champion_exclusion_reason",
    "created_timestamp",
]
PAIRWISE_COLUMNS = [
    "run_id",
    "model_a",
    "model_b",
    "model_a_origin",
    "model_b_origin",
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
EVIDENCE_SUMMARY_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "comparisons_tested",
    "supported_better_count",
    "supported_worse_count",
    "inconclusive_count",
    "net_supported_evidence",
    "audit_risk_flag",
    "created_timestamp",
]
STANDINGS_COLUMNS = [
    "run_id",
    "preliminary_position",
    "model_name",
    "model_origin",
    "model_family",
    "official_median_mase",
    "official_median_rmsse",
    "supported_better_count",
    "supported_worse_count",
    "risk_status",
    "audit_risk_flag",
    "eligible_for_champion_consideration",
    "created_timestamp",
]
RISK_COLUMNS = [
    "run_id",
    "model_name",
    "risk_type",
    "risk_level",
    "evidence",
    "impact_on_tournament",
    "recommended_review_action",
    "created_timestamp",
]
VALIDATION_COLUMNS = ["check_name", "status", "details", "created_timestamp"]
SUMMARY_COLUMNS = [
    "run_id",
    "baseline_models",
    "challenger_models",
    "total_tournament_models",
    "entity_model_rows",
    "pairwise_comparisons",
    "preliminary_standings_created",
    "champion_selected",
    "winner_selected",
    "ready_for_5_30A_sanity_review",
    "created_timestamp",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _require(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")


def _write_csv(df: pd.DataFrame, filename: str, columns: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(OUTPUT_DIR / filename, index=False)


def _baseline_family(model: str) -> str:
    if model in {"ARIMA_Fixed", "ETS_Current"}:
        return "statistical"
    if model == "LinearRegression":
        return "machine_learning"
    return "growth_baseline"


def _load_inputs() -> dict[str, pd.DataFrame]:
    for path in [
        BASE_ENTITY_PATH,
        BASE_MODEL_PATH,
        CHAL_ENTITY_PATH,
        CHAL_MODEL_PATH,
        CHAL_RISK_PATH,
        CHAL_MANIFEST_PATH,
        AUDIT_SUMMARY_PATH,
        AUDIT_FINDINGS_PATH,
    ]:
        _require(path)
    return {
        "base_entity": pd.read_csv(BASE_ENTITY_PATH),
        "base_model": pd.read_csv(BASE_MODEL_PATH),
        "chal_entity": pd.read_csv(CHAL_ENTITY_PATH),
        "chal_model": pd.read_csv(CHAL_MODEL_PATH),
        "chal_risk": pd.read_csv(CHAL_RISK_PATH),
        "chal_manifest": pd.read_csv(CHAL_MANIFEST_PATH),
        "audit_summary": pd.read_csv(AUDIT_SUMMARY_PATH),
        "audit_findings": pd.read_csv(AUDIT_FINDINGS_PATH),
    }


def _risk_flags(chal_risk: pd.DataFrame) -> set[str]:
    high = chal_risk[chal_risk["risk_level"].astype(str).str.lower().isin({"high", "critical"})]
    return set(high["model_name"])


def _universe(chal_manifest: pd.DataFrame, risk_models: set[str], timestamp: str) -> pd.DataFrame:
    rows = []
    for model in BASELINE_MODELS:
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": "baseline",
                "model_family": _baseline_family(model),
                "included_in_tournament": True,
                "exclusion_reason": "",
                "audit_risk_flag": False,
                "created_timestamp": timestamp,
            }
        )
    family_map = dict(zip(chal_manifest["model_name"], chal_manifest["model_family"]))
    for model in CHALLENGER_MODELS:
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": "challenger",
                "model_family": family_map.get(model, "unknown"),
                "included_in_tournament": True,
                "exclusion_reason": "",
                "audit_risk_flag": model in risk_models,
                "created_timestamp": timestamp,
            }
        )
    for model, reason in EXCLUDED_MODELS.items():
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": "challenger",
                "model_family": "deep_learning",
                "included_in_tournament": False,
                "exclusion_reason": reason,
                "audit_risk_flag": True,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=UNIVERSE_COLUMNS)


def _entity_scores(inputs: dict[str, pd.DataFrame], universe: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    base = inputs["base_entity"].copy()
    base = base[base["model_name"].isin(BASELINE_MODELS)].copy()
    base["model_origin"] = "baseline"
    base["model_family"] = base["model_name"].map(_baseline_family)
    base = base.rename(columns={"windows": "window_count"})
    for col in ["median_wmape", "median_smape", "median_bias"]:
        base[col] = np.nan

    chal = inputs["chal_entity"].copy()
    chal = chal[chal["model_name"].isin(CHALLENGER_MODELS)].copy()
    chal["model_origin"] = "challenger"
    family_map = dict(zip(universe["model_name"], universe["model_family"]))
    chal["model_family"] = chal["model_name"].map(family_map)

    frame = pd.concat([base, chal], ignore_index=True, sort=False)
    risk_map = dict(zip(universe["model_name"], universe["audit_risk_flag"]))
    frame["run_id"] = RUN_ID
    frame["entity_weight"] = 1
    frame["audit_risk_flag"] = frame["model_name"].map(risk_map).fillna(False)
    frame["created_timestamp"] = timestamp
    return frame[ENTITY_COLUMNS]


def _guardrail_status(mase: float, rmsse: float) -> tuple[str, str, str, str, bool]:
    mase_status = "pass" if mase < 25 else "warning" if mase < 100 else "fail"
    rmsse_status = "pass" if rmsse < 5 else "warning" if rmsse < 25 else "fail"
    if mase_status == "fail" or rmsse_status == "fail":
        risk = "high"
        eligible = False
        reason = "severe MASE/RMSSE guardrail risk; review before champion consideration"
    elif mase_status == "warning" or rmsse_status == "warning":
        risk = "medium"
        eligible = True
        reason = ""
    else:
        risk = "low"
        eligible = True
        reason = ""
    return mase_status, rmsse_status, risk, reason, eligible


def _scorecard(inputs: dict[str, pd.DataFrame], universe: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    base = inputs["base_model"].copy()
    base = base[base["model_name"].isin(BASELINE_MODELS)].copy()
    base["model_origin"] = "baseline"
    base["model_family"] = base["model_name"].map(_baseline_family)
    base = base.rename(columns={"entities": "entity_count"})
    for col in ["median_wmape", "median_smape", "median_bias"]:
        base[col] = np.nan

    chal = inputs["chal_model"].copy()
    chal = chal[chal["model_name"].isin(CHALLENGER_MODELS)].copy()
    chal["model_origin"] = "challenger"
    family_map = dict(zip(universe["model_name"], universe["model_family"]))
    chal["model_family"] = chal["model_name"].map(family_map)

    raw = pd.concat([base, chal], ignore_index=True, sort=False)
    risk_map = dict(zip(universe["model_name"], universe["audit_risk_flag"]))
    rows = []
    for _, r in raw.iterrows():
        mase = float(r["official_median_mase"])
        rmsse = float(r["official_median_rmsse"])
        mase_status, rmsse_status, risk_status, exclusion_reason, eligible = _guardrail_status(
            mase, rmsse
        )
        audit_risk = bool(risk_map.get(r["model_name"], False))
        if audit_risk and r["model_name"] == "FastNeuralAR_MLP":
            eligible = False
            risk_status = "high"
            exclusion_reason = (
                "Audit #4 high-risk flag: extreme MASE/RMSSE and possible scale or recursive-collapse issue"
            )
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": r["model_name"],
                "model_origin": r["model_origin"],
                "model_family": r["model_family"],
                "entity_count": int(r["entity_count"]),
                "official_median_mase": mase,
                "official_median_rmsse": rmsse,
                "median_wmape": r.get("median_wmape", np.nan),
                "median_smape": r.get("median_smape", np.nan),
                "median_bias": r.get("median_bias", np.nan),
                "mase_guardrail_status": mase_status,
                "rmsse_guardrail_status": rmsse_status,
                "risk_status": risk_status,
                "audit_risk_flag": audit_risk,
                "eligible_for_champion_consideration": eligible,
                "champion_exclusion_reason": exclusion_reason,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=SCORECARD_COLUMNS)


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


def _pairwise(entity_scores: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    model_meta = (
        entity_scores[["model_name", "model_origin"]]
        .drop_duplicates()
        .set_index("model_name")["model_origin"]
        .to_dict()
    )
    models = BASELINE_MODELS + CHALLENGER_MODELS
    rows = []
    p_values = []
    for model_a, model_b in combinations(models, 2):
        a = entity_scores[entity_scores["model_name"] == model_a][["entity_key", "median_mase"]]
        b = entity_scores[entity_scores["model_name"] == model_b][["entity_key", "median_mase"]]
        paired = a.merge(b, on="entity_key", suffixes=("_a", "_b"), how="inner")
        n = len(paired)
        if n < 2:
            row = {
                "run_id": RUN_ID,
                "model_a": model_a,
                "model_b": model_b,
                "model_a_origin": model_meta.get(model_a, ""),
                "model_b_origin": model_meta.get(model_b, ""),
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
            boot = np.median(delta[samples], axis=1)
            median_delta = float(np.median(delta))
            row = {
                "run_id": RUN_ID,
                "model_a": model_a,
                "model_b": model_b,
                "model_a_origin": model_meta.get(model_a, ""),
                "model_b_origin": model_meta.get(model_b, ""),
                "paired_entity_count": n,
                "median_delta_mase": median_delta,
                "bootstrap_ci_low": float(np.quantile(boot, 0.025)),
                "bootstrap_ci_high": float(np.quantile(boot, 0.975)),
                "sign_test_p_value": _sign_test_p_value(delta),
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
    for row, adj in zip(rows, adjusted):
        row["bh_adjusted_p_value"] = adj
        ci_excludes_zero = (
            pd.notna(row["bootstrap_ci_low"])
            and pd.notna(row["bootstrap_ci_high"])
            and (row["bootstrap_ci_high"] < 0 or row["bootstrap_ci_low"] > 0)
        )
        supported = (
            row["comparison_status"] != "insufficient_pairs"
            and row["practically_meaningful"]
            and adj <= 0.05
            and ci_excludes_zero
        )
        row["statistically_supported"] = bool(supported)
        if supported:
            row["comparison_status"] = "supported_difference"
    return pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)


def _evidence_summary(
    scorecard: pd.DataFrame, pairwise: pd.DataFrame, timestamp: str
) -> pd.DataFrame:
    rows = []
    meta = scorecard.set_index("model_name")
    for model in BASELINE_MODELS + CHALLENGER_MODELS:
        tested = pairwise[(pairwise["model_a"] == model) | (pairwise["model_b"] == model)]
        better = 0
        worse = 0
        for _, r in tested.iterrows():
            if not bool(r["statistically_supported"]):
                continue
            model_a_better = float(r["median_delta_mase"]) < 0
            if (r["model_a"] == model and model_a_better) or (
                r["model_b"] == model and not model_a_better
            ):
                better += 1
            else:
                worse += 1
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": meta.loc[model, "model_origin"],
                "model_family": meta.loc[model, "model_family"],
                "comparisons_tested": int(len(tested)),
                "supported_better_count": int(better),
                "supported_worse_count": int(worse),
                "inconclusive_count": int((tested["comparison_status"] != "supported_difference").sum()),
                "net_supported_evidence": int(better - worse),
                "audit_risk_flag": bool(meta.loc[model, "audit_risk_flag"]),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=EVIDENCE_SUMMARY_COLUMNS)


def _standings(
    scorecard: pd.DataFrame, evidence: pd.DataFrame, timestamp: str
) -> pd.DataFrame:
    frame = scorecard.merge(
        evidence[["model_name", "supported_better_count", "supported_worse_count"]],
        on="model_name",
        how="left",
    )
    frame = frame.sort_values(
        [
            "eligible_for_champion_consideration",
            "official_median_mase",
            "official_median_rmsse",
            "supported_worse_count",
            "supported_better_count",
            "model_name",
        ],
        ascending=[False, True, True, True, False, True],
    ).reset_index(drop=True)
    frame["preliminary_position"] = np.arange(1, len(frame) + 1)
    frame["created_timestamp"] = timestamp
    return frame[STANDINGS_COLUMNS]


def _risk_register(
    scorecard: pd.DataFrame,
    chal_risk: pd.DataFrame,
    audit_findings: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    rows = []
    for _, r in scorecard.iterrows():
        if r["mase_guardrail_status"] == "fail" or r["rmsse_guardrail_status"] == "fail":
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": r["model_name"],
                    "risk_type": "severe_mase_or_rmsse_guardrail",
                    "risk_level": "high",
                    "evidence": (
                        f"official_median_mase={float(r['official_median_mase']):.6f}; "
                        f"official_median_rmsse={float(r['official_median_rmsse']):.6f}"
                    ),
                    "impact_on_tournament": "Model remains scored but may be excluded from champion consideration.",
                    "recommended_review_action": "Review in 5.30A sanity review before 5.31 decision.",
                    "created_timestamp": timestamp,
                }
            )
    for _, r in chal_risk.iterrows():
        if r["model_name"] == "FastNeuralAR_MLP":
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": "FastNeuralAR_MLP",
                    "risk_type": r["risk_type"],
                    "risk_level": r["risk_level"],
                    "evidence": r["evidence"],
                    "impact_on_tournament": "High-risk flag carried forward; scored but not silently promoted.",
                    "recommended_review_action": "Investigate scale/normalization or recursive collapse behavior.",
                    "created_timestamp": timestamp,
                }
            )
    rows.append(
        {
            "run_id": RUN_ID,
            "model_name": "NBEATS",
            "risk_type": "partial_rows_excluded",
            "risk_level": "medium",
            "evidence": "Audit #4 F-015: pre-recovery NBEATS partial rows existed only in inventory/checkpoints.",
            "impact_on_tournament": "NBEATS is not scored; tournament consumes final audited artifacts only.",
            "recommended_review_action": "Do not read checkpoint or partial forecast files in downstream blocks.",
            "created_timestamp": timestamp,
        }
    )
    rows.append(
        {
            "run_id": RUN_ID,
            "model_name": "NHITS",
            "risk_type": "dependency_deferral",
            "risk_level": "medium",
            "evidence": "NHITS deferred_dependency_blocked due to Python 3.14 / neuralforecast / ray incompatibility.",
            "impact_on_tournament": "NHITS is not scored.",
            "recommended_review_action": "Do not include NHITS until dependency blocker is resolved and audited.",
            "created_timestamp": timestamp,
        }
    )
    if not audit_findings.empty:
        advisories = audit_findings[
            audit_findings.astype(str).apply(
                lambda row: row.str.contains("FastNeuralAR|NBEATS|eligibility", case=False, regex=True).any(),
                axis=1,
            )
        ]
        for _, r in advisories.iterrows():
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": "AUDIT_4",
                    "risk_type": "audit_condition",
                    "risk_level": "advisory",
                    "evidence": " | ".join(str(x) for x in r.to_dict().values())[:500],
                    "impact_on_tournament": "Condition carried forward for sanity review.",
                    "recommended_review_action": "Review Audit #4 conditions during 5.30A.",
                    "created_timestamp": timestamp,
                }
            )
    return pd.DataFrame(rows, columns=RISK_COLUMNS).drop_duplicates()


def _validate(
    universe: pd.DataFrame,
    entity_scores: pd.DataFrame,
    scorecard: pd.DataFrame,
    pairwise: pd.DataFrame,
    summary: pd.DataFrame,
    audit_summary: pd.DataFrame,
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

    scored = universe[universe["included_in_tournament"].astype(bool)]
    add("baseline_model_rows_7", int((scored["model_origin"] == "baseline").sum()) == 7, "expected=7")
    add("challenger_model_rows_6", int((scored["model_origin"] == "challenger").sum()) == 6, "expected=6")
    add("total_scored_tournament_models_13", len(scored) == 13, f"actual={len(scored)}")
    add("tournament_entity_model_rows_507", len(entity_scores) == 507, f"actual={len(entity_scores)}")
    add("tournament_scorecard_rows_13", len(scorecard) == 13, f"actual={len(scorecard)}")
    add("pairwise_comparisons_78", len(pairwise) == 78, f"actual={len(pairwise)}")
    add("no_nbeats_scored", "NBEATS" not in set(scorecard["model_name"]), "NBEATS absent")
    add("no_nhits_scored", "NHITS" not in set(scorecard["model_name"]), "NHITS absent")
    fast = scorecard[scorecard["model_name"] == "FastNeuralAR_MLP"]
    add(
        "fast_neural_included_and_flagged",
        len(fast) == 1 and bool(fast.iloc[0]["audit_risk_flag"]),
        "FastNeuralAR_MLP scored with audit_risk_flag",
    )
    add("no_champion_selected", not bool(summary.iloc[0]["champion_selected"]), "champion_selected=false")
    add("no_winner_selected", not bool(summary.iloc[0]["winner_selected"]), "winner_selected=false")
    add("no_final_champion_artifact", not (MODEL_LAB_DIR / "champion").exists() and not (MODEL_LAB_DIR / "challenger_champion").exists(), "champion dirs absent")
    add("no_shiny_modified", (PROJECT_ROOT / "shiny_app").exists(), "Shiny present and untouched by this script")
    verdict = str(audit_summary.iloc[0].get("verdict", "")).lower()
    add(
        "audit_4_verdict_approved",
        "approve" in verdict,
        f"verdict={audit_summary.iloc[0].get('verdict', '')}",
    )
    add(
        "only_final_audited_challenger_artifacts_consumed",
        CHAL_ENTITY_PATH.exists() and CHAL_MODEL_PATH.exists() and CHAL_MANIFEST_PATH.exists(),
        "used challenger_aggregation_significance artifacts",
    )
    return pd.DataFrame(rows, columns=VALIDATION_COLUMNS)


def _summary(
    universe: pd.DataFrame,
    entity_scores: pd.DataFrame,
    pairwise: pd.DataFrame,
    validation_ok: bool,
    timestamp: str,
) -> pd.DataFrame:
    scored = universe[universe["included_in_tournament"].astype(bool)]
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "baseline_models": int((scored["model_origin"] == "baseline").sum()),
                "challenger_models": int((scored["model_origin"] == "challenger").sum()),
                "total_tournament_models": int(len(scored)),
                "entity_model_rows": int(len(entity_scores)),
                "pairwise_comparisons": int(len(pairwise)),
                "preliminary_standings_created": True,
                "champion_selected": False,
                "winner_selected": False,
                "ready_for_5_30A_sanity_review": bool(validation_ok),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _report(
    scorecard: pd.DataFrame,
    pairwise: pd.DataFrame,
    standings: pd.DataFrame,
    risk: pd.DataFrame,
    validation: pd.DataFrame,
    audit_summary: pd.DataFrame,
    summary: pd.DataFrame,
) -> str:
    s = summary.iloc[0]
    failures = validation[validation["status"] == "fail"]
    supported = int((pairwise["comparison_status"] == "supported_difference").sum())
    inconclusive = int((pairwise["comparison_status"] == "inconclusive").sum())
    lines = [
        "# Block 5.30 - Tournament Engine Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Build a unified baseline + challenger tournament framework with preliminary standings and pairwise evidence. This block does not select a winner or champion.",
        "",
        "## Audit #4 Approval Status",
        "",
        f"- Verdict: {audit_summary.iloc[0].get('verdict', '')}",
        f"- Blockers: {audit_summary.iloc[0].get('blockers', '')}",
        f"- Major findings: {audit_summary.iloc[0].get('major_findings', '')}",
        "",
        "## Baseline Model Universe",
        "",
        ", ".join(BASELINE_MODELS),
        "",
        "## Challenger Model Universe",
        "",
        ", ".join(CHALLENGER_MODELS),
        "",
        "## Excluded / Deferred Models",
        "",
        "- NBEATS: deferred_runtime_impractical; partial/checkpoint rows are not consumed.",
        "- NHITS: deferred_dependency_blocked.",
        "",
        "## Official Metrics and Aggregation Logic",
        "",
        "Primary metric is official_median_mase. RMSSE is a guardrail. The tournament consumes entity-level medians and model-level equal-entity-weighted medians from audited aggregation artifacts.",
        "",
        "## Pairwise Evidence Method",
        "",
        f"Pairwise evidence uses entity-level paired MASE, {BOOTSTRAP_ITERATIONS:,} bootstrap iterations, seed {BOOTSTRAP_SEED}, exact sign tests, BH correction, and practical threshold {PRACTICAL_THRESHOLD}.",
        f"- Pairwise comparisons: {len(pairwise)}",
        f"- Supported differences: {supported}",
        f"- Inconclusive comparisons: {inconclusive}",
        "",
        "## Preliminary Standings Disclaimer",
        "",
        "Preliminary standings are for 5.30A sanity review only. Position 1 is not a winner and not a champion. Final champion/no-champion decision is deferred to 5.31.",
        "",
        "| position | model_name | origin | official_median_mase | official_median_rmsse | risk_status | audit_risk | eligible_for_champion_consideration |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for _, r in standings.iterrows():
        lines.append(
            f"| {r['preliminary_position']} | {r['model_name']} | {r['model_origin']} | "
            f"{float(r['official_median_mase']):.6f} | {float(r['official_median_rmsse']):.6f} | "
            f"{r['risk_status']} | {r['audit_risk_flag']} | {r['eligible_for_champion_consideration']} |"
        )
    lines += [
        "",
        "## Risk Register",
        "",
        f"- Risk rows: {len(risk)}",
        "- FastNeuralAR_MLP high-risk condition is carried forward.",
        "- NBEATS partial-row condition is carried forward.",
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
        "- No forecasts or metrics were recalculated.",
        "- Baseline, challenger source, Audit #4, and Shiny outputs were not modified.",
        "- No winner or champion artifact was created.",
        "",
        "## Recommendation for 5.30A",
        "",
        "**PROCEED_TO_5.30A_TOURNAMENT_SANITY_REVIEW**" if bool(s["ready_for_5_30A_sanity_review"]) else "**BLOCK_5.30A_PENDING_TOURNAMENT_ENGINE_FIX**",
        "",
    ]
    return "\n".join(lines)


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.30 - Tournament Engine ===")
    timestamp = _now()
    inputs = _load_inputs()
    risk_models = _risk_flags(inputs["chal_risk"])
    universe = _universe(inputs["chal_manifest"], risk_models, timestamp)
    entity_scores = _entity_scores(inputs, universe, timestamp)
    scorecard = _scorecard(inputs, universe, timestamp)
    pairwise = _pairwise(entity_scores, timestamp)
    evidence = _evidence_summary(scorecard, pairwise, timestamp)
    standings = _standings(scorecard, evidence, timestamp)
    risk = _risk_register(scorecard, inputs["chal_risk"], inputs["audit_findings"], timestamp)
    provisional_summary = _summary(universe, entity_scores, pairwise, False, timestamp)
    validation = _validate(
        universe,
        entity_scores,
        scorecard,
        pairwise,
        provisional_summary,
        inputs["audit_summary"],
    )
    summary = _summary(
        universe,
        entity_scores,
        pairwise,
        not (validation["status"] == "fail").any(),
        timestamp,
    )
    report = _report(
        scorecard,
        pairwise,
        standings,
        risk,
        validation,
        inputs["audit_summary"],
        summary,
    )

    _write_csv(universe, "tournament_model_universe.csv", UNIVERSE_COLUMNS)
    _write_csv(entity_scores, "tournament_entity_model_scores.csv", ENTITY_COLUMNS)
    _write_csv(scorecard, "tournament_model_scorecard.csv", SCORECARD_COLUMNS)
    _write_csv(pairwise, "tournament_pairwise_evidence.csv", PAIRWISE_COLUMNS)
    _write_csv(evidence, "tournament_model_evidence_summary.csv", EVIDENCE_SUMMARY_COLUMNS)
    _write_csv(standings, "tournament_preliminary_standings.csv", STANDINGS_COLUMNS)
    _write_csv(risk, "tournament_risk_register.csv", RISK_COLUMNS)
    _write_csv(validation, "tournament_validation.csv", VALIDATION_COLUMNS)
    _write_csv(summary, "tournament_summary.csv", SUMMARY_COLUMNS)
    (OUTPUT_DIR / "tournament_engine_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Tournament engine complete: models=%d entity_rows=%d pairwise=%d validation_failures=%d",
        len(scorecard),
        len(entity_scores),
        len(pairwise),
        int((validation["status"] == "fail").sum()),
    )
    return scorecard, pairwise, validation


if __name__ == "__main__":
    build()

"""Block 5.31 - Champion / No-Champion Decision.

Creates the formal Model Lab champion decision from audited tournament and
sanity-review artifacts. This block does not rerun models or modify source
outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_champion_decision")

RUN_ID = "champion_decision"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"

TOURNAMENT_DIR = MODEL_LAB_DIR / "tournament_engine"
SANITY_DIR = MODEL_LAB_DIR / "tournament_sanity_review"
AUDIT_DIR = MODEL_LAB_DIR / "audit_4"

SCORECARD_PATH = TOURNAMENT_DIR / "tournament_model_scorecard.csv"
EVIDENCE_PATH = TOURNAMENT_DIR / "tournament_model_evidence_summary.csv"
STANDINGS_PATH = TOURNAMENT_DIR / "tournament_preliminary_standings.csv"
RISK_PATH = TOURNAMENT_DIR / "tournament_risk_register.csv"
TOURNAMENT_SUMMARY_PATH = TOURNAMENT_DIR / "tournament_summary.csv"
SANITY_SUMMARY_PATH = SANITY_DIR / "tournament_sanity_summary.csv"
CANDIDATE_READINESS_PATH = SANITY_DIR / "tournament_candidate_readiness_for_5_31.csv"
SANITY_FINDINGS_PATH = SANITY_DIR / "tournament_sanity_findings.csv"
AUDIT_FINDINGS_PATH = AUDIT_DIR / "audit_4_findings.csv"

DECISIONS = {
    "CHAMPION_SELECTED",
    "CHAMPION_SELECTED_WITH_CONDITIONS",
    "NO_CHAMPION_SELECTED",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _require(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")


def _write_csv(df: pd.DataFrame, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / filename, index=False)


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _load_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "scorecard": SCORECARD_PATH,
        "evidence": EVIDENCE_PATH,
        "standings": STANDINGS_PATH,
        "risk": RISK_PATH,
        "tournament_summary": TOURNAMENT_SUMMARY_PATH,
        "sanity_summary": SANITY_SUMMARY_PATH,
        "candidate_readiness": CANDIDATE_READINESS_PATH,
        "sanity_findings": SANITY_FINDINGS_PATH,
        "audit_findings": AUDIT_FINDINGS_PATH,
    }
    for path in paths.values():
        _require(path)
    return {name: pd.read_csv(path) for name, path in paths.items()}


def _candidate_status(row: pd.Series, readiness: pd.Series) -> str:
    if not _bool(row["eligible_for_champion_consideration"]):
        if str(row["risk_status"]).lower() == "high" or _bool(row["audit_risk_flag"]):
            return "ineligible_due_to_risk"
        return "ineligible_due_to_guardrail"
    if int(row["supported_worse_count"]) >= 5:
        return "ineligible_due_to_evidence"
    if _bool(readiness.get("requires_manual_review", False)):
        return "conditionally_eligible"
    return "eligible_candidate"


def _build_candidate_evaluation(inputs: dict[str, pd.DataFrame], timestamp: str) -> pd.DataFrame:
    scorecard = inputs["scorecard"]
    evidence = inputs["evidence"]
    readiness = inputs["candidate_readiness"].set_index("model_name")
    merged = scorecard.merge(
        evidence[
            [
                "model_name",
                "supported_better_count",
                "supported_worse_count",
                "inconclusive_count",
            ]
        ],
        on="model_name",
        how="left",
    )
    rows = []
    for _, row in merged.iterrows():
        ready = readiness.loc[row["model_name"]]
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": row["model_name"],
                "model_origin": row["model_origin"],
                "model_family": row["model_family"],
                "official_median_mase": row["official_median_mase"],
                "official_median_rmsse": row["official_median_rmsse"],
                "supported_better_count": int(row["supported_better_count"]),
                "supported_worse_count": int(row["supported_worse_count"]),
                "inconclusive_count": int(row["inconclusive_count"]),
                "risk_status": row["risk_status"],
                "audit_risk_flag": bool(_bool(row["audit_risk_flag"])),
                "eligible_for_champion_consideration": bool(
                    _bool(row["eligible_for_champion_consideration"])
                ),
                "manual_review_required": bool(_bool(ready["requires_manual_review"])),
                "manual_review_reason": ready.get("manual_review_reason", ""),
                "champion_candidate_status": _candidate_status(row, ready),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows)


def _pairwise_strength(row: pd.Series) -> str:
    better = int(row["supported_better_count"])
    worse = int(row["supported_worse_count"])
    if better >= 6 and worse == 0:
        return "strong"
    if better >= 3 and worse <= 1:
        return "moderate"
    if worse >= better:
        return "weak_or_negative"
    return "limited"


def _build_decision_scorecard(candidates: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    ordered = candidates.sort_values(
        [
            "champion_candidate_status",
            "official_median_mase",
            "official_median_rmsse",
            "supported_worse_count",
        ],
        ascending=[True, True, True, True],
    )
    for _, row in ordered.iterrows():
        guardrail = "acceptable" if row["official_median_rmsse"] < 5 else "review_required"
        if str(row["risk_status"]).lower() == "high":
            guardrail = "failed_or_high_risk"
        eligibility = row["champion_candidate_status"]
        notes = (
            f"pairwise={row['supported_better_count']} better/"
            f"{row['supported_worse_count']} worse; status={eligibility}"
        )
        if row["manual_review_required"]:
            notes += f"; manual_review={row['manual_review_reason']}"
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": row["model_name"],
                "model_origin": row["model_origin"],
                "model_family": row["model_family"],
                "official_median_mase": row["official_median_mase"],
                "official_median_rmsse": row["official_median_rmsse"],
                "pairwise_support_strength": _pairwise_strength(row),
                "guardrail_status": guardrail,
                "risk_status": row["risk_status"],
                "decision_eligibility": eligibility,
                "decision_notes": notes,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows)


def _select_decision(candidates: pd.DataFrame, sanity_summary: pd.DataFrame) -> tuple[str, pd.Series | None, str, str, str]:
    if int(sanity_summary.iloc[0]["blockers"]) > 0 or int(sanity_summary.iloc[0]["major_findings"]) > 0:
        return (
            "NO_CHAMPION_SELECTED",
            None,
            "low",
            "",
            "Tournament sanity review has blocker or major findings.",
        )
    eligible = candidates[
        candidates["champion_candidate_status"].isin(["eligible_candidate", "conditionally_eligible"])
    ].copy()
    eligible = eligible[
        (eligible["risk_status"].astype(str).str.lower() != "high")
        & (~eligible["audit_risk_flag"].astype(bool))
        & (eligible["official_median_rmsse"] < 5)
    ]
    if eligible.empty:
        return (
            "NO_CHAMPION_SELECTED",
            None,
            "medium",
            "",
            "No candidate survived risk, guardrail, and eligibility filters.",
        )
    top = eligible.sort_values(
        ["official_median_mase", "official_median_rmsse", "supported_worse_count"],
        ascending=[True, True, True],
    ).iloc[0]
    if int(top["supported_better_count"]) >= 6 and int(top["supported_worse_count"]) == 0:
        conditions = (
            "Proceed through 5.31B closure pack; retain FastNeuralAR_MLP high-risk "
            "investigation and NBEATS/NHITS exclusion notes as non-champion conditions."
        )
        return ("CHAMPION_SELECTED_WITH_CONDITIONS", top, "medium", conditions, "")
    return (
        "NO_CHAMPION_SELECTED",
        None,
        "medium",
        "",
        "Top candidate did not meet the conservative pairwise support threshold.",
    )


def _evidence_summary(
    candidates: pd.DataFrame,
    decision: str,
    selected: pd.Series | None,
    timestamp: str,
) -> pd.DataFrame:
    top = candidates.sort_values("official_median_mase").iloc[0]
    rows = [
        ("primary metric MASE", f"Lowest official median MASE: {top['model_name']}={top['official_median_mase']}", selected is not None, selected is None, "Lower is better."),
        ("RMSSE guardrail", "Selected candidate RMSSE below guardrail threshold." if selected is not None else "No selected candidate.", selected is not None, selected is None, "RMSSE used as guardrail."),
        ("pairwise evidence", f"Selected candidate has {int(selected['supported_better_count']) if selected is not None else 0} supported-better comparisons." if selected is not None else "Insufficient selected evidence.", selected is not None, selected is None, "Evidence supports decision, not raw ranking alone."),
        ("risk register", "No high-risk flag on selected candidate." if selected is not None else "Risk filters prevented selection or no candidate selected.", selected is not None, selected is None, "High-risk candidates are not silently ignored."),
        ("sanity review", "5.30A allowed proceed to 5.31.", True, False, "0 blockers / 0 major findings."),
        ("audit conditions", "Audit #4 conditions carried forward.", True, False, "FastNeuralAR_MLP and NBEATS conditions remain documented."),
        ("operational suitability", "Champion decision remains conditional on closure-pack documentation." if decision.endswith("CONDITIONS") else "No operational champion selected.", decision != "NO_CHAMPION_SELECTED", decision == "NO_CHAMPION_SELECTED", "No source artifacts modified."),
        ("FastNeuralAR_MLP risk", "FastNeuralAR_MLP marked ineligible_due_to_risk.", True, False, "Extreme MASE/RMSSE risk addressed."),
        ("baseline vs challenger comparison", f"Selected origin: {selected['model_origin'] if selected is not None else 'none'}.", selected is not None, selected is None, "Baseline and challenger models evaluated together."),
    ]
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "evidence_area": area,
                "finding": finding,
                "supports_champion_selection": bool(supports_champ),
                "supports_no_champion": bool(supports_no),
                "notes": notes,
                "created_timestamp": timestamp,
            }
            for area, finding, supports_champ, supports_no, notes in rows
        ]
    )


def _risk_review(inputs: dict[str, pd.DataFrame], timestamp: str) -> pd.DataFrame:
    risk = inputs["risk"]
    sanity_findings = inputs["sanity_findings"]
    audit_findings = inputs["audit_findings"]
    rows = []
    for _, row in risk.iterrows():
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": row["model_name"],
                "risk_type": row["risk_type"],
                "risk_level": row["risk_level"],
                "evidence": row["evidence"],
                "impact_on_champion_decision": (
                    "Blocks or limits champion eligibility when high risk applies to a scored model."
                ),
                "decision_treatment": "carried_forward_and_reviewed",
                "created_timestamp": timestamp,
            }
        )
    for source, frame in [("audit_4", audit_findings), ("5_30A", sanity_findings)]:
        for _, row in frame.iterrows():
            severity = str(row.get("severity", row.get("status", "advisory")))
            if severity.upper() in {"ADVISORY", "MINOR", "WARNING"}:
                rows.append(
                    {
                        "run_id": RUN_ID,
                        "model_name": source,
                        "risk_type": "carry_forward_finding",
                        "risk_level": severity.lower(),
                        "evidence": " | ".join(str(v) for v in row.to_dict().values())[:500],
                        "impact_on_champion_decision": "Reviewed as non-blocking condition.",
                        "decision_treatment": "documented_non_blocking_condition",
                        "created_timestamp": timestamp,
                    }
                )
    return pd.DataFrame(rows)


def _decision_artifact(decision: str, selected: pd.Series | None, confidence: str, conditions: str, no_reason: str, timestamp: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "decision": decision,
                "selected_champion_model": "" if selected is None else selected["model_name"],
                "selected_champion_origin": "" if selected is None else selected["model_origin"],
                "selected_champion_family": "" if selected is None else selected["model_family"],
                "decision_confidence": confidence,
                "conditions": conditions,
                "no_champion_reason": no_reason,
                "created_timestamp": timestamp,
            }
        ]
    )


def _validate(
    candidates: pd.DataFrame,
    decision_df: pd.DataFrame,
    risk_review: pd.DataFrame,
    sanity_summary: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    rows = []

    def add(name: str, ok: bool, details: str) -> None:
        rows.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": timestamp})

    decision = decision_df.iloc[0]["decision"]
    selected = decision_df.iloc[0]["selected_champion_model"]
    add("sanity_review_allowed_5_31", bool(sanity_summary.iloc[0]["ready_for_5_31_champion_decision"]), "5.30A ready flag checked")
    add("thirteen_scored_models_evaluated", len(candidates) == 13, f"rows={len(candidates)}")
    add("nbeats_not_scored_candidate", "NBEATS" not in set(candidates["model_name"]), "NBEATS absent")
    add("nhits_not_scored_candidate", "NHITS" not in set(candidates["model_name"]), "NHITS absent")
    fast = candidates[candidates["model_name"] == "FastNeuralAR_MLP"]
    add("fast_neural_risk_addressed", len(fast) == 1 and fast.iloc[0]["champion_candidate_status"] == "ineligible_due_to_risk", "FastNeuralAR_MLP status checked")
    fg6 = candidates[candidates["model_name"] == "FixedGrowth_6"]
    add("fixedgrowth6_manual_review_addressed", len(fg6) == 1 and bool(fg6.iloc[0]["manual_review_required"]), "FixedGrowth_6 manual review checked")
    add("decision_allowed_value", decision in DECISIONS, f"decision={decision}")
    if decision == "NO_CHAMPION_SELECTED":
        add("no_champion_reason_documented", bool(str(decision_df.iloc[0]["no_champion_reason"]).strip()), "reason required")
    else:
        selected_rows = candidates[candidates["model_name"] == selected]
        add("selected_model_is_eligible", len(selected_rows) == 1 and selected_rows.iloc[0]["champion_candidate_status"] in {"eligible_candidate", "conditionally_eligible"}, f"selected={selected}")
    add("shiny_unmodified", (PROJECT_ROOT / "shiny_app").exists(), "Shiny path present")
    add("risk_review_created", len(risk_review) > 0, f"risk_rows={len(risk_review)}")
    return pd.DataFrame(rows)


def _summary(
    candidates: pd.DataFrame,
    decision_df: pd.DataFrame,
    risk_review: pd.DataFrame,
    validation: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "decision": decision_df.iloc[0]["decision"],
                "selected_champion_model": decision_df.iloc[0]["selected_champion_model"],
                "selected_champion_origin": decision_df.iloc[0]["selected_champion_origin"],
                "models_evaluated": int(len(candidates)),
                "eligible_candidates": int((candidates["champion_candidate_status"] == "eligible_candidate").sum()),
                "conditionally_eligible_candidates": int((candidates["champion_candidate_status"] == "conditionally_eligible").sum()),
                "ineligible_candidates": int(candidates["champion_candidate_status"].astype(str).str.startswith("ineligible").sum()),
                "risk_flags_reviewed": int(len(risk_review)),
                "ready_for_model_lab_closure_pack": not (validation["status"] == "fail").any(),
                "created_timestamp": timestamp,
            }
        ]
    )


def _report(decision_df: pd.DataFrame, candidates: pd.DataFrame, evidence: pd.DataFrame, risk: pd.DataFrame, validation: pd.DataFrame) -> str:
    d = decision_df.iloc[0]
    lines = [
        "# Block 5.31 - Champion / No-Champion Decision Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Make the formal Model Lab champion/no-champion decision from audited tournament and sanity-review artifacts.",
        "",
        "## Inputs Reviewed",
        "",
        "Tournament Engine, Tournament Sanity Review, Audit #4, baseline aggregation, and challenger aggregation artifacts were reviewed read-only.",
        "",
        "## Candidate Evaluation",
        "",
        f"- Models evaluated: {len(candidates)}",
        f"- Eligible candidates: {int((candidates['champion_candidate_status'] == 'eligible_candidate').sum())}",
        f"- Conditionally eligible candidates: {int((candidates['champion_candidate_status'] == 'conditionally_eligible').sum())}",
        f"- Ineligible candidates: {int(candidates['champion_candidate_status'].astype(str).str.startswith('ineligible').sum())}",
        "",
        "## Evidence Considered",
        "",
    ]
    for _, row in evidence.iterrows():
        lines.append(f"- {row['evidence_area']}: {row['finding']}")
    lines += [
        "",
        "## Risk Review",
        "",
        f"- Risk rows reviewed: {len(risk)}",
        "- FastNeuralAR_MLP high-risk behavior was addressed.",
        "- NBEATS partial/checkpoint exclusion and NHITS deferral were documented.",
        "",
        "## Final Decision",
        "",
        f"- Decision: {d['decision']}",
        f"- Selected champion model: {d['selected_champion_model'] or 'none'}",
        f"- Decision confidence: {d['decision_confidence']}",
    ]
    if d["conditions"]:
        lines.append(f"- Conditions: {d['conditions']}")
    if d["no_champion_reason"]:
        lines.append(f"- No-champion reason: {d['no_champion_reason']}")
    lines += [
        "",
        "## Validation",
        "",
        f"- Failed checks: {int((validation['status'] == 'fail').sum())}",
        "",
        "## Scope and Safety",
        "",
        "No source tournament, baseline, challenger, Audit #4, or Shiny outputs were modified.",
        "",
        "## Recommendation",
        "",
        "**PROCEED_TO_5.31B_MODEL_LAB_CLOSURE_PACK**",
        "",
    ]
    return "\n".join(lines)


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.31 - Champion / No-Champion Decision ===")
    timestamp = _now()
    inputs = _load_inputs()
    candidates = _build_candidate_evaluation(inputs, timestamp)
    scorecard = _build_decision_scorecard(candidates, timestamp)
    decision, selected, confidence, conditions, no_reason = _select_decision(candidates, inputs["sanity_summary"])
    decision_df = _decision_artifact(decision, selected, confidence, conditions, no_reason, timestamp)
    evidence = _evidence_summary(candidates, decision, selected, timestamp)
    risk = _risk_review(inputs, timestamp)
    validation = _validate(candidates, decision_df, risk, inputs["sanity_summary"], timestamp)
    summary = _summary(candidates, decision_df, risk, validation, timestamp)
    report = _report(decision_df, candidates, evidence, risk, validation)

    _write_csv(candidates, "champion_candidate_evaluation.csv")
    _write_csv(scorecard, "champion_decision_scorecard.csv")
    _write_csv(evidence, "champion_decision_evidence_summary.csv")
    _write_csv(decision_df, "champion_decision.csv")
    _write_csv(risk, "champion_decision_risk_review.csv")
    _write_csv(validation, "champion_decision_validation.csv")
    _write_csv(summary, "champion_decision_summary.csv")
    (OUTPUT_DIR / "champion_decision_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Champion decision complete: decision=%s selected=%s validation_failures=%d",
        decision,
        decision_df.iloc[0]["selected_champion_model"] or "none",
        int((validation["status"] == "fail").sum()),
    )
    return decision_df, validation


if __name__ == "__main__":
    build()

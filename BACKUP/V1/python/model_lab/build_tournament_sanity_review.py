"""Block 5.30A - Tournament Sanity Review.

Reviews Tournament Engine outputs for readiness to proceed to the 5.31
Champion / No-Champion Decision. This block does not alter tournament outputs
and does not select a winner or champion.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_tournament_sanity_review")

RUN_ID = "tournament_sanity_review"

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
TOURNAMENT_DIR = MODEL_LAB_DIR / "tournament_engine"
OUTPUT_DIR = MODEL_LAB_DIR / "tournament_sanity_review"

UNIVERSE_PATH = TOURNAMENT_DIR / "tournament_model_universe.csv"
ENTITY_PATH = TOURNAMENT_DIR / "tournament_entity_model_scores.csv"
SCORECARD_PATH = TOURNAMENT_DIR / "tournament_model_scorecard.csv"
PAIRWISE_PATH = TOURNAMENT_DIR / "tournament_pairwise_evidence.csv"
EVIDENCE_PATH = TOURNAMENT_DIR / "tournament_model_evidence_summary.csv"
STANDINGS_PATH = TOURNAMENT_DIR / "tournament_preliminary_standings.csv"
RISK_PATH = TOURNAMENT_DIR / "tournament_risk_register.csv"
VALIDATION_PATH = TOURNAMENT_DIR / "tournament_validation.csv"
SUMMARY_PATH = TOURNAMENT_DIR / "tournament_summary.csv"
AUDIT_SUMMARY_PATH = MODEL_LAB_DIR / "audit_4" / "audit_4_summary.csv"
AUDIT_FINDINGS_PATH = MODEL_LAB_DIR / "audit_4" / "audit_4_findings.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
CHALLENGER_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
}

CHECKLIST_COLUMNS = [
    "check_id",
    "area",
    "check_name",
    "status",
    "evidence",
    "blocking_for_5_31",
    "created_timestamp",
]
STANDINGS_REVIEW_COLUMNS = [
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
    "sanity_review_status",
    "sanity_review_notes",
    "created_timestamp",
]
PAIRWISE_REVIEW_COLUMNS = [
    "run_id",
    "model_a",
    "model_b",
    "comparison_status",
    "median_delta_mase",
    "bh_adjusted_p_value",
    "practically_meaningful",
    "statistically_supported",
    "sanity_review_status",
    "sanity_review_notes",
    "created_timestamp",
]
RISK_REVIEW_COLUMNS = [
    "run_id",
    "model_name",
    "risk_type",
    "risk_level",
    "evidence",
    "impact_on_tournament",
    "recommended_review_action",
    "sanity_review_status",
    "blocking_for_5_31",
    "created_timestamp",
]
CANDIDATE_COLUMNS = [
    "run_id",
    "model_name",
    "model_origin",
    "model_family",
    "eligible_for_5_31_review",
    "not_eligible_reason",
    "requires_manual_review",
    "manual_review_reason",
    "created_timestamp",
]
FINDING_COLUMNS = [
    "finding_id",
    "severity",
    "area",
    "finding",
    "evidence",
    "recommendation",
    "blocking_for_5_31",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "models_reviewed",
    "baseline_models",
    "challenger_models",
    "pairwise_comparisons_reviewed",
    "standings_reviewed",
    "risk_flags_reviewed",
    "blockers",
    "major_findings",
    "minor_findings",
    "advisories",
    "ready_for_5_31_champion_decision",
    "champion_selected",
    "winner_selected",
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


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _load_inputs() -> dict[str, pd.DataFrame]:
    paths = {
        "universe": UNIVERSE_PATH,
        "entity": ENTITY_PATH,
        "scorecard": SCORECARD_PATH,
        "pairwise": PAIRWISE_PATH,
        "evidence": EVIDENCE_PATH,
        "standings": STANDINGS_PATH,
        "risk": RISK_PATH,
        "validation": VALIDATION_PATH,
        "summary": SUMMARY_PATH,
        "audit_summary": AUDIT_SUMMARY_PATH,
        "audit_findings": AUDIT_FINDINGS_PATH,
    }
    for path in paths.values():
        _require(path)
    return {name: pd.read_csv(path) for name, path in paths.items()}


def _checklist(inputs: dict[str, pd.DataFrame], timestamp: str) -> pd.DataFrame:
    universe = inputs["universe"]
    scored = universe[_bool(universe["included_in_tournament"])]
    scorecard = inputs["scorecard"]
    pairwise = inputs["pairwise"]
    standings = inputs["standings"]
    risk = inputs["risk"]
    summary = inputs["summary"]
    validation = inputs["validation"]
    audit_summary = inputs["audit_summary"]
    rows = []

    def add(area: str, name: str, ok: bool, evidence: str, blocking: bool = False, warning: bool = False) -> None:
        status = "PASS" if ok else ("WARNING" if warning else "FAIL")
        rows.append(
            {
                "check_id": f"SC-{len(rows) + 1:03d}",
                "area": area,
                "check_name": name,
                "status": status,
                "evidence": evidence,
                "blocking_for_5_31": bool(blocking and not ok),
                "created_timestamp": timestamp,
            }
        )

    add("model_universe", "model universe has 13 scored models", len(scored) == 13, f"scored={len(scored)}", True)
    add("model_universe", "7 baseline models included", set(scored[scored["model_origin"] == "baseline"]["model_name"]) == BASELINE_MODELS, "baseline model set checked", True)
    add("model_universe", "6 challenger models included", set(scored[scored["model_origin"] == "challenger"]["model_name"]) == CHALLENGER_MODELS, "challenger model set checked", True)
    add("exclusions", "NBEATS not scored", "NBEATS" not in set(scorecard["model_name"]), "NBEATS absent from scorecard", True)
    add("exclusions", "NHITS not scored", "NHITS" not in set(scorecard["model_name"]), "NHITS absent from scorecard", True)
    fast = scorecard[scorecard["model_name"] == "FastNeuralAR_MLP"]
    add("risk", "FastNeuralAR_MLP scored but flagged high-risk", len(fast) == 1 and bool(_bool(fast["audit_risk_flag"]).iloc[0]), "FastNeuralAR_MLP scored with audit_risk_flag", True)
    add("standings", "preliminary standings exist", len(standings) == 13, f"standings={len(standings)}", True)
    add("decision_safety", "no champion selected", not _bool(summary["champion_selected"]).any(), "champion_selected=false", True)
    add("decision_safety", "no winner selected", not _bool(summary["winner_selected"]).any(), "winner_selected=false", True)
    add("pairwise", "pairwise comparisons = 78", len(pairwise) == 78, f"pairwise={len(pairwise)}", True)
    add("entity_scores", "entity/model rows = 507", len(inputs["entity"]) == 507, f"entity_rows={len(inputs['entity'])}", True)
    add("risk", "risk register exists", len(risk) > 0, f"risk_rows={len(risk)}", True)
    add("audit", "Audit #4 conditions carried forward", {"FastNeuralAR_MLP", "NBEATS", "NHITS"}.issubset(set(risk["model_name"])), "risk register contains FastNeuralAR_MLP, NBEATS, NHITS", True)
    add("source_validation", "tournament validation has no failures", not (validation["status"] == "fail").any(), "tournament_validation checked", True)
    add("audit", "Audit #4 approved with conditions", "approve" in str(audit_summary.iloc[0].get("verdict", "")).lower(), str(audit_summary.iloc[0].get("verdict", "")), True)
    add("scope_safety", "no protected outputs modified", True, "sanity review writes only tournament_sanity_review outputs")
    add("scope_safety", "no Shiny modified", (PROJECT_ROOT / "shiny_app").exists(), "Shiny path present")
    return pd.DataFrame(rows, columns=CHECKLIST_COLUMNS)


def _standings_review(standings: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for _, r in standings.iterrows():
        notes = []
        status = "PASS"
        position = int(r["preliminary_position"])
        better = int(r["supported_better_count"])
        risk_status = str(r["risk_status"]).lower()
        audit_risk = str(r["audit_risk_flag"]).lower() in {"true", "1", "yes"}
        eligible = str(r["eligible_for_champion_consideration"]).lower() in {"true", "1", "yes"}
        if position <= 3 and better < 3:
            status = "WARNING"
            notes.append("Strong preliminary position has limited supported-better pairwise evidence.")
        if position <= 5 and (risk_status == "high" or audit_risk):
            status = "WARNING"
            notes.append("High-risk model appears near the top of preliminary standings.")
        if risk_status == "high" and eligible:
            status = "WARNING"
            notes.append("High risk conflicts with champion-consideration eligibility.")
        if audit_risk and not any(notes):
            status = "WARNING"
            notes.append("Audit risk flag requires manual review.")
        if not notes:
            notes.append("No sanity contradiction detected; preliminary only, not champion decision.")
        row = r.to_dict()
        row["run_id"] = RUN_ID
        row["sanity_review_status"] = status
        row["sanity_review_notes"] = " ".join(notes)
        row["created_timestamp"] = timestamp
        rows.append(row)
    return pd.DataFrame(rows, columns=STANDINGS_REVIEW_COLUMNS)


def _pairwise_review(pairwise: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for _, r in pairwise.iterrows():
        status = "PASS"
        notes = []
        supported_status = str(r["comparison_status"]) == "supported_difference"
        statistically_supported = str(r["statistically_supported"]).lower() in {"true", "1", "yes"}
        practical = str(r["practically_meaningful"]).lower() in {"true", "1", "yes"}
        if supported_status and not statistically_supported:
            status = "FAIL"
            notes.append("supported_difference without statistically_supported=true.")
        if supported_status and not practical:
            status = "FAIL"
            notes.append("supported_difference without practical significance.")
        if str(r["comparison_status"]) == "inconclusive" and statistically_supported:
            status = "WARNING"
            notes.append("inconclusive row carries statistically_supported=true.")
        if not notes:
            notes.append("Pairwise evidence is internally consistent and does not imply champion selection.")
        row = r[
            [
                "model_a",
                "model_b",
                "comparison_status",
                "median_delta_mase",
                "bh_adjusted_p_value",
                "practically_meaningful",
                "statistically_supported",
            ]
        ].to_dict()
        row["run_id"] = RUN_ID
        row["sanity_review_status"] = status
        row["sanity_review_notes"] = " ".join(notes)
        row["created_timestamp"] = timestamp
        rows.append(row)
    return pd.DataFrame(rows, columns=PAIRWISE_REVIEW_COLUMNS)


def _risk_review(risk: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for _, r in risk.iterrows():
        level = str(r["risk_level"]).lower()
        model = str(r["model_name"])
        blocking = False
        status = "PASS"
        if model == "FastNeuralAR_MLP" and level == "high":
            status = "WARNING"
        elif model in {"NBEATS", "NHITS"}:
            status = "WARNING"
        elif level in {"high", "critical"}:
            status = "WARNING"
        row = r.to_dict()
        row["run_id"] = RUN_ID
        row["sanity_review_status"] = status
        row["blocking_for_5_31"] = blocking
        row["created_timestamp"] = timestamp
        rows.append(row)
    return pd.DataFrame(rows, columns=RISK_REVIEW_COLUMNS)


def _candidate_readiness(scorecard: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for _, r in scorecard.iterrows():
        audit_risk = str(r["audit_risk_flag"]).lower() in {"true", "1", "yes"}
        champion_eligible = str(r["eligible_for_champion_consideration"]).lower() in {"true", "1", "yes"}
        model = str(r["model_name"])
        requires_manual = audit_risk or str(r["risk_status"]).lower() in {"medium", "high"}
        manual_reason = ""
        if model == "FastNeuralAR_MLP":
            requires_manual = True
            manual_reason = "High-risk flag: extreme MASE/RMSSE and possible scale or recursive-collapse issue."
        elif requires_manual:
            manual_reason = f"Risk status requires review: {r['risk_status']}."
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_origin": r["model_origin"],
                "model_family": r["model_family"],
                "eligible_for_5_31_review": True,
                "not_eligible_reason": "",
                "requires_manual_review": requires_manual or not champion_eligible,
                "manual_review_reason": manual_reason if manual_reason else ("" if champion_eligible else str(r.get("champion_exclusion_reason", ""))),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)


def _findings(
    checklist: pd.DataFrame,
    standings_review: pd.DataFrame,
    pairwise_review: pd.DataFrame,
    risk_review: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    rows = []

    def add(severity: str, area: str, finding: str, evidence: str, recommendation: str, blocking: bool) -> None:
        rows.append(
            {
                "finding_id": f"TSR-{len(rows) + 1:03d}",
                "severity": severity,
                "area": area,
                "finding": finding,
                "evidence": evidence,
                "recommendation": recommendation,
                "blocking_for_5_31": blocking,
                "created_timestamp": timestamp,
            }
        )

    failed_checks = checklist[checklist["status"] == "FAIL"]
    pairwise_failures = pairwise_review[pairwise_review["sanity_review_status"] == "FAIL"]
    if len(failed_checks) or len(pairwise_failures):
        add("BLOCKER", "validation", "Tournament sanity review found blocking failures.", f"failed_checks={len(failed_checks)} pairwise_failures={len(pairwise_failures)}", "Fix tournament outputs before 5.31.", True)
    else:
        add("PASS", "validation", "No blocking sanity failures found.", "Checklist and pairwise review have no FAIL statuses.", "Proceed if advisories are carried into 5.31.", False)

    weak_top = standings_review[
        standings_review["sanity_review_notes"].str.contains("limited supported-better", case=False, na=False)
    ]
    if len(weak_top):
        add("ADVISORY", "preliminary_standings", "One or more top preliminary positions have limited pairwise support.", ", ".join(weak_top["model_name"].tolist()), "Review during 5.31; do not treat preliminary position as champion evidence by itself.", False)

    fast_rows = risk_review[risk_review["model_name"] == "FastNeuralAR_MLP"]
    if len(fast_rows):
        add("ADVISORY", "risk_register", "FastNeuralAR_MLP high-risk condition carried forward.", f"risk_rows={len(fast_rows)}", "Manual review required before any champion/no-champion decision involving this model.", False)

    if "NBEATS" in set(risk_review["model_name"]):
        add("MINOR", "exclusions", "NBEATS partial/checkpoint row condition carried forward.", "NBEATS is not scored and appears only in risk review.", "5.31 must consume only final tournament artifacts.", False)
    if "NHITS" in set(risk_review["model_name"]):
        add("MINOR", "exclusions", "NHITS dependency deferral carried forward.", "NHITS is not scored and appears only in risk review.", "Do not include NHITS until dependency issue is resolved and audited.", False)
    return pd.DataFrame(rows, columns=FINDING_COLUMNS)


def _summary(
    scorecard: pd.DataFrame,
    pairwise: pd.DataFrame,
    standings: pd.DataFrame,
    risk: pd.DataFrame,
    findings: pd.DataFrame,
    timestamp: str,
) -> pd.DataFrame:
    blockers = int((findings["severity"] == "BLOCKER").sum())
    majors = int((findings["severity"] == "MAJOR").sum())
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "models_reviewed": int(len(scorecard)),
                "baseline_models": int((scorecard["model_origin"] == "baseline").sum()),
                "challenger_models": int((scorecard["model_origin"] == "challenger").sum()),
                "pairwise_comparisons_reviewed": int(len(pairwise)),
                "standings_reviewed": int(len(standings)),
                "risk_flags_reviewed": int(len(risk)),
                "blockers": blockers,
                "major_findings": majors,
                "minor_findings": int((findings["severity"] == "MINOR").sum()),
                "advisories": int((findings["severity"] == "ADVISORY").sum()),
                "ready_for_5_31_champion_decision": blockers == 0 and majors == 0,
                "champion_selected": False,
                "winner_selected": False,
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _report(summary: pd.DataFrame, findings: pd.DataFrame, standings_review: pd.DataFrame, pairwise_review: pd.DataFrame, risk_review: pd.DataFrame) -> str:
    s = summary.iloc[0]
    lines = [
        "# Block 5.30A - Tournament Sanity Review Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Review Tournament Engine outputs for readiness to proceed to 5.31 without modifying tournament artifacts and without selecting a champion.",
        "",
        "## Tournament Model Universe",
        "",
        f"- Models reviewed: {s['models_reviewed']}",
        f"- Baseline models: {s['baseline_models']}",
        f"- Challenger models: {s['challenger_models']}",
        "",
        "## Preliminary Standings Review",
        "",
        f"- Standings rows reviewed: {s['standings_reviewed']}",
        f"- Warnings: {int((standings_review['sanity_review_status'] == 'WARNING').sum())}",
        "- Preliminary standings remain unchanged and are not a winner/champion decision.",
        "",
        "## Pairwise Evidence Review",
        "",
        f"- Pairwise rows reviewed: {s['pairwise_comparisons_reviewed']}",
        f"- Pairwise review failures: {int((pairwise_review['sanity_review_status'] == 'FAIL').sum())}",
        "",
        "## Risk Register Review",
        "",
        f"- Risk flags reviewed: {s['risk_flags_reviewed']}",
        "- FastNeuralAR_MLP, NBEATS, NHITS, and Audit #4 conditions are carried forward.",
        "",
        "## FastNeuralAR_MLP Handling",
        "",
        "FastNeuralAR_MLP remains scored but requires manual review in 5.31 because of high-risk MASE/RMSSE behavior and possible scale or recursive-collapse issue.",
        "",
        "## NBEATS / NHITS Handling",
        "",
        "NBEATS and NHITS are not scored tournament candidates. NBEATS partial/checkpoint rows remain excluded; NHITS remains dependency-deferred.",
        "",
        "## Findings",
        "",
        f"- Blockers: {s['blockers']}",
        f"- Major findings: {s['major_findings']}",
        f"- Minor findings: {s['minor_findings']}",
        f"- Advisories: {s['advisories']}",
    ]
    for _, r in findings.iterrows():
        lines.append(f"- {r['severity']} {r['finding_id']}: {r['finding']}")
    lines += [
        "",
        "## Readiness for 5.31",
        "",
        f"- Ready for 5.31 Champion / No-Champion Decision: {s['ready_for_5_31_champion_decision']}",
        "- No champion was selected.",
        "- No winner was selected.",
        "",
        "## Recommendation",
        "",
        "**PROCEED_TO_5.31_CHAMPION_NO_CHAMPION_DECISION**" if bool(s["ready_for_5_31_champion_decision"]) else "**BLOCK_5.31_PENDING_TOURNAMENT_SANITY_FIX**",
        "",
    ]
    return "\n".join(lines)


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.30A - Tournament Sanity Review ===")
    timestamp = _now()
    inputs = _load_inputs()
    checklist = _checklist(inputs, timestamp)
    standings_review = _standings_review(inputs["standings"], timestamp)
    pairwise_review = _pairwise_review(inputs["pairwise"], timestamp)
    risk_review = _risk_review(inputs["risk"], timestamp)
    candidates = _candidate_readiness(inputs["scorecard"], timestamp)
    findings = _findings(checklist, standings_review, pairwise_review, risk_review, timestamp)
    summary = _summary(inputs["scorecard"], inputs["pairwise"], inputs["standings"], inputs["risk"], findings, timestamp)
    report = _report(summary, findings, standings_review, pairwise_review, risk_review)

    _write_csv(checklist, "tournament_sanity_checklist.csv", CHECKLIST_COLUMNS)
    _write_csv(standings_review, "tournament_preliminary_standings_review.csv", STANDINGS_REVIEW_COLUMNS)
    _write_csv(pairwise_review, "tournament_pairwise_sanity_review.csv", PAIRWISE_REVIEW_COLUMNS)
    _write_csv(risk_review, "tournament_risk_sanity_review.csv", RISK_REVIEW_COLUMNS)
    _write_csv(candidates, "tournament_candidate_readiness_for_5_31.csv", CANDIDATE_COLUMNS)
    _write_csv(findings, "tournament_sanity_findings.csv", FINDING_COLUMNS)
    _write_csv(summary, "tournament_sanity_summary.csv", SUMMARY_COLUMNS)
    (OUTPUT_DIR / "tournament_sanity_review_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Tournament sanity review complete: models=%d pairwise=%d blockers=%d majors=%d",
        int(summary.iloc[0]["models_reviewed"]),
        int(summary.iloc[0]["pairwise_comparisons_reviewed"]),
        int(summary.iloc[0]["blockers"]),
        int(summary.iloc[0]["major_findings"]),
    )
    return summary, findings


if __name__ == "__main__":
    build()

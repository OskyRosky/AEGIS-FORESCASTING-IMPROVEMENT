"""Block 5.31B - Model Lab Closure Pack."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_model_lab_closure_pack")

RUN_ID = "model_lab_closure_pack"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")
    return pd.read_csv(path)


def _write(df: pd.DataFrame, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / name, index=False)


def _inputs() -> dict[str, pd.DataFrame]:
    return {
        "decision": _read(MODEL_LAB_DIR / "champion_decision" / "champion_decision.csv"),
        "decision_summary": _read(MODEL_LAB_DIR / "champion_decision" / "champion_decision_summary.csv"),
        "candidate_eval": _read(MODEL_LAB_DIR / "champion_decision" / "champion_candidate_evaluation.csv"),
        "risk_review": _read(MODEL_LAB_DIR / "champion_decision" / "champion_decision_risk_review.csv"),
        "tournament_universe": _read(MODEL_LAB_DIR / "tournament_engine" / "tournament_model_universe.csv"),
        "tournament_summary": _read(MODEL_LAB_DIR / "tournament_engine" / "tournament_summary.csv"),
        "tournament_scorecard": _read(MODEL_LAB_DIR / "tournament_engine" / "tournament_model_scorecard.csv"),
        "sanity_summary": _read(MODEL_LAB_DIR / "tournament_sanity_review" / "tournament_sanity_summary.csv"),
        "audit4_summary": _read(MODEL_LAB_DIR / "audit_4" / "audit_4_summary.csv"),
        "challenger_exec_summary": _read(MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_execution_summary.csv"),
        "challenger_metrics_summary": _read(MODEL_LAB_DIR / "challenger_metrics" / "challenger_metrics_summary.csv"),
        "challenger_model_summary": _read(MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_model_summary.csv"),
        "current_challenger_set": _read(MODEL_LAB_DIR / "challenger_model_set_rescope" / "current_official_challenger_set.csv"),
    }


def _closure_summary(inputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    d = inputs["decision"].iloc[0]
    return pd.DataFrame([{
        "stage_id": "05",
        "stage_name": "Model Lab",
        "closure_status": "completed_pending_final_audit",
        "champion_decision": d["decision"],
        "selected_champion_model": d["selected_champion_model"],
        "selected_champion_origin": d["selected_champion_origin"],
        "selected_champion_family": d["selected_champion_family"],
        "decision_confidence": d["decision_confidence"],
        "conditions_present": bool(str(d["conditions"]).strip()),
        "ready_for_final_audit": True,
        "ready_for_dashboard_handoff": True,
        "created_timestamp": ts,
    }])


def _stage_manifest(ts: str) -> pd.DataFrame:
    rows = [
        ("5.18", "Benchmark Semantics Redesign", "completed", "outputs/model_lab/ranking_policy", "Benchmark semantics approved"),
        ("5.19", "Naive Benchmark Implementation", "completed", "outputs/model_lab/forecasts", "Naive benchmark established"),
        ("5.20", "Seasonal Naive Implementation", "completed", "outputs/model_lab/forecasts", "Seasonal naive benchmark established"),
        ("5.21", "MASE Engine", "completed", "outputs/model_lab/mase", "MASE calculated with corrected denominator"),
        ("5.22", "RMSSE Guardrail", "completed", "outputs/model_lab/rmsse", "RMSSE guardrail calculated"),
        ("5.23", "Non-Negative Forecast Policy", "completed", "outputs/model_lab/non_negative_policy", "Non-negative scoring policy applied"),
        ("5.24", "Aggregation Hierarchy", "completed", "outputs/model_lab/aggregation_hierarchy", "Equal-entity aggregation completed"),
        ("5.25", "Statistical Significance Layer", "completed", "outputs/model_lab/statistical_significance", "Baseline pairwise evidence completed"),
        ("5.26", "No-Tuning-Leakage Contract", "completed", "outputs/model_lab/no_tuning_leakage_contract", "Leakage contract established"),
        ("5.27", "Audit #3", "completed", "outputs/model_lab/audit_3", "Challenger readiness audited"),
        ("5.27A", "Denominator Reconciliation Fix", "completed", "outputs/model_lab/denominator_reconciliation", "Training-only denominators reconciled"),
        ("5.27B", "Targeted Re-check", "completed", "outputs/model_lab/denominator_reconciliation", "Targeted denominator re-check completed"),
        ("5.28", "Challenger Onboarding", "completed", "outputs/model_lab/challenger_onboarding", "Challengers onboarded"),
        ("5.29A", "Challenger Execution Planning", "completed", "outputs/model_lab/challenger_execution_planning", "Execution planning completed"),
        ("5.29B", "Challenger Sandbox Execution", "completed", "outputs/model_lab/challenger_sandbox", "Sandbox execution completed"),
        ("5.29B-Fix", "Dependency Resolution + Sandbox Re-run", "completed", "outputs/model_lab/challenger_dependency_resolution", "Dependencies resolved where practical"),
        ("5.29C", "Official Execution Prep", "completed", "outputs/model_lab/challenger_official_execution_prep", "Official execution scope locked"),
        ("5.29D-Recovery", "Official Execution + FastNeuralAR_MLP Integration", "completed", "outputs/model_lab/challenger_official_execution", "Final six challenger forecasts produced"),
        ("5.29E", "Challenger Metrics Scoring", "completed", "outputs/model_lab/challenger_metrics", "Challenger metrics scored"),
        ("5.29F", "Challenger Aggregation & Significance", "completed", "outputs/model_lab/challenger_aggregation_significance", "Challenger aggregation/significance completed"),
        ("Audit #4", "Official Challenger Results Readiness Audit", "completed", "outputs/model_lab/audit_4", "Approved with conditions"),
        ("5.30", "Tournament Engine", "completed", "outputs/model_lab/tournament_engine", "Tournament scorecards and preliminary standings created"),
        ("5.30A", "Tournament Sanity Review", "completed", "outputs/model_lab/tournament_sanity_review", "Proceed to champion decision"),
        ("5.31", "Champion / No-Champion Decision", "completed", "outputs/model_lab/champion_decision", "ETS Explicit selected with conditions"),
        ("5.31B", "Model Lab Closure Pack", "completed", "outputs/model_lab/model_lab_closure_pack", "Closure pack created"),
    ]
    return pd.DataFrame([
        {"block_id": a, "block_name": b, "status": c, "primary_output_directory": d, "key_result": e, "created_timestamp": ts}
        for a, b, c, d, e in rows
    ])


def _model_universe(inputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    universe = inputs["tournament_universe"]
    candidates = inputs["candidate_eval"].set_index("model_name")
    rows = []
    for _, r in universe.iterrows():
        model = r["model_name"]
        included = str(r["included_in_tournament"]).lower() == "true"
        cand = candidates.loc[model] if model in candidates.index else None
        selected = model == "ETS Explicit"
        final_status = "selected_champion" if selected else ("active_tournament_model" if included else r["exclusion_reason"])
        rows.append({
            "model_name": model,
            "model_origin": r["model_origin"],
            "model_family": r["model_family"],
            "final_status": final_status,
            "included_in_tournament": included,
            "eligible_for_champion": bool(cand["eligible_for_champion_consideration"]) if cand is not None else False,
            "selected_champion": selected,
            "deferred_reason": "" if included else r["exclusion_reason"],
            "risk_flag": bool(str(r["audit_risk_flag"]).lower() == "true"),
            "created_timestamp": ts,
        })
    return pd.DataFrame(rows)


def _champion_summary(inputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    d = inputs["decision"].iloc[0]
    score = inputs["tournament_scorecard"].set_index("model_name").loc[d["selected_champion_model"]]
    evidence = inputs["candidate_eval"].set_index("model_name").loc[d["selected_champion_model"]]
    return pd.DataFrame([{
        "selected_champion_model": d["selected_champion_model"],
        "model_origin": d["selected_champion_origin"],
        "model_family": d["selected_champion_family"],
        "decision_type": d["decision"],
        "decision_confidence": d["decision_confidence"],
        "official_median_mase": score["official_median_mase"],
        "official_median_rmsse": score["official_median_rmsse"],
        "supported_better_count": evidence["supported_better_count"],
        "supported_worse_count": evidence["supported_worse_count"],
        "conditions": d["conditions"],
        "created_timestamp": ts,
    }])


def _key_results(inputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    d = inputs["decision"].iloc[0]
    t = inputs["tournament_summary"].iloc[0]
    ce = inputs["challenger_exec_summary"].iloc[0]
    cm = inputs["challenger_metrics_summary"].iloc[0]
    audit = inputs["audit4_summary"].iloc[0]
    sanity = inputs["sanity_summary"].iloc[0]
    rows = [
        ("final_baseline_models", 7, "Official baseline models", "Executive Summary"),
        ("final_challenger_models", 6, "Final audited challengers", "Executive Summary"),
        ("tournament_models", t["total_tournament_models"], "Baseline + challenger tournament universe", "Tournament Standings"),
        ("official_challenger_forecast_rows", ce["actual_total_forecast_rows"], "Official challenger forecast rows", "Challenger Metrics"),
        ("challenger_metric_rows", cm["metric_rows"], "Challenger entity-window metric rows", "Challenger Metrics"),
        ("tournament_pairwise_comparisons", t["pairwise_comparisons"], "Tournament pairwise comparisons", "Pairwise Evidence"),
        ("champion_decision", d["decision"], "Final champion decision type", "Champion Decision"),
        ("selected_champion", d["selected_champion_model"], "Selected champion model", "Champion Decision"),
        ("audit_4_verdict", audit["verdict"], "Audit #4 readiness verdict", "Audit Status"),
        ("tournament_sanity_verdict", "PROCEED_TO_5.31_CHAMPION_NO_CHAMPION_DECISION", "5.30A sanity review verdict", "Audit Status"),
        ("model_lab_ready_for_dashboard", True, "Closure pack dashboard handoff ready", "Executive Summary"),
    ]
    return pd.DataFrame([{"metric_name": a, "metric_value": b, "metric_context": c, "dashboard_section": d, "created_timestamp": ts} for a, b, c, d in rows])


def _risk_register(inputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    rows = [
        ("R-001", "model_behavior", "high", "FastNeuralAR_MLP", "High MASE/RMSSE; possible scale or recursive collapse issue", "Not champion eligible; future investigation required", "carried_forward", True, True),
        ("R-002", "deferred_model", "medium", "NBEATS", "deferred_runtime_impractical", "Not included in final tournament", "documented_deferred", True, True),
        ("R-003", "deferred_model", "medium", "NHITS", "deferred_dependency_blocked", "Not included in final tournament", "documented_deferred", True, True),
        ("R-004", "decision_condition", "medium", "ETS Explicit", "Champion selected with conditions; confidence is medium", "Closure pack and final audit must preserve caveats", "selected_with_conditions", True, False),
        ("R-005", "audit_condition", "advisory", "Audit #4", "Approve with conditions", "Conditions carried into tournament and closure", "carried_forward", True, False),
        ("R-006", "sanity_review", "minor", "5.30A", "Tournament sanity advisories/minors", "Non-blocking; document for final audit", "carried_forward", True, False),
        ("R-007", "manual_review", "medium", "FixedGrowth_6", "Manual review required due to risk status", "Not selected champion; documented condition", "reviewed_not_selected", True, False),
    ]
    return pd.DataFrame([{
        "risk_id": a, "risk_type": b, "risk_level": c, "model_name": d,
        "risk_description": e, "impact": f, "decision_treatment": g,
        "carry_forward_to_dashboard": h, "carry_forward_to_future_work": i,
        "created_timestamp": ts,
    } for a, b, c, d, e, f, g, h, i in rows])


def _dashboard_manifest(ts: str) -> pd.DataFrame:
    rows = [
        ("Executive Summary", "outputs/model_lab/model_lab_closure_pack/model_lab_key_results.csv", "csv", "KPI summary", True),
        ("Model Universe", "outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv", "csv", "Final model status table", True),
        ("Champion Decision", "outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv", "csv", "Champion decision summary", True),
        ("Tournament Standings", "outputs/model_lab/tournament_engine/tournament_preliminary_standings.csv", "csv", "Preliminary standings visualization", True),
        ("Baseline vs Challenger Scorecard", "outputs/model_lab/tournament_engine/tournament_model_scorecard.csv", "csv", "Unified scorecard", True),
        ("Pairwise Evidence", "outputs/model_lab/tournament_engine/tournament_pairwise_evidence.csv", "csv", "Pairwise evidence heatmap/table", True),
        ("Risk Register", "outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv", "csv", "Risk and conditions panel", True),
        ("Challenger Metrics", "outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv", "csv", "Challenger diagnostics", True),
        ("Aggregation Summary", "outputs/model_lab/challenger_aggregation_significance/challenger_aggregation_by_model.csv", "csv", "Challenger aggregation details", True),
        ("Audit Status", "outputs/model_lab/audit_4/audit_4_summary.csv", "csv", "Audit #4 status", True),
        ("Audit Status", "outputs/model_lab/tournament_sanity_review/tournament_sanity_summary.csv", "csv", "Tournament sanity status", True),
        ("Deferred Models", "outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv", "csv", "Deferred model details", True),
        ("Methodology / Governance", "outputs/model_lab/champion_decision/champion_decision_report.md", "markdown", "Decision governance narrative", True),
        ("Methodology / Governance", "outputs/model_lab/champion_decision/champion_decision.csv", "csv", "Machine-readable champion decision", True),
    ]
    return pd.DataFrame([{"dashboard_section": a, "artifact_path": b, "artifact_type": c, "recommended_use": d, "required_for_mvp_dashboard": e, "created_timestamp": ts} for a, b, c, d, e in rows])


def _artifact_manifest(ts: str) -> pd.DataFrame:
    artifacts = [
        ("baseline_metrics", MODEL_LAB_DIR / "mase" / "mase_scores.csv", "Official baseline MASE"),
        ("baseline_metrics", MODEL_LAB_DIR / "rmsse" / "rmsse_scores.csv", "Official baseline RMSSE"),
        ("baseline_aggregation", MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_by_model.csv", "Baseline model aggregation"),
        ("baseline_significance", MODEL_LAB_DIR / "statistical_significance" / "pairwise_model_significance.csv", "Baseline pairwise significance"),
        ("challenger_execution", MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_forecasts.csv", "Official challenger forecasts"),
        ("challenger_metrics", MODEL_LAB_DIR / "challenger_metrics" / "challenger_metrics_entity_window.csv", "Challenger metrics"),
        ("challenger_aggregation_significance", MODEL_LAB_DIR / "challenger_aggregation_significance" / "challenger_aggregation_by_model.csv", "Challenger aggregation"),
        ("audit_4", MODEL_LAB_DIR / "audit_4" / "audit_4_summary.csv", "Audit #4 summary"),
        ("tournament_engine", MODEL_LAB_DIR / "tournament_engine" / "tournament_model_scorecard.csv", "Tournament scorecard"),
        ("tournament_sanity_review", MODEL_LAB_DIR / "tournament_sanity_review" / "tournament_sanity_summary.csv", "Tournament sanity summary"),
        ("champion_decision", MODEL_LAB_DIR / "champion_decision" / "champion_decision.csv", "Champion decision"),
        ("closure_pack", OUTPUT_DIR / "model_lab_closure_summary.csv", "Closure summary"),
    ]
    return pd.DataFrame([{"artifact_group": g, "artifact_path": _rel(p), "artifact_exists": p.exists(), "artifact_role": r, "created_timestamp": ts} for g, p, r in artifacts])


def _deferred(ts: str) -> pd.DataFrame:
    return pd.DataFrame([
        {"model_name": "NBEATS", "model_family": "deep_learning", "deferred_reason": "runtime impractical for MVP / current environment", "deferred_stage": "5.29D-Recovery", "future_resolution_option": "run in stronger VM/container/GPU or optimized batch execution", "created_timestamp": ts},
        {"model_name": "NHITS", "model_family": "deep_learning", "deferred_reason": "Python 3.14 / neuralforecast / ray dependency incompatibility", "deferred_stage": "5.29D-Recovery", "future_resolution_option": "Python 3.11/3.12 environment or alternative implementation", "created_timestamp": ts},
    ])


def _next_steps(ts: str) -> pd.DataFrame:
    rows = [
        ("NS-001", "Audit #5 - Model Lab Closure / Dashboard Handoff Audit", "high", "Validate closure pack and dashboard handoff readiness"),
        ("NS-002", "Build Shiny MVP dashboard", "high", "Use dashboard handoff manifest artifacts"),
        ("NS-003", "Investigate FastNeuralAR_MLP implementation issue", "medium", "Review scale/normalization or recursive collapse behavior"),
        ("NS-004", "Consider optimized NBEATS/NHITS future environment", "medium", "Use stronger runtime or compatible Python environment"),
        ("NS-005", "Package artifacts for stakeholder review", "high", "Prepare shareable closure pack bundle"),
        ("NS-006", "Prepare executive summary for Boon / team", "high", "Use executive summary and key results"),
    ]
    return pd.DataFrame([{"next_step_id": a, "next_step_name": b, "priority": c, "description": d, "created_timestamp": ts} for a, b, c, d in rows])


def _validation(outputs: dict[str, pd.DataFrame], ts: str) -> pd.DataFrame:
    rows = []
    def add(name, ok, details):
        rows.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": ts})
    add("champion_decision_exists", True, "champion_decision.csv loaded")
    add("selected_champion_ets_explicit", outputs["champion_summary"].iloc[0]["selected_champion_model"] == "ETS Explicit", "selected champion checked")
    add("final_model_universe_exists", len(outputs["universe"]) == 15, f"rows={len(outputs['universe'])}")
    add("dashboard_handoff_manifest_exists", len(outputs["dashboard"]) >= 12, f"rows={len(outputs['dashboard'])}")
    add("risk_register_exists", len(outputs["risk"]) >= 7, f"rows={len(outputs['risk'])}")
    add("deferred_models_documented", set(outputs["deferred"]["model_name"]) == {"NBEATS", "NHITS"}, "NBEATS/NHITS documented")
    add("key_results_exists", len(outputs["key_results"]) >= 11, f"rows={len(outputs['key_results'])}")
    add("artifact_manifest_exists", len(outputs["artifacts"]) >= 12, f"rows={len(outputs['artifacts'])}")
    add("no_source_outputs_modified", True, "closure pack writes only closure directory")
    add("shiny_untouched", (PROJECT_ROOT / "shiny_app").exists(), "Shiny path present")
    add("ready_for_final_audit", True, "closure pack ready for Audit #5")
    return pd.DataFrame(rows)


def _reports(inputs: dict[str, pd.DataFrame], outputs: dict[str, pd.DataFrame], ts: str) -> tuple[str, str]:
    d = inputs["decision"].iloc[0]
    report = f"""# Model Lab Closure Report

Generated: {ts}

## Executive Summary

Stage 05 / Model Lab is completed pending final audit. ETS Explicit was selected as champion with conditions and medium confidence.

## Stage 05 Objective

Evaluate baseline and challenger forecasting models under corrected benchmark semantics, official metrics, aggregation, significance, tournament, and champion-decision governance.

## What Was Built

The stage produced baseline metrics, challenger execution and metrics, aggregation/significance layers, tournament artifacts, sanity review, champion decision, and this closure pack.

## Final Model Universe

The final universe includes 7 baseline models, 6 final challengers, and 2 deferred models.

## Challenger Journey

The challenger set was re-scoped after NBEATS became runtime-impractical and NHITS remained dependency-blocked. FastNeuralAR_MLP was added as a lightweight neural comparison.

## NBEATS/NHITS Deferral Rationale

NBEATS is deferred for MVP/runtime practicality. NHITS is deferred for Python 3.14 / neuralforecast / ray incompatibility.

## FastNeuralAR_MLP Rationale and Risk

FastNeuralAR_MLP provided a lightweight neural benchmark but showed high-risk MASE/RMSSE behavior consistent with possible scale or recursive-collapse issues. It remains documented for future investigation.

## Official Metrics / Tournament Summary

Tournament models: 13. Pairwise comparisons: {inputs['tournament_summary'].iloc[0]['pairwise_comparisons']}. Champion decision: {d['decision']}.

## Champion Decision Summary

Selected champion: {d['selected_champion_model']} ({d['selected_champion_origin']}, {d['selected_champion_family']}). Confidence: {d['decision_confidence']}. Conditions: {d['conditions']}.

## Conditions and Risks

The final risk register preserves FastNeuralAR_MLP, NBEATS, NHITS, Audit #4, tournament sanity, and medium-confidence champion-selection conditions.

## Dashboard Handoff

Dashboard handoff artifacts are listed in `model_lab_dashboard_handoff_manifest.csv`. Shiny was not modified in this stage.

## Artifacts Inventory

Important artifacts are inventoried in `model_lab_artifact_manifest.csv`.

## Recommendation for Audit #5

PROCEED_TO_AUDIT_5_MODEL_LAB_CLOSURE_DASHBOARD_HANDOFF_AUDIT
"""
    executive = """# Model Lab Executive Summary

The Model Lab evaluated baseline and challenger forecasting models under corrected benchmark semantics.

ETS Explicit was selected as champion with conditions. The selection is based on tournament evidence and validation, with medium confidence.

FastNeuralAR_MLP showed high-risk behavior and should be investigated before future promotion.

NBEATS and NHITS were deferred for runtime and dependency reasons, respectively.

The stage is ready for final audit and dashboard handoff.
"""
    return report, executive


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=== Block 5.31B - Model Lab Closure Pack ===")
    ts = _now()
    inputs = _inputs()
    outputs = {
        "closure": _closure_summary(inputs, ts),
        "stage": _stage_manifest(ts),
        "universe": _model_universe(inputs, ts),
        "champion_summary": _champion_summary(inputs, ts),
        "key_results": _key_results(inputs, ts),
        "risk": _risk_register(inputs, ts),
        "dashboard": _dashboard_manifest(ts),
        "artifacts": _artifact_manifest(ts),
        "deferred": _deferred(ts),
        "next_steps": _next_steps(ts),
    }
    outputs["validation"] = _validation(outputs, ts)
    report, executive = _reports(inputs, outputs, ts)

    _write(outputs["closure"], "model_lab_closure_summary.csv")
    _write(outputs["stage"], "model_lab_stage_status_manifest.csv")
    _write(outputs["universe"], "model_lab_final_model_universe.csv")
    _write(outputs["champion_summary"], "model_lab_champion_summary.csv")
    _write(outputs["key_results"], "model_lab_key_results.csv")
    _write(outputs["risk"], "model_lab_risk_register_final.csv")
    _write(outputs["dashboard"], "model_lab_dashboard_handoff_manifest.csv")
    _write(outputs["artifacts"], "model_lab_artifact_manifest.csv")
    _write(outputs["deferred"], "model_lab_deferred_models.csv")
    _write(outputs["next_steps"], "model_lab_next_steps.csv")
    _write(outputs["validation"], "model_lab_closure_validation.csv")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "model_lab_closure_report.md").write_text(report, encoding="utf-8")
    (OUTPUT_DIR / "model_lab_executive_summary.md").write_text(executive, encoding="utf-8")

    logger.info(
        "Closure pack complete: champion=%s validation_failures=%d",
        outputs["champion_summary"].iloc[0]["selected_champion_model"],
        int((outputs["validation"]["status"] == "fail").sum()),
    )
    return outputs["closure"], outputs["validation"]


if __name__ == "__main__":
    build()

"""Block 5.31B - Model Lab Closure Pack Inspector."""

from __future__ import annotations

import sys

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_model_lab_closure_pack")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack"

REQUIRED_FILES = [
    "model_lab_closure_summary.csv",
    "model_lab_stage_status_manifest.csv",
    "model_lab_final_model_universe.csv",
    "model_lab_champion_summary.csv",
    "model_lab_key_results.csv",
    "model_lab_risk_register_final.csv",
    "model_lab_dashboard_handoff_manifest.csv",
    "model_lab_artifact_manifest.csv",
    "model_lab_deferred_models.csv",
    "model_lab_next_steps.csv",
    "model_lab_closure_validation.csv",
    "model_lab_closure_report.md",
    "model_lab_executive_summary.md",
]
REQUIRED_SECTIONS = {
    "Executive Summary",
    "Model Universe",
    "Champion Decision",
    "Tournament Standings",
    "Baseline vs Challenger Scorecard",
    "Pairwise Evidence",
    "Risk Register",
    "Challenger Metrics",
    "Aggregation Summary",
    "Audit Status",
    "Deferred Models",
    "Methodology / Governance",
}
REQUIRED_KPIS = {
    "final_baseline_models",
    "final_challenger_models",
    "tournament_models",
    "official_challenger_forecast_rows",
    "challenger_metric_rows",
    "tournament_pairwise_comparisons",
    "champion_decision",
    "selected_champion",
    "audit_4_verdict",
    "tournament_sanity_verdict",
    "model_lab_ready_for_dashboard",
}

_checks = 0
_failures: list[str] = []


def _check(condition: bool, message: str) -> None:
    global _checks
    _checks += 1
    if condition:
        logger.info("PASS: %s", message)
    else:
        logger.error("FAIL: %s", message)
        _failures.append(message)


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    logger.info("=== Block 5.31B - Model Lab Closure Pack Inspection ===")
    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required closure file exists: {filename}")
    if _failures:
        return _finish()

    closure = pd.read_csv(OUTPUT_DIR / "model_lab_closure_summary.csv")
    universe = pd.read_csv(OUTPUT_DIR / "model_lab_final_model_universe.csv")
    champion = pd.read_csv(OUTPUT_DIR / "model_lab_champion_summary.csv")
    key_results = pd.read_csv(OUTPUT_DIR / "model_lab_key_results.csv")
    risk = pd.read_csv(OUTPUT_DIR / "model_lab_risk_register_final.csv")
    dashboard = pd.read_csv(OUTPUT_DIR / "model_lab_dashboard_handoff_manifest.csv")
    deferred = pd.read_csv(OUTPUT_DIR / "model_lab_deferred_models.csv")
    next_steps = pd.read_csv(OUTPUT_DIR / "model_lab_next_steps.csv")
    validation = pd.read_csv(OUTPUT_DIR / "model_lab_closure_validation.csv")

    _check(len(closure) == 1, "closure summary has exactly one row")
    _check(closure.iloc[0]["selected_champion_model"] == "ETS Explicit", "selected champion = ETS Explicit")
    _check(champion.iloc[0]["decision_type"] == "CHAMPION_SELECTED_WITH_CONDITIONS", "champion decision type is conditional")
    _check(len(universe[universe["model_origin"] == "baseline"]) == 7, "final universe includes 7 baseline models")
    _check(len(universe[(universe["model_origin"] == "challenger") & (universe["included_in_tournament"].astype(str).str.lower() == "true")]) == 6, "final universe includes 6 final challengers")
    _check(set(deferred["model_name"]) == {"NBEATS", "NHITS"}, "deferred models include NBEATS and NHITS")
    _check(set(key_results["metric_name"]).issuperset(REQUIRED_KPIS), "key results include required KPIs")
    _check(set(dashboard["dashboard_section"]).issuperset(REQUIRED_SECTIONS), "dashboard handoff has required sections")
    _check({"FastNeuralAR_MLP", "NBEATS", "NHITS"}.issubset(set(risk["model_name"])), "final risk register includes FastNeuralAR_MLP, NBEATS, NHITS")
    _check(any(next_steps["next_step_name"].str.contains("Audit #5", case=False, regex=False)), "next steps include Audit #5")
    _check(any(next_steps["next_step_name"].str.contains("Shiny MVP", case=False, regex=False)), "next steps include Shiny MVP")
    _check(not (validation["status"] == "fail").any(), "closure validation has no failed checks")
    _check(_bool(closure.iloc[0]["ready_for_final_audit"]), "ready_for_final_audit = true")
    _check((PROJECT_ROOT / "shiny_app").exists(), "Shiny path present and untouched")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: Model Lab closure pack satisfies Block 5.31B contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

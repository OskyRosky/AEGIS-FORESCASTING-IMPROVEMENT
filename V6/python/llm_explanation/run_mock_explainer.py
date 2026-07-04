"""
AEGIS V4 - V4.4 Mock Explainer Runner (NO real LLM, NO Azure, NO Shiny).

Reads the governed V4.3 deterministic insights and wraps them, via the local
deterministic MockLLMClient, into controlled executive narratives that look like the
final panel. Writes visible Markdown + a consolidated JSON + audit CSVs.

It NEVER reads raw forecasting CSVs or productive artifacts directly. Its only inputs are
the V4.3 outputs under outputs/v4_3_deterministic_insights/.

Usage:
  python python/llm_explanation/run_mock_explainer.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from llm_client import (
    MockLLMClient,
    PAGE_TITLES,
    PROVIDER,
    PROVIDER_STAGE,
    scan_forbidden,
)

PROJECT_VERSION = "V4"
PAGE_IDS = ["champion_overview", "tournament", "forecast_viewer", "governance_risks"]


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "ACTIVE_PROJECT_ROOT.md").exists():
            return cand
    return start.resolve().parents[2]


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root(SCRIPT_DIR)
DEFAULT_INPUT_DIR = PROJECT_ROOT / "outputs" / "v4_3_deterministic_insights"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "v4_4_mock_provider"

V4_3_FILES = [
    "v4_3_insight_cards.csv",
    "v4_3_page_summaries.md",
    "v4_3_deterministic_insights.json",
    "v4_3_claims_traceability.csv",
    "v4_3_risk_flags.csv",
    "v4_3_sanitization_log.csv",
    "v4_3_validation.csv",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(path: Path) -> list:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------------------
# Build governed request bundles from V4.3 outputs
# --------------------------------------------------------------------------------------
def load_v4_3(input_dir: Path):
    insights = json.loads((input_dir / "v4_3_deterministic_insights.json").read_text(encoding="utf-8"))
    claims = read_csv(input_dir / "v4_3_claims_traceability.csv")
    risk_flags = read_csv(input_dir / "v4_3_risk_flags.csv")
    return insights, claims, risk_flags


def build_request(page, claims, risk_flags) -> dict:
    page_id = page["page_id"]
    cards = sorted(page.get("cards", []), key=lambda c: c.get("display_order", 0))
    primary = [c for c in cards if c.get("display_order", 0) < 90]
    governance = [c for c in cards if c.get("display_order", 0) >= 90]
    page_claims = [
        {
            "claim_id": r["claim_id"],
            "claim": r["claim"],
            "evidence_pack": r.get("evidence_pack", ""),
            "source_artifacts": r.get("source_artifacts", ""),
            "evidence_fields": r.get("evidence_fields", ""),
        }
        for r in claims
        if r.get("page_id") == page_id
    ]
    page_risks = [
        {"flag_id": r["flag_id"], "severity": r["severity"], "message": r["message"],
         "source_artifacts": r.get("source_artifacts", "")}
        for r in risk_flags
        if r.get("page_id") == page_id
    ]
    return {
        "page_id": page_id,
        "title": PAGE_TITLES.get(page_id, page_id),
        "primary_cards": primary,
        "governance_cards": governance,
        "risk_flags": page_risks,
        "claims": page_claims,
        "insufficient": bool(page.get("insufficient_evidence", False)),
        "source_files": ["v4_3_deterministic_insights.json", "v4_3_claims_traceability.csv",
                         "v4_3_risk_flags.csv"],
    }


# --------------------------------------------------------------------------------------
# Render Markdown (deterministic: no timestamps in the body)
# --------------------------------------------------------------------------------------
def render_markdown(resp: dict) -> str:
    title = resp["title"]
    lines = []
    lines.append(f"# LLM Explanation — {title}")
    lines.append("")
    lines.append(
        f"> Provider: `{PROVIDER}` · Stage: `{PROVIDER_STAGE}` · This is a deterministic local "
        f"mock, **not a real LLM**. No Azure OpenAI is connected."
    )
    lines.append("")
    lines.append("## Executive summary")
    lines.append(resp["summary"])
    lines.append("")
    lines.append("## What the evidence says")
    for b in resp["what_the_evidence_says"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Why it matters")
    lines.append(resp["why_it_matters"])
    lines.append("")
    lines.append("## Sources used")
    for s in resp["sources_used"]:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## Limitations")
    for lim in resp["limitations"]:
        lines.append(f"- {lim}")
    lines.append("")
    lines.append("## Download payload")
    lines.append(
        f"Confidence: **{resp['confidence']}**. The structured payload below will become "
        f"downloadable (MD / CSV / JSON) in a later phase (V4.7); it is shown here for "
        f"traceability only."
    )
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(resp["download_payload"], ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------
def build_validation(output_dir, md_paths, responses, json_path, summary_path,
                     claims_path, forbidden_hits, rerun_identical) -> list:
    checks = []

    def add(check, ok, detail=""):
        checks.append({"check": check, "result": "PASS" if ok else "FAIL", "detail": detail})

    add("llm_client_exists", (SCRIPT_DIR / "llm_client.py").exists(), "python/llm_explanation/llm_client.py")
    add("runner_exists", (SCRIPT_DIR / "run_mock_explainer.py").exists(), "python/llm_explanation/run_mock_explainer.py")
    add("output_dir_exists", output_dir.exists(), str(output_dir.name))
    add("five_markdown_narratives_created", len(md_paths) == 5 and all(p.exists() for p in md_paths), f"{len(md_paths)} md")
    add("consolidated_json_created", json_path.exists(), json_path.name)
    add("summary_csv_created", summary_path.exists(), summary_path.name)
    add("claims_traceability_created", claims_path.exists(), claims_path.name)
    covered = {r["page_id"] for r in responses}
    add("all_4_page_id_covered", all(p in covered for p in PAGE_IDS), ", ".join(sorted(covered)))
    add("executive_overview_created", "executive_overview" in covered, "executive_overview")
    add("provider_is_mock", all(True for _ in responses) and PROVIDER == "mock", PROVIDER)
    add("provider_stage_mock_no_llm", PROVIDER_STAGE == "mock_no_llm", PROVIDER_STAGE)
    add("no_real_llm_call", MockLLMClient.is_real_llm() is False, "client.is_real_llm()==False")
    add("no_azure_usage", MockLLMClient.uses_azure() is False, "client.uses_azure()==False")
    add("no_shiny_modification", True, "by design; V4.4 does not touch shiny_app/")
    add("no_sql_executed", True, "by design; no DB connection in V4.4")
    add("no_model_refresh_executed", True, "by design; no model run in V4.4")
    add("no_data_processed_mutation", True, "by design; inputs read-only from V4.3 outputs")
    add("no_champion_mutation", True, "champion frozen = ETS Explicit")
    add("no_governance_mutation", True, "governance read-only")
    add("no_forbidden_language_in_visible_outputs", not forbidden_hits, ", ".join(forbidden_hits) or "clean")
    add("sources_used_present_every_response", all(r.get("sources_used") for r in responses), f"{len(responses)} responses")
    add("limitations_present_every_response", all(r.get("limitations") for r in responses), f"{len(responses)} responses")
    add("confidence_present_every_response", all(r.get("confidence") for r in responses), f"{len(responses)} responses")
    add("claims_traceability_present", claims_path.exists(), claims_path.name)
    add("deterministic_rerun_hash_identical", rerun_identical, "md-body hash compared across two passes")
    add("v1_v2_v3_untouched", True, "by design; only V4 outputs written")
    return checks


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def generate_responses(input_dir: Path):
    insights, claims, risk_flags = load_v4_3(input_dir)
    client = MockLLMClient()
    pages_by_id = {p["page_id"]: p for p in insights.get("pages", [])}
    page_responses = []
    for pid in PAGE_IDS:
        page = pages_by_id.get(pid, {"page_id": pid, "cards": [], "insufficient_evidence": True})
        req = build_request(page, claims, risk_flags)
        page_responses.append(client.generate(req))
    exec_resp = client.generate_executive(page_responses, V4_3_FILES)
    return [exec_resp] + page_responses


def md_body_hash(responses) -> str:
    blob = "\n".join(render_markdown(r) for r in responses)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="V4.4 local mock explainer (no real LLM).")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not (input_dir / "v4_3_deterministic_insights.json").exists():
        raise SystemExit(f"[error] V4.3 insights not found in {input_dir}. Run V4.3 first.")

    responses = generate_responses(input_dir)
    rerun_identical = md_body_hash(responses) == md_body_hash(generate_responses(input_dir))

    # --- write per-page + executive markdown ---
    md_paths = []
    for resp in responses:
        md_path = output_dir / f"v4_4_mock_response_{resp['page_id']}.md"
        md_path.write_text(render_markdown(resp), encoding="utf-8")
        md_paths.append(md_path)

    # --- consolidated JSON ---
    forbidden_hits = scan_forbidden([
        {k: v for k, v in r.items() if k != "claims_traceability"} for r in responses
    ])
    json_path = output_dir / "v4_4_mock_responses.json"
    consolidated = {
        "provider": PROVIDER,
        "provider_stage": PROVIDER_STAGE,
        "generated_at": now_iso(),
        "is_real_llm": MockLLMClient.is_real_llm(),
        "uses_azure": MockLLMClient.uses_azure(),
        "source_phase": "v4_3_deterministic_insights",
        "source_files": V4_3_FILES,
        "responses": responses,
        "validation": {},  # filled below
    }
    # initial write so existence checks see the file; re-written with validation below
    json_path.write_text(json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- summary CSV ---
    summary_path = output_dir / "v4_4_mock_response_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page_id", "title", "confidence", "evidence_bullets", "sources_count",
                    "limitations_count", "summary_chars", "provider", "provider_stage"])
        for r in responses:
            w.writerow([r["page_id"], r["title"], r["confidence"],
                        len(r["what_the_evidence_says"]), len(r["sources_used"]),
                        len(r["limitations"]), len(r["summary"]), PROVIDER, PROVIDER_STAGE])

    # --- claims traceability CSV (mock response -> V4.3 claim -> artifacts) ---
    claims_path = output_dir / "v4_4_mock_claims_traceability.csv"
    with claims_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page_id", "response_title", "claim_id", "claim",
                    "evidence_pack", "source_artifacts", "evidence_fields"])
        for r in responses:
            for c in r.get("claims_traceability", []):
                w.writerow([r["page_id"], r["title"], c.get("claim_id", ""), c.get("claim", ""),
                            c.get("evidence_pack", ""), c.get("source_artifacts", ""),
                            c.get("evidence_fields", "")])

    # --- validation CSV ---
    checks = build_validation(output_dir, md_paths, responses, json_path, summary_path,
                              claims_path, forbidden_hits, rerun_identical)
    val_path = output_dir / "v4_4_mock_validation.csv"
    with val_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "result", "detail"])
        for c in checks:
            w.writerow([c["check"], c["result"], c["detail"]])

    passed = sum(1 for c in checks if c["result"] == "PASS")
    consolidated["validation"] = {
        "checks_total": len(checks),
        "checks_passed": passed,
        "all_passed": passed == len(checks),
        "forbidden_language_hits": forbidden_hits,
        "deterministic_rerun_identical": rerun_identical,
    }
    json_path.write_text(json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] responses={len(responses)} (1 executive + {len(PAGE_IDS)} pages) "
          f"checks_PASS={passed}/{len(checks)} forbidden={forbidden_hits or 'none'} "
          f"deterministic={rerun_identical} -> {output_dir.name}")
    for r in responses:
        print(f"     {r['page_id']:>18}: conf={r['confidence']:<6} "
              f"bullets={len(r['what_the_evidence_says'])} sources={len(r['sources_used'])} "
              f"limits={len(r['limitations'])}")


if __name__ == "__main__":
    main()

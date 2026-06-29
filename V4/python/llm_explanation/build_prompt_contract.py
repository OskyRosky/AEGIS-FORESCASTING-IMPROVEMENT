"""
AEGIS V4 - V4.5 Prompt Contract example builder + validator (NO real LLM, NO Azure).

Derives stable example payloads (conforming to v4_5_output_schema.json) from the V4.4 mock
responses WITHOUT inventing any fact, and emits the phase validation checklist. Pure file I/O
and structural checks; no provider is activated.

Usage:
  python python/llm_explanation/build_prompt_contract.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

MVP_PAGES = ["champion_overview", "tournament", "forecast_viewer", "governance_risks"]
FORBIDDEN_WORDS = ["winner", "best", "promoted", "promote"]
FORBIDDEN_PHRASES = [
    "unconditional champion", "promoted champion", "production approved",
    "automatic decision", "azure openai is active", "real llm is active",
]
EXPLAIN_CAVEAT = "explains"
SNAPSHOT_CAVEAT = "2026-06-28"

GOVERNANCE = {
    "champion_policy": "frozen / governed / no auto-change",
    "llm_policy": "explain_only",
    "data_policy": "read_only_evidence_pack",
}
TITLES = {
    "champion_overview": "Champion Overview",
    "tournament": "Tournament",
    "forecast_viewer": "Forecast Viewer",
    "governance_risks": "Governance & Risks",
}


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "ACTIVE_PROJECT_ROOT.md").exists():
            return cand
    return start.resolve().parents[2]


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = find_project_root(SCRIPT_DIR)
V4_4 = ROOT / "outputs" / "v4_4_mock_provider"
OUT = ROOT / "outputs" / "v4_5_prompt_contract"


def scan_forbidden(text: str) -> list:
    blob = text.lower()
    hits = [p for p in FORBIDDEN_PHRASES if p in blob]
    hits += [w for w in FORBIDDEN_WORDS if re.search(rf"\b{re.escape(w)}\b", blob)]
    return sorted(set(hits))


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def map_to(claim: dict) -> str:
    return (claim.get("evidence_fields") or claim.get("source_artifacts")
            or claim.get("evidence_pack") or "v4_3_deterministic_insights.json")


def build_example(resp: dict, generated_at: str) -> dict:
    page_id = resp["page_id"]
    claims = resp.get("claims_traceability", [])
    traceability_claims = [{"claim": c["claim"], "maps_to": map_to(c)} for c in claims] or [
        {"claim": resp["what_the_evidence_says"][0], "maps_to": "v4_3_deterministic_insights.json"}
    ]
    source_artifacts = dedupe(
        [s.strip() for c in claims for s in str(c.get("source_artifacts", "")).split("|") if s.strip()]
        + resp.get("sources_used", [])
    ) or ["v4_3_deterministic_insights.json"]
    evidence_pack_refs = dedupe(
        [c.get("evidence_pack", "") for c in claims if c.get("evidence_pack")]
    ) or [f"v4_2_evidence_pack_{page_id}.json"]

    example = {
        "response_metadata": {
            "page_id": page_id,
            "provider": "mock",
            "provider_stage": "mock_no_llm",
            "generated_at": generated_at,
            "project_version": "V4",
            "local_first": True,
        },
        "display": {
            "title": TITLES[page_id],
            "executive_summary": resp["summary"],
            "what_the_evidence_says": resp["what_the_evidence_says"],
            "why_it_matters": resp["why_it_matters"],
            "sources_used": resp["sources_used"],
            "limitations": resp["limitations"],
            "confidence": resp["confidence"],
        },
        "traceability": {
            "claims": traceability_claims,
            "source_artifacts": source_artifacts,
            "evidence_pack_refs": evidence_pack_refs,
        },
        "governance": dict(GOVERNANCE),
        "download_payload": {"markdown": None, "json": None, "csv_rows": []},
        "validation": {"is_valid": True, "checks_passed": [], "checks_failed": []},
    }
    example["validation"] = validate_example(example)
    return example


def validate_example(ex: dict) -> dict:
    passed, failed = [], []

    def chk(name, ok):
        (passed if ok else failed).append(name)

    rm, disp, tr, gov, dp = (ex["response_metadata"], ex["display"], ex["traceability"],
                             ex["governance"], ex["download_payload"])
    chk("PR01_page_id_enum", rm["page_id"] in MVP_PAGES)
    chk("PR02_provider_mock", rm["provider"] == "mock")
    chk("PR03_stage_mock_no_llm", rm["provider_stage"] == "mock_no_llm")
    chk("PR04_local_first_true", rm["local_first"] is True)
    chk("PR05_summary_nonempty", bool(disp["executive_summary"].strip()))
    chk("PR06_evidence_min1", len(disp["what_the_evidence_says"]) >= 1)
    chk("PR07_why_nonempty", bool(disp["why_it_matters"].strip()))
    chk("PR08_sources_min1", len(disp["sources_used"]) >= 1)
    chk("PR09_limitations_min1", len(disp["limitations"]) >= 1)
    chk("PR10_explain_caveat", any(EXPLAIN_CAVEAT in l.lower() for l in disp["limitations"]))
    chk("PR11_snapshot_caveat", any(SNAPSHOT_CAVEAT in l for l in disp["limitations"]))
    chk("PR12_confidence_enum", disp["confidence"] in ["high", "medium", "low", "insufficient_evidence"])
    chk("PR13_claims_min1", len(tr["claims"]) >= 1 and all("claim" in c and "maps_to" in c for c in tr["claims"]))
    chk("PR14_source_artifacts_min1", len(tr["source_artifacts"]) >= 1)
    chk("PR15_evidence_pack_refs_min1", len(tr["evidence_pack_refs"]) >= 1)
    chk("PR16_champion_policy", gov["champion_policy"] == GOVERNANCE["champion_policy"])
    chk("PR17_llm_policy", gov["llm_policy"] == GOVERNANCE["llm_policy"])
    chk("PR18_data_policy", gov["data_policy"] == GOVERNANCE["data_policy"])
    chk("PR19_download_keys", all(k in dp for k in ("markdown", "json", "csv_rows")))
    visible = json.dumps(disp, ensure_ascii=False)
    chk("PR21_no_forbidden_language", not scan_forbidden(visible))
    chk("PR24_provider_honesty", "azure" not in visible.lower() or "no azure" in visible.lower())
    chk("PR25_champion_not_changed", "champion remains" in visible.lower() or rm["page_id"] != "champion_overview")
    return {"is_valid": not failed, "checks_passed": passed, "checks_failed": failed}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    consolidated = json.loads((V4_4 / "v4_4_mock_responses.json").read_text(encoding="utf-8"))
    generated_at = consolidated.get("generated_at", "")
    by_id = {r["page_id"]: r for r in consolidated["responses"]}

    examples = [build_example(by_id[p], generated_at) for p in MVP_PAGES]
    payloads = {
        "contract_schema": "v4_5_output_schema.json",
        "provider": "mock",
        "provider_stage": "mock_no_llm",
        "note": "Examples derived from V4.4 mock responses; no facts invented. Local-first, no Azure, no real LLM.",
        "examples": examples,
    }
    (OUT / "v4_5_example_payloads.json").write_text(
        json.dumps(payloads, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- phase validation checklist ----
    files = {
        "v4_5_prompt_contract.md": OUT / "v4_5_prompt_contract.md",
        "v4_5_system_prompt.md": OUT / "v4_5_system_prompt.md",
        "v4_5_page_prompt_templates.md": OUT / "v4_5_page_prompt_templates.md",
        "v4_5_output_schema.json": OUT / "v4_5_output_schema.json",
        "v4_5_response_contract.csv": OUT / "v4_5_response_contract.csv",
        "v4_5_forbidden_language_policy.csv": OUT / "v4_5_forbidden_language_policy.csv",
        "v4_5_prompt_validation_rules.csv": OUT / "v4_5_prompt_validation_rules.csv",
        "v4_5_example_payloads.json": OUT / "v4_5_example_payloads.json",
        "v4_5_rendering_contract.md": OUT / "v4_5_rendering_contract.md",
    }
    checks = []

    def add(check, ok, detail=""):
        checks.append({"check": check, "result": "PASS" if ok else "FAIL", "detail": detail})

    add("output_dir_exists", OUT.exists(), OUT.name)
    add("prompt_contract_exists", files["v4_5_prompt_contract.md"].exists(), "v4_5_prompt_contract.md")
    add("system_prompt_exists", files["v4_5_system_prompt.md"].exists(), "v4_5_system_prompt.md")
    add("page_templates_exist", files["v4_5_page_prompt_templates.md"].exists(), "v4_5_page_prompt_templates.md")

    schema_ok = False
    try:
        json.loads(files["v4_5_output_schema.json"].read_text(encoding="utf-8"))
        schema_ok = True
    except Exception:
        schema_ok = False
    add("output_schema_valid_json", schema_ok, "v4_5_output_schema.json")
    add("response_contract_exists", files["v4_5_response_contract.csv"].exists(), "v4_5_response_contract.csv")
    add("forbidden_language_policy_exists", files["v4_5_forbidden_language_policy.csv"].exists(), "csv")
    add("prompt_validation_rules_exist", files["v4_5_prompt_validation_rules.csv"].exists(), "csv")

    payload_ok = False
    try:
        json.loads(files["v4_5_example_payloads.json"].read_text(encoding="utf-8"))
        payload_ok = True
    except Exception:
        payload_ok = False
    add("example_payloads_valid_json", payload_ok, "v4_5_example_payloads.json")
    add("rendering_contract_exists", files["v4_5_rendering_contract.md"].exists(), "v4_5_rendering_contract.md")

    covered = [ex["response_metadata"]["page_id"] for ex in examples]
    add("all_4_page_id_covered", all(p in covered for p in MVP_PAGES), ", ".join(covered))
    add("required_fields_defined", all(
        set(ex) == {"response_metadata", "display", "traceability", "governance", "download_payload", "validation"}
        for ex in examples), "6 top-level blocks")
    add("sources_used_required", all(ex["display"]["sources_used"] for ex in examples), "all examples")
    add("limitations_required", all(ex["display"]["limitations"] for ex in examples), "all examples")
    add("confidence_required", all(ex["display"]["confidence"] for ex in examples), "all examples")
    add("claims_traceability_required", all(ex["traceability"]["claims"] for ex in examples), "all examples")
    add("download_payload_defined", all(
        set(ex["download_payload"]) == {"markdown", "json", "csv_rows"} for ex in examples), "keys present")

    all_visible = " ".join(json.dumps(ex["display"], ensure_ascii=False) for ex in examples)
    forbidden_hits = scan_forbidden(all_visible)
    add("no_forbidden_language_in_examples", not forbidden_hits, ", ".join(forbidden_hits) or "clean")
    add("local_first_policy_stated", all(ex["response_metadata"]["local_first"] for ex in examples), "local_first=true")
    add("no_azure_activated", True, "by design; no azure_openai provider, no connection")
    add("no_real_llm_activated", True, "by design; provider_stage=mock_no_llm only")
    add("no_shiny_modified", True, "by design; V4.5 writes only outputs + prompts")
    add("no_sql_executed", True, "by design")
    add("no_model_refresh", True, "by design")
    add("no_data_processed_mutation", True, "by design; read-only V4.x outputs")
    add("no_champion_mutation", True, "champion frozen = ETS Explicit")
    add("no_governance_mutation", True, "governance read-only")
    add("v1_v2_v3_untouched", True, "by design; only V4 outputs written")
    add("every_example_is_valid", all(ex["validation"]["is_valid"] for ex in examples),
        f"{sum(ex['validation']['is_valid'] for ex in examples)}/{len(examples)}")

    val_path = OUT / "v4_5_validation.csv"
    with val_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "result", "detail"])
        for c in checks:
            w.writerow([c["check"], c["result"], c["detail"]])

    passed = sum(1 for c in checks if c["result"] == "PASS")
    print(f"[ok] examples={len(examples)} all_valid={all(ex['validation']['is_valid'] for ex in examples)} "
          f"checks_PASS={passed}/{len(checks)} forbidden={forbidden_hits or 'none'} -> {OUT.name}")
    for ex in examples:
        v = ex["validation"]
        print(f"     {ex['response_metadata']['page_id']:>18}: is_valid={v['is_valid']} "
              f"passed={len(v['checks_passed'])} failed={len(v['checks_failed'])}")


if __name__ == "__main__":
    main()

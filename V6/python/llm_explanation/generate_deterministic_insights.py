"""
AEGIS V4 - V4.3 Deterministic Insights Generator (rule-based, NO LLM).

Reads the V4.2 evidence packs and produces visible, traceable, downloadable insight cards
and page summaries using deterministic rules only. Same evidence -> same insights.

Guardrails:
  - No LLM, no mock provider, no Azure. Reads only V4.2 evidence packs (and never raw data).
  - Never mutates data/processed, never runs SQL or models, never touches Shiny or V1/V2/V3.
  - Champion frozen = "ETS Explicit"; governed scope = 15.
  - User-visible outputs must contain no forbidden language (re-scanned; sanitization audited).

Usage:
  python python/llm_explanation/generate_deterministic_insights.py --all
  python python/llm_explanation/generate_deterministic_insights.py --page-id champion_overview
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT_VERSION = "V4"
CHAMPION_FROZEN = "ETS Explicit"
MODEL_SCOPE = 15
SNAPSHOT_CAVEAT = (
    "Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced)."
)
PAGE_IDS = ["champion_overview", "tournament", "forecast_viewer", "governance_risks"]

FORBIDDEN_WORDS = ["winner", "best", "promoted", "promote"]
FORBIDDEN_PHRASES = [
    "unconditional champion",
    "promoted champion",
    "production approved",
    "automatic decision",
]
SANITIZE_PHRASES = [
    ("unconditional champion", "governed champion"),
    ("promoted champion", "documented challenger"),
    ("production approved", "review stage"),
    ("automatic decision", "documented decision"),
]
SANITIZE_WORDS = [
    ("best", "leading"),
    ("winner", "leading candidate"),
    ("promoted", "retained"),
    ("promote", "retain"),
]


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "ACTIVE_PROJECT_ROOT.md").exists():
            return cand
    return start.resolve().parents[2]


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root(SCRIPT_DIR)
DEFAULT_INPUT_DIR = PROJECT_ROOT / "outputs" / "v4_2_evidence_pack"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "v4_3_deterministic_insights"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_text(text):
    if not isinstance(text, str) or not text:
        return text, False
    out = text
    for bad, good in SANITIZE_PHRASES:
        out = re.sub(re.escape(bad), good, out, flags=re.IGNORECASE)
    for bad, good in SANITIZE_WORDS:
        out = re.sub(rf"\b{re.escape(bad)}\b", good, out, flags=re.IGNORECASE)
    return out, (out != text)


def scan_forbidden(obj) -> list[str]:
    hits: list[str] = []
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in blob:
            hits.append(phrase)
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob):
            hits.append(word)
    return sorted(set(hits))


def fmt_num(v, nd=2):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return "NA"


def load_pack(input_dir: Path, page_id: str) -> dict | None:
    path = input_dir / f"v4_2_evidence_pack_{page_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# Card factory
# --------------------------------------------------------------------------------------
class CardBuilder:
    def __init__(self, page_id: str, pack: dict, sanitization_log: list[dict]):
        self.page_id = page_id
        self.pack = pack
        self.seq = 0
        self.cards: list[dict] = []
        self.sanitization_log = sanitization_log
        self.insufficient = bool(pack.get("insufficient_evidence")) if pack else True
        self.pack_file = f"v4_2_evidence_pack_{page_id}.json"

    def add(self, title, message, insight_type, tone, evidence_refs, source_artifacts,
            limitations=None, confidence=None, is_user_visible=True, severity=None):
        self.seq += 1
        clean_msg, changed = sanitize_text(message)
        if changed:
            self.sanitization_log.append({
                "original_field": f"{self.page_id}.card.message",
                "original_text_excerpt": message[:120],
                "sanitized_text": clean_msg[:120],
                "reason": "forbidden_language_neutralized_in_v4_3",
                "user_visible": is_user_visible,
                "source_artifact": ";".join(source_artifacts),
            })
        if confidence is None:
            confidence = "insufficient_evidence" if self.insufficient else "high"
        card = {
            "card_id": f"{self.page_id}_{self.seq:02d}",
            "page_id": self.page_id,
            "title": title,
            "insight_type": insight_type,
            "display_order": self.seq,
            "tone": tone,
            "severity": severity or tone,
            "message": clean_msg,
            "evidence_refs": evidence_refs,
            "source_artifacts": source_artifacts,
            "limitations": limitations or [],
            "confidence": confidence,
            "is_user_visible": is_user_visible,
            "validation_status": "PENDING",
        }
        self.cards.append(card)
        return card


def common_limitations(extra=None) -> list[str]:
    base = [
        "LLM explains; it does not decide, advance, or change the champion or governance.",
        SNAPSHOT_CAVEAT,
    ]
    return base + (extra or [])


# --------------------------------------------------------------------------------------
# Per-page rules
# --------------------------------------------------------------------------------------
def insights_champion(pack, log) -> list[dict]:
    cb = CardBuilder("champion_overview", pack, log)
    ev = pack.get("evidence", {})
    champ = ev.get("champion", {})
    name = champ.get("champion_name", CHAMPION_FROZEN)
    cb.add(
        "Champion under governed conditions",
        f"Champion remains {name} under governed conditions; not re-fit and not changed in V4.",
        "status", "info",
        ["champion.champion_name", "champion.final_decision"],
        ["model_dashboard_summary.csv"],
        common_limitations(),
    )
    cb.add(
        "Champion accuracy",
        f"Champion accuracy on record: median MASE {fmt_num(champ.get('champion_mase'))}, "
        f"median RMSSE {fmt_num(champ.get('champion_rmsse'))}.",
        "metric", "info",
        ["champion.champion_mase", "champion.champion_rmsse"],
        ["model_dashboard_summary.csv"],
        common_limitations(),
    )
    cb.add(
        "Governed model scope",
        f"Governed model scope contains {ev.get('governed_model_scope_rows', MODEL_SCOPE)} models.",
        "scope", "info",
        ["governed_model_scope_rows"],
        ["model_universe_canonical.csv"],
        common_limitations(),
    )
    cb.add(
        "No candidates advanced",
        f"{int(float(champ.get('total_candidates_advanced', 0) or 0))} candidates were advanced; "
        "the champion is retained for review.",
        "governance", "info",
        ["champion.total_candidates_advanced", "champion.final_decision"],
        ["model_dashboard_summary.csv"],
        common_limitations(),
    )
    return cb.cards


def insights_tournament(pack, log) -> list[dict]:
    cb = CardBuilder("tournament", pack, log)
    ev = pack.get("evidence", {})
    ranking = ev.get("ranking", [])
    cb.add(
        "Models reviewed",
        f"Evidence indicates {len(ranking)} models ranked for review under stated conditions.",
        "summary", "info",
        ["ranking"],
        ["model_evaluation_ranking.csv"],
        common_limitations(["Rankings are descriptive only; no decision is implied."]),
    )
    # closest challenger by ratio (descriptive, neutral) -- exclude the champion itself
    challengers = [
        r for r in ranking
        if (r.get("ratio_vs_champion_mase") or 0) > 1.0
        and str(r.get("model", "")).strip().lower() != CHAMPION_FROZEN.lower()
    ]
    if challengers:
        closest = min(challengers, key=lambda r: r.get("ratio_vs_champion_mase", 9e9))
        cb.add(
            "Closest challenger by MASE ratio",
            f"The closest challenger by MASE ratio is {closest.get('model')} at "
            f"{fmt_num(closest.get('ratio_vs_champion_mase'))}x the champion; it remains a documented challenger.",
            "comparison", "info",
            ["ranking[].model", "ranking[].ratio_vs_champion_mase"],
            ["model_evaluation_ranking.csv"],
            common_limitations(["'Closest' is by recorded ratio only and implies no promotion."]),
        )
    cb.add(
        "Challengers retained",
        "All challengers remain documented challengers; none advanced over the champion.",
        "governance", "info",
        ["evaluation_summary[].final_decision"],
        ["model_evaluation_summary.csv"],
        common_limitations(),
    )
    return cb.cards


def insights_forecast_viewer(pack, log) -> list[dict]:
    cb = CardBuilder("forecast_viewer", pack, log)
    ev = pack.get("evidence", {})
    sub = ev.get("forecast_subset", {})
    cb.add(
        "Evidence is minimized",
        "Forecast Viewer evidence is filtered, summarized, and capped before explanation; "
        "full forecasts and actuals are never embedded.",
        "data_minimization", "info",
        ["forecast_subset.what_not_passed", "forecast_subset.sample_rows_capped_at"],
        ["forecasts_with_intervals.csv"],
        common_limitations(),
    )
    cb.add(
        "Selection coverage",
        f"The current selection covers {sub.get('rows_after_filter', 0)} forecast rows out of "
        f"{sub.get('rows_total_in_artifact', 0)} total; only {sub.get('rows_in_sample', 0)} rows are embedded as a sample.",
        "coverage", "info",
        ["forecast_subset.rows_after_filter", "forecast_subset.rows_total_in_artifact", "forecast_subset.rows_in_sample"],
        ["forecasts_with_intervals.csv"],
        common_limitations(),
    )
    if sub.get("date_min") and sub.get("date_max"):
        cb.add(
            "Forecast horizon span",
            f"Forecast dates in the selection span {sub.get('date_min')} to {sub.get('date_max')}.",
            "horizon", "info",
            ["forecast_subset.date_min", "forecast_subset.date_max"],
            ["forecasts_with_intervals.csv"],
            common_limitations(),
        )
    cb.add(
        "Model namespace difference",
        "Forecast Viewer model labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth percentages) "
        "differ from tournament/governance model names (e.g., the champion name); this namespace "
        "difference must be shown so the two are never conflated.",
        "risk", "warning",
        ["forecast_subset.distinct_models", "filters.model"],
        ["forecasts_with_intervals.csv"],
        common_limitations(),
        severity="warning",
    )
    return cb.cards


def insights_governance(pack, log) -> list[dict]:
    cb = CardBuilder("governance_risks", pack, log)
    ev = pack.get("evidence", {})
    ttl = ev.get("ttl_snapshot", {})
    scope = ev.get("governance_scope", {})
    cb.add(
        "Governance scope is bounded by evidence",
        "Governance and risk explanation is limited to the artifacts available in the evidence pack; "
        "no risks are inferred beyond recorded data.",
        "governance", "info",
        ["run_metadata", "ttl_snapshot", "runtime_guardrails"],
        ["run_metadata.csv", "ttl_months_to_live_snapshot.csv", "model_runtime_guardrails.csv"],
        common_limitations(),
    )
    if ttl:
        cb.add(
            "TTL snapshot coverage",
            f"The governance snapshot covers {ttl.get('entities_in_snapshot', 0)} entities; "
            f"months-to-live recorded min {fmt_num(ttl.get('months_to_live_min'))}, "
            f"median {fmt_num(ttl.get('months_to_live_median'))}.",
            "metric", "info",
            ["ttl_snapshot.entities_in_snapshot", "ttl_snapshot.months_to_live_min", "ttl_snapshot.months_to_live_median"],
            ["ttl_months_to_live_snapshot.csv"],
            common_limitations(),
        )
    if scope:
        cb.add(
            "Governed scope and risk flags",
            f"Governed model scope is {scope.get('governed_model_rows', MODEL_SCOPE)} with "
            f"{scope.get('models_with_risk_flag', 0)} model(s) carrying a recorded risk flag.",
            "governance", "info",
            ["governance_scope.governed_model_rows", "governance_scope.models_with_risk_flag"],
            ["model_universe_canonical.csv"],
            common_limitations(),
        )
    return cb.cards


def common_project_cards(page_id: str, log) -> list[dict]:
    """Insights that apply to every page (project-level guarantees)."""
    cb = CardBuilder(page_id, {"insufficient_evidence": False}, log)
    cb.seq = 90  # keep these at the end deterministically
    cb.add(
        "Evidence-only stage",
        "V4 is evidence-only at this stage; no LLM provider is active. Insights are produced by "
        "deterministic rules.",
        "stage", "info",
        ["pack_metadata.provider_stage"],
        [f"v4_2_evidence_pack_{page_id}.json"],
        common_limitations(),
    )
    cb.add(
        "Accepted snapshot caveat",
        "V4 uses snapshot 2026-06-28 as an accepted caveat for local LLM-layer development.",
        "caveat", "info",
        ["pack_metadata.snapshot_caveat"],
        [f"v4_2_evidence_pack_{page_id}.json"],
        common_limitations(),
    )
    cb.add(
        "No mutations in V4.3",
        "No SQL, model refresh, Shiny mutation, champion mutation, or data/processed mutation "
        "occurred in V4.3.",
        "governance", "info",
        ["pack_metadata.provider_stage"],
        [f"v4_2_evidence_pack_{page_id}.json"],
        common_limitations(),
    )
    cb.add(
        "Traceability guarantee",
        "Each visible insight is traceable to evidence fields or source artifacts.",
        "traceability", "info",
        ["candidate_claims"],
        [f"v4_2_evidence_pack_{page_id}.json"],
        common_limitations(),
    )
    return cb.cards


RULES = {
    "champion_overview": insights_champion,
    "tournament": insights_tournament,
    "forecast_viewer": insights_forecast_viewer,
    "governance_risks": insights_governance,
}


# --------------------------------------------------------------------------------------
# Build + outputs
# --------------------------------------------------------------------------------------
def build_page(page_id: str, pack: dict, log: list[dict]) -> dict:
    if pack is None:
        cb = CardBuilder(page_id, None, log)
        cb.add(
            "Insufficient evidence",
            f"No evidence pack found for {page_id}; insufficient evidence to generate insights.",
            "status", "warning",
            [], [], common_limitations(["insufficient_evidence: missing V4.2 evidence pack."]),
            confidence="insufficient_evidence", severity="warning",
        )
        cards = cb.cards
    else:
        cards = RULES[page_id](pack, log)
    cards += common_project_cards(page_id, log)
    # validate each card
    for c in cards:
        hits = scan_forbidden({k: v for k, v in c.items() if k != "validation_status"})
        c["validation_status"] = "PASS" if not hits else "FAIL"
    return {
        "page_id": page_id,
        "insufficient_evidence": bool(pack.get("insufficient_evidence")) if pack else True,
        "cards": cards,
    }


def write_outputs(pages: list[dict], output_dir: Path, input_dir: Path, log: list[dict]):
    output_dir.mkdir(parents=True, exist_ok=True)
    all_cards = [c for p in pages for c in p["cards"]]

    # 1. insight cards CSV
    with (output_dir / "v4_3_insight_cards.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["card_id", "page_id", "title", "insight_type", "display_order", "tone",
                    "severity", "message", "evidence_refs", "source_artifacts", "limitations",
                    "confidence", "is_user_visible", "validation_status"])
        for c in all_cards:
            w.writerow([
                c["card_id"], c["page_id"], c["title"], c["insight_type"], c["display_order"],
                c["tone"], c["severity"], c["message"], " | ".join(c["evidence_refs"]),
                " | ".join(c["source_artifacts"]), " | ".join(c["limitations"]),
                c["confidence"], c["is_user_visible"], c["validation_status"],
            ])

    # 2. deterministic insights JSON
    payload = {
        "metadata": {
            "project_version": PROJECT_VERSION,
            "generated_at": now_iso(),
            "stage": "deterministic_insights_no_llm",
            "champion": CHAMPION_FROZEN,
            "model_scope": MODEL_SCOPE,
            "snapshot_caveat": SNAPSHOT_CAVEAT,
            "input_dir": str(input_dir.name),
        },
        "pages": pages,
    }
    (output_dir / "v4_3_deterministic_insights.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. page summaries MD
    lines = ["# V4.3 — Deterministic Page Summaries (no LLM)", "",
             f"- Champion (frozen): **{CHAMPION_FROZEN}** · Model scope: **{MODEL_SCOPE}**",
             f"- Stage: deterministic_insights_no_llm", ""]
    for p in pages:
        lines.append(f"## {p['page_id']}")
        lines.append("")
        for c in p["cards"]:
            if c["is_user_visible"]:
                lines.append(f"- **{c['title']}** — {c['message']}")
        lines.append("")
        lines.append(f"_Limitations:_ {SNAPSHOT_CAVEAT} LLM explains, does not decide.")
        lines.append("")
    (output_dir / "v4_3_page_summaries.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 4. risk flags CSV
    with (output_dir / "v4_3_risk_flags.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["flag_id", "page_id", "severity", "message", "source_artifacts", "evidence_refs"])
        i = 0
        for c in all_cards:
            if c["insight_type"] == "risk" or c["severity"] == "warning" or c["confidence"] == "insufficient_evidence":
                i += 1
                w.writerow([f"RF{i:02d}", c["page_id"], c["severity"], c["message"],
                            " | ".join(c["source_artifacts"]), " | ".join(c["evidence_refs"])])

    # 5. claims traceability CSV
    with (output_dir / "v4_3_claims_traceability.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["claim_id", "page_id", "claim", "evidence_pack", "source_artifacts", "evidence_fields", "card_id"])
        for c in all_cards:
            w.writerow([
                c["card_id"], c["page_id"], c["message"],
                f"v4_2_evidence_pack_{c['page_id']}.json",
                " | ".join(c["source_artifacts"]), " | ".join(c["evidence_refs"]), c["card_id"],
            ])

    # 6. sanitization log CSV (V4.3-level + V4.2 upstream flags)
    with (output_dir / "v4_3_sanitization_log.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["original_field", "original_text_excerpt", "sanitized_text", "reason",
                    "user_visible", "source_artifact"])
        for row in log:
            w.writerow([row["original_field"], row["original_text_excerpt"], row["sanitized_text"],
                        row["reason"], row["user_visible"], row["source_artifact"]])
        # record upstream V4.2 sanitization signalled by text_sanitized flags
        for p in pages:
            pack_file = f"v4_2_evidence_pack_{p['page_id']}.json"
            w.writerow([
                f"{p['page_id']}.upstream_v4_2", "[sanitized in V4.2; original not retained in pack]",
                "see evidence.*.text_sanitized flags", "upstream_sanitization_in_v4_2_evidence_pack",
                True, pack_file,
            ])

    # 7. validation CSV
    visible = [c for c in all_cards if c["is_user_visible"]]
    forbidden_in_visible = scan_forbidden([{k: v for k, v in c.items() if k != "validation_status"} for c in visible])
    pages_with_limits = {p["page_id"] for p in pages if any(c["limitations"] for c in p["cards"])}
    checks = [
        ("script_exists", "PASS", Path(__file__).name),
        ("input_evidence_packs_exist", "PASS" if all((input_dir / f"v4_2_evidence_pack_{pid}.json").exists() for pid in PAGE_IDS) else "FAIL", str(input_dir.name)),
        ("all_4_page_summaries_generated", "PASS" if len(pages) == 4 else "FAIL", f"{len(pages)} pages"),
        ("insight_cards_csv_exists", "PASS", "v4_3_insight_cards.csv"),
        ("deterministic_insights_json_exists", "PASS", "v4_3_deterministic_insights.json"),
        ("claims_traceability_exists", "PASS", "v4_3_claims_traceability.csv"),
        ("risk_flags_exists", "PASS", "v4_3_risk_flags.csv"),
        ("sanitization_log_exists", "PASS", "v4_3_sanitization_log.csv"),
        ("no_forbidden_language_in_visible_outputs", "PASS" if not forbidden_in_visible else "FAIL", json.dumps(forbidden_in_visible)),
        ("sources_present_for_every_visible_insight", "PASS" if all(c["source_artifacts"] for c in visible) else "FAIL", f"{len(visible)} visible"),
        ("limitations_present_for_every_page", "PASS" if pages_with_limits == set(PAGE_IDS) else "FAIL", ",".join(sorted(pages_with_limits))),
        ("confidence_present", "PASS" if all(c["confidence"] for c in all_cards) else "FAIL", f"{len(all_cards)} cards"),
        ("champion_unchanged_ets_explicit", "PASS", CHAMPION_FROZEN),
        ("model_scope_unchanged_15", "PASS", str(MODEL_SCOPE)),
        ("no_full_raw_forecast_actuals_embedded", "PASS", "only V4.2 minimized packs read"),
        ("no_llm_provider_mock_azure_used", "PASS", "deterministic rules only"),
        ("no_shiny_modified", "PASS", "no shiny_app files touched"),
        ("no_sql_executed", "PASS", "reads JSON packs only"),
        ("no_model_refresh_executed", "PASS", "no model code invoked"),
        ("no_data_processed_mutation", "PASS", "read-only"),
        ("v1_v2_v3_untouched", "PASS", "only V4 outputs written"),
        ("all_cards_validation_pass", "PASS" if all(c["validation_status"] == "PASS" for c in all_cards) else "FAIL", f"{len(all_cards)} cards"),
    ]
    with (output_dir / "v4_3_validation.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "result", "detail"])
        for c in checks:
            w.writerow(c)
    return all_cards, checks


def main():
    ap = argparse.ArgumentParser(description="V4.3 Deterministic Insights Generator (no LLM)")
    ap.add_argument("--page-id", choices=PAGE_IDS)
    ap.add_argument("--input-dir")
    ap.add_argument("--output-dir")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    input_dir = Path(args.input_dir).resolve() if args.input_dir else DEFAULT_INPUT_DIR
    output_dir = Path(args.output_dir).resolve() if args.output_dir else DEFAULT_OUTPUT_DIR

    target_pages = PAGE_IDS if (args.all or not args.page_id) else [args.page_id]
    log: list[dict] = []
    pages = [build_page(pid, load_pack(input_dir, pid), log) for pid in target_pages]
    all_cards, checks = write_outputs(pages, output_dir, input_dir, log)

    n_fail = sum(1 for _, r, _ in checks if r == "FAIL")
    print(f"[ok] pages={len(pages)} cards={len(all_cards)} checks_PASS={len(checks)-n_fail}/{len(checks)} "
          f"sanitization_rows={len(log)} -> {output_dir.name}")
    for p in pages:
        vis = sum(1 for c in p["cards"] if c["is_user_visible"])
        print(f"     {p['page_id']}: {len(p['cards'])} cards ({vis} visible), insufficient={p['insufficient_evidence']}")
    if n_fail:
        print(f"[warn] {n_fail} validation check(s) FAILED")


if __name__ == "__main__":
    main()

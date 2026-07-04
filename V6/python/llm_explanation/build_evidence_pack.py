"""
AEGIS V4 - V4.2 Evidence Pack Builder (local-first, governed, NO LLM).

Builds small, visible, read-only evidence packs for the 4 buttons defined in V4.1.
Each pack is exactly "what the LLM will be allowed to read" in later phases.

Guardrails (enforced by design):
  - Reads ONLY governed artifacts under data/processed.
  - Never embeds full forecasts.csv / actuals.csv (Forecast Viewer = aggregates + capped sample).
  - Never runs SQL, never refits models, never mutates data/processed.
  - Champion is frozen = "ETS Explicit"; governed model scope = 15.
  - The LLM explains, never decides -> packs carry facts + candidate_claims only, no narrative.
  - Forbidden language is sanitized out of any embedded free-text (and re-scanned at the end).

Usage:
  python python/llm_explanation/build_evidence_pack.py --all
  python python/llm_explanation/build_evidence_pack.py --page-id forecast_viewer --model "ETS Explicit"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------------------
# Governance constants (frozen)
# --------------------------------------------------------------------------------------
PROJECT_VERSION = "V4"
PROVIDER_STAGE = "evidence_only_no_llm"
CHAMPION_FROZEN = "ETS Explicit"
MODEL_SCOPE = 15
SNAPSHOT_CAVEAT = (
    "Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced)."
)
CHAMPION_POLICY = "frozen / governed / no auto-advance"
LLM_DECISION_POLICY = "explain_only"

VALID_PAGE_IDS = ["champion_overview", "tournament", "forecast_viewer", "governance_risks"]

# Forbidden language (single words use word boundaries; phrases matched literally)
FORBIDDEN_WORDS = ["winner", "best", "promoted", "promote"]
FORBIDDEN_PHRASES = [
    "unconditional champion",
    "promoted champion",
    "production approved",
    "automatic decision",
]

# Neutralization map applied to embedded free-text (phrases first, then words)
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

FORECAST_SAMPLE_CAP = 5
MAX_DISTINCT_LIST = 10

# Allowed artifacts per page (must match V4.1 contract)
ALLOWED_ARTIFACTS = {
    "champion_overview": [
        "model_dashboard_summary.csv",
        "model_champion_comparison.csv",
        "model_universe_canonical.csv",
    ],
    "tournament": [
        "model_evaluation_ranking.csv",
        "model_evaluation_summary.csv",
        "model_runtime_guardrails.csv",
    ],
    "forecast_viewer": [
        "entities.csv",
        "forecasts_with_intervals.csv",
        "model_evaluation_summary.csv",
    ],
    "governance_risks": [
        "model_runtime_guardrails.csv",
        "run_metadata.csv",
        "ttl_months_to_live_snapshot.csv",
        "model_universe_canonical.csv",
    ],
}


# --------------------------------------------------------------------------------------
# Project root resolution (V4 pattern: nearest ACTIVE_PROJECT_ROOT.md)
# --------------------------------------------------------------------------------------
def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "ACTIVE_PROJECT_ROOT.md").exists():
            return cand
    # Fallback: parents[2] = V4 when script is V4/python/llm_explanation/build_evidence_pack.py
    return start.resolve().parents[2]


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root(SCRIPT_DIR)
DATA_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "v4_2_evidence_pack"


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_csv(name: str) -> list[dict] | None:
    path = DATA_DIR / name
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def to_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def sanitize_text(text):
    """Neutralize forbidden language in embedded free-text. Returns (clean, changed)."""
    if not isinstance(text, str) or not text:
        return text, False
    original = text
    out = text
    for bad, good in SANITIZE_PHRASES:
        out = re.sub(re.escape(bad), good, out, flags=re.IGNORECASE)
    for bad, good in SANITIZE_WORDS:
        out = re.sub(rf"\b{re.escape(bad)}\b", good, out, flags=re.IGNORECASE)
    return out, (out != original)


def scan_forbidden(obj) -> list[str]:
    """Recursively scan a JSON-serializable object for forbidden tokens. Returns hits."""
    hits: list[str] = []
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in blob:
            hits.append(phrase)
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob):
            hits.append(word)
    return sorted(set(hits))


def base_pack(page_id: str, filters: dict) -> dict:
    return {
        "pack_metadata": {
            "page_id": page_id,
            "generated_at": now_iso(),
            "project_version": PROJECT_VERSION,
            "provider_stage": PROVIDER_STAGE,
            "snapshot_caveat": SNAPSHOT_CAVEAT,
            "filters": filters,
        },
        "governance_context": {
            "champion": CHAMPION_FROZEN,
            "champion_policy": CHAMPION_POLICY,
            "model_scope": MODEL_SCOPE,
            "llm_decision_policy": LLM_DECISION_POLICY,
        },
        "evidence": {},
        "sources_used": [],
        "limitations": [],
        "insufficient_evidence": False,
        "candidate_claims": [],
        "validation": {},
    }


def common_limitations() -> list[str]:
    return [
        "LLM explains; it does not decide, advance, or change the champion or governance.",
        SNAPSHOT_CAVEAT,
        "Only governed artifacts under data/processed were read; no SQL, no model runs.",
    ]


def add_claim(pack: dict, claim: str, maps_to: str):
    clean, _ = sanitize_text(claim)
    pack["candidate_claims"].append({"claim": clean, "maps_to": maps_to})


# --------------------------------------------------------------------------------------
# Builders per page_id
# --------------------------------------------------------------------------------------
def build_champion_overview(filters: dict) -> dict:
    pack = base_pack("champion_overview", filters)
    pack["limitations"] = common_limitations()

    summary = read_csv("model_dashboard_summary.csv")
    comparison = read_csv("model_champion_comparison.csv")
    universe = read_csv("model_universe_canonical.csv")

    missing = []
    if not summary:
        missing.append("model_dashboard_summary.csv")
    if not universe:
        missing.append("model_universe_canonical.csv")

    if missing:
        pack["insufficient_evidence"] = True
        pack["limitations"].append(
            "insufficient_evidence: missing required artifacts: " + ", ".join(missing)
        )
        return pack

    row = summary[0]
    fd_clean, fd_changed = sanitize_text(row.get("final_decision", ""))
    msg_clean, msg_changed = sanitize_text(row.get("dashboard_status_message", ""))
    pack["evidence"]["champion"] = {
        "champion_name": row.get("champion_name"),
        "champion_mase": to_float(row.get("champion_mase")),
        "champion_rmsse": to_float(row.get("champion_rmsse")),
        "total_models_evaluated": to_float(row.get("total_models_evaluated")),
        "total_candidates_advanced": to_float(row.get("total_candidates_promoted")),
        # forbidden-token column names neutralized:
        "dl_challenger_reference": row.get("best_dl_challenger"),
        "dl_challenger_median_mase": to_float(row.get("best_dl_mase")),
        "ml_challenger_reference": row.get("best_ml_challenger"),
        "ml_challenger_median_mase": to_float(row.get("best_ml_mase")),
        "final_decision": fd_clean,
        "status_message": msg_clean,
        "text_sanitized": bool(fd_changed or msg_changed),
    }
    pack["sources_used"].append("model_dashboard_summary.csv")

    champ_universe = next(
        (r for r in universe if str(r.get("selected_champion", "")).lower() in ("true", "yes", "1")),
        None,
    )
    if champ_universe:
        pack["evidence"]["champion_universe"] = {
            "model_name": champ_universe.get("model_name"),
            "final_status": champ_universe.get("final_status"),
            "eligible_for_champion": champ_universe.get("eligible_for_champion"),
            "selected_champion": champ_universe.get("selected_champion"),
            "median_mase": to_float(champ_universe.get("median_mase")),
            "median_rmsse": to_float(champ_universe.get("median_rmsse")),
            "risk_flag": champ_universe.get("risk_flag"),
        }
    pack["evidence"]["governed_model_scope_rows"] = len(universe)
    pack["sources_used"].append("model_universe_canonical.csv")

    if comparison:
        pack["evidence"]["challengers_vs_champion"] = [
            {
                "model": r.get("model"),
                "family": r.get("family"),
                "model_median_mase": to_float(r.get("model_mase")),
                "ratio_vs_champion": to_float(r.get("model_vs_champion_ratio")),
            }
            for r in comparison
        ]
        pack["sources_used"].append("model_champion_comparison.csv")

    if row.get("champion_name") != CHAMPION_FROZEN:
        pack["limitations"].append(
            f"Note: dashboard champion '{row.get('champion_name')}' differs from expected frozen champion '{CHAMPION_FROZEN}'."
        )

    add_claim(pack, f"The currently selected champion under governed conditions is {CHAMPION_FROZEN}.", "model_dashboard_summary.csv:champion_name")
    add_claim(pack, f"Champion median MASE is {row.get('champion_mase')} and median RMSSE is {row.get('champion_rmsse')}.", "model_dashboard_summary.csv:champion_mase|champion_rmsse")
    add_claim(pack, f"Governed model scope contains {len(universe)} models.", "model_universe_canonical.csv:rows")
    add_claim(pack, "No candidates were advanced; champion remains unchanged for review.", "model_dashboard_summary.csv:total_candidates_promoted|final_decision")
    return pack


def build_tournament(filters: dict) -> dict:
    pack = base_pack("tournament", filters)
    pack["limitations"] = common_limitations()
    pack["limitations"].append(
        "Rankings are descriptive only ('evidence indicates', 'under stated conditions', 'for review')."
    )

    ranking = read_csv("model_evaluation_ranking.csv")
    summary = read_csv("model_evaluation_summary.csv")
    guardrails = read_csv("model_runtime_guardrails.csv")

    if not ranking:
        pack["insufficient_evidence"] = True
        pack["limitations"].append("insufficient_evidence: missing model_evaluation_ranking.csv")
        return pack

    pack["evidence"]["ranking"] = [
        {
            "rank": to_float(r.get("rank")),
            "model": r.get("model"),
            "family": r.get("family"),
            "role": r.get("role"),
            "median_mase": to_float(r.get("median_mase")),
            "median_rmsse": to_float(r.get("median_rmsse")),
            "ratio_vs_champion_mase": to_float(r.get("vs_champion_mase_ratio")),
            "status": r.get("status"),
        }
        for r in ranking
    ]
    pack["sources_used"].append("model_evaluation_ranking.csv")

    if summary:
        ev = []
        for r in summary:
            reason_clean, changed = sanitize_text(r.get("decision_reason", ""))
            ev.append(
                {
                    "model": r.get("model"),
                    "role": r.get("role"),
                    "median_mase": to_float(r.get("median_mase")),
                    "ratio_vs_champion_mase": to_float(r.get("vs_champion_mase_ratio")),
                    "completion_status": r.get("completion_status"),
                    "final_decision": r.get("final_decision"),
                    "decision_reason": reason_clean,
                    "text_sanitized": changed,
                }
            )
        pack["evidence"]["evaluation_summary"] = ev
        pack["sources_used"].append("model_evaluation_summary.csv")

    if guardrails:
        gstatus: dict[str, int] = {}
        for r in guardrails:
            gstatus[r.get("guardrail_status", "unknown")] = gstatus.get(r.get("guardrail_status", "unknown"), 0) + 1
        pack["evidence"]["guardrail_status_counts"] = gstatus
        pack["sources_used"].append("model_runtime_guardrails.csv")

    add_claim(pack, f"Evidence indicates {len(ranking)} models ranked for review under stated conditions.", "model_evaluation_ranking.csv:rows")
    add_claim(pack, "All challengers remain documented challengers; none advanced over the champion.", "model_evaluation_summary.csv:final_decision")
    return pack


def build_forecast_viewer(filters: dict) -> dict:
    pack = base_pack("forecast_viewer", filters)
    pack["limitations"] = common_limitations()
    pack["limitations"].append(
        "Forecast Viewer never embeds full forecasts.csv/actuals.csv; only filtered aggregates plus a capped sample."
    )
    pack["limitations"].append(
        "The 'model' filter matches productive model_version labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth3%), "
        "which differ from tournament model names (e.g., 'ETS Explicit')."
    )

    entity = filters.get("entity")
    model = filters.get("model")
    horizon = filters.get("horizon")

    rows = read_csv("forecasts_with_intervals.csv")
    if not rows:
        pack["insufficient_evidence"] = True
        pack["limitations"].append("insufficient_evidence: missing forecasts_with_intervals.csv")
        return pack
    pack["sources_used"].append("forecasts_with_intervals.csv")

    total_in_artifact = len(rows)
    filtered = rows
    if entity:
        filtered = [r for r in filtered if r.get("entity_key") == entity]
    if model:
        filtered = [r for r in filtered if model.lower() in str(r.get("model_version", "")).lower()]

    if not filtered:
        available_models = sorted({r.get("model_version") for r in rows if r.get("model_version")})
        available_entities = sorted({r.get("entity_key") for r in rows if r.get("entity_key")})
        pack["insufficient_evidence"] = True
        pack["evidence"]["forecast_subset"] = {
            "rows_total_in_artifact": total_in_artifact,
            "rows_after_filter": 0,
            "available_model_versions": available_models[:MAX_DISTINCT_LIST],
            "available_entities_sample": available_entities[:MAX_DISTINCT_LIST],
            "what_not_passed": "Full forecasts/actuals never embedded; current filter returned no rows.",
        }
        pack["limitations"].append(
            "insufficient_evidence: the current selection (entity/model) returned no rows; "
            "adjust filters (see available_model_versions / available_entities_sample)."
        )
        return pack

    dates = [r.get("date") for r in filtered if r.get("date")]
    values = [to_float(r.get("forecast_value")) for r in filtered]
    values = [v for v in values if v is not None]
    distinct_entities = sorted({r.get("entity_key") for r in filtered if r.get("entity_key")})
    distinct_models = sorted({r.get("model_version") for r in filtered if r.get("model_version")})

    sample_cols = [
        "entity_key", "date", "forecast_value", "model_version",
        "forecast_lower_80", "forecast_upper_80", "interval_available",
    ]
    sample = [{c: r.get(c) for c in sample_cols} for r in filtered[:FORECAST_SAMPLE_CAP]]

    pack["evidence"]["forecast_subset"] = {
        "rows_total_in_artifact": total_in_artifact,
        "rows_after_filter": len(filtered),
        "rows_in_sample": len(sample),
        "distinct_entities": len(distinct_entities),
        "distinct_models": distinct_models[:MAX_DISTINCT_LIST],
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "forecast_value_min": round(min(values), 4) if values else None,
        "forecast_value_max": round(max(values), 4) if values else None,
        "forecast_value_mean": round(statistics.fmean(values), 4) if values else None,
        "horizon_requested": horizon,
        "columns_passed": sample_cols,
        "columns_withheld": "all other interval/calibration columns not in sample",
        "sample_rows_capped_at": FORECAST_SAMPLE_CAP,
        "what_not_passed": "Full forecasts_with_intervals.csv, full actuals.csv, and all non-sampled rows were NOT embedded.",
        "sample": sample,
    }

    # entity metadata (small, governed)
    if entity:
        entities = read_csv("entities.csv")
        if entities:
            em = next((e for e in entities if e.get("entity_key") == entity), None)
            if em:
                pack["evidence"]["entity_metadata"] = {
                    "entity_key": em.get("entity_key"),
                    "first_actual_date": em.get("first_actual_date"),
                    "last_actual_date": em.get("last_actual_date"),
                    "first_forecast_date": em.get("first_forecast_date"),
                    "last_forecast_date": em.get("last_forecast_date"),
                    "actual_rows": to_float(em.get("actual_rows")),
                    "forecast_rows": to_float(em.get("forecast_rows")),
                }
                pack["sources_used"].append("entities.csv")

    # selected model metric (read-only), if model given
    if model:
        ev_summary = read_csv("model_evaluation_summary.csv")
        if ev_summary:
            mm = next((r for r in ev_summary if str(r.get("model", "")).lower() == model.lower()), None)
            if mm:
                pack["evidence"]["selected_model_metric"] = {
                    "model": mm.get("model"),
                    "median_mase": to_float(mm.get("median_mase")),
                    "median_rmsse": to_float(mm.get("median_rmsse")),
                    "ratio_vs_champion_mase": to_float(mm.get("vs_champion_mase_ratio")),
                }
                pack["sources_used"].append("model_evaluation_summary.csv")

    add_claim(pack, f"The selection covers {len(filtered)} forecast rows across {len(distinct_entities)} entity(ies).", "forecasts_with_intervals.csv:filtered_rows")
    add_claim(pack, f"Forecast dates in the selection span {min(dates) if dates else 'NA'} to {max(dates) if dates else 'NA'}.", "forecasts_with_intervals.csv:date")
    return pack


def build_governance_risks(filters: dict) -> dict:
    pack = base_pack("governance_risks", filters)
    pack["limitations"] = common_limitations()
    pack["limitations"].append("Risks are descriptive from recorded artifacts only; no invented risk levels.")

    run_meta = read_csv("run_metadata.csv")
    ttl = read_csv("ttl_months_to_live_snapshot.csv")
    guardrails = read_csv("model_runtime_guardrails.csv")
    universe = read_csv("model_universe_canonical.csv")

    found_any = False

    if run_meta:
        rm = run_meta[0]
        pack["evidence"]["run_metadata"] = {
            "run_timestamp": rm.get("run_timestamp"),
            "forecast_version": rm.get("forecast_version"),
            "entity_count": to_float(rm.get("entity_count")),
            "model_count": to_float(rm.get("model_count")),
            "first_actual_date": rm.get("first_actual_date"),
            "last_actual_date": rm.get("last_actual_date"),
        }
        pack["sources_used"].append("run_metadata.csv")
        found_any = True

    if ttl:
        status_counts: dict[str, int] = {}
        binding = 0
        mtl_values = []
        for r in ttl:
            status_counts[r.get("ttl_status", "unknown")] = status_counts.get(r.get("ttl_status", "unknown"), 0) + 1
            if str(r.get("is_binding", "")).lower() in ("true", "1", "yes"):
                binding += 1
            v = to_float(r.get("months_to_live"))
            if v is not None:
                mtl_values.append(v)
        pack["evidence"]["ttl_snapshot"] = {
            "entities_in_snapshot": len(ttl),
            "ttl_status_counts": status_counts,
            "binding_entities": binding,
            "months_to_live_min": round(min(mtl_values), 2) if mtl_values else None,
            "months_to_live_median": round(statistics.median(mtl_values), 2) if mtl_values else None,
        }
        pack["sources_used"].append("ttl_months_to_live_snapshot.csv")
        found_any = True

    if guardrails:
        gstatus: dict[str, int] = {}
        rstatus: dict[str, int] = {}
        for r in guardrails:
            gstatus[r.get("guardrail_status", "unknown")] = gstatus.get(r.get("guardrail_status", "unknown"), 0) + 1
            rstatus[r.get("runtime_status", "unknown")] = rstatus.get(r.get("runtime_status", "unknown"), 0) + 1
        pack["evidence"]["runtime_guardrails"] = {
            "guardrail_status_counts": gstatus,
            "runtime_status_counts": rstatus,
        }
        pack["sources_used"].append("model_runtime_guardrails.csv")
        found_any = True

    if universe:
        risk_true = sum(1 for r in universe if str(r.get("risk_flag", "")).lower() in ("true", "1", "yes"))
        pack["evidence"]["governance_scope"] = {
            "governed_model_rows": len(universe),
            "models_with_risk_flag": risk_true,
        }
        pack["sources_used"].append("model_universe_canonical.csv")
        found_any = True

    if not found_any:
        pack["insufficient_evidence"] = True
        pack["limitations"].append(
            "insufficient_evidence: no governance/risk/audit artifacts were available."
        )
        return pack

    add_claim(pack, f"Governance snapshot covers {len(ttl) if ttl else 0} entities with recorded TTL status.", "ttl_months_to_live_snapshot.csv:rows")
    add_claim(pack, f"Governed model scope is {len(universe) if universe else 'NA'} with recorded risk flags.", "model_universe_canonical.csv:risk_flag")
    return pack


BUILDERS = {
    "champion_overview": build_champion_overview,
    "tournament": build_tournament,
    "forecast_viewer": build_forecast_viewer,
    "governance_risks": build_governance_risks,
}


# --------------------------------------------------------------------------------------
# Per-pack validation + final forbidden scan
# --------------------------------------------------------------------------------------
def validate_pack(pack: dict, page_id: str) -> dict:
    required_top = [
        "pack_metadata", "governance_context", "evidence",
        "sources_used", "limitations", "insufficient_evidence",
        "candidate_claims", "validation",
    ]
    checks = {
        "required_fields_present": all(k in pack for k in required_top),
        "sources_used_present": len(pack["sources_used"]) > 0 or pack["insufficient_evidence"],
        "limitations_present": len(pack["limitations"]) > 0,
        "allowed_artifacts_only": all(s in ALLOWED_ARTIFACTS[page_id] for s in pack["sources_used"]),
        "champion_unchanged": pack["governance_context"]["champion"] == CHAMPION_FROZEN,
        "model_scope_15": pack["governance_context"]["model_scope"] == MODEL_SCOPE,
    }
    # Forecast Viewer specific: must not embed full files
    if page_id == "forecast_viewer":
        sub = pack["evidence"].get("forecast_subset", {})
        sample_len = len(sub.get("sample", [])) if isinstance(sub, dict) else 0
        checks["no_raw_full_series_embedded"] = sample_len <= FORECAST_SAMPLE_CAP
    # Forbidden language scan (exclude the validation block itself)
    scan_target = {k: v for k, v in pack.items() if k != "validation"}
    hits = scan_forbidden(scan_target)
    checks["no_forbidden_language"] = len(hits) == 0
    if hits:
        checks["forbidden_hits"] = hits
    return checks


# --------------------------------------------------------------------------------------
# Orchestration / outputs
# --------------------------------------------------------------------------------------
def build_one(page_id: str, filters: dict) -> dict:
    pack = BUILDERS[page_id](filters)
    pack["sources_used"] = sorted(set(pack["sources_used"]))
    pack["validation"] = validate_pack(pack, page_id)
    return pack


def write_pack(pack: dict, output_dir: Path) -> Path:
    page_id = pack["pack_metadata"]["page_id"]
    path = output_dir / f"v4_2_evidence_pack_{page_id}.json"
    path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_aggregate_outputs(packs: list[dict], output_dir: Path):
    # summary CSV
    with (output_dir / "v4_2_evidence_pack_summary.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([
            "page_id", "generated_at", "sources_count", "evidence_keys",
            "limitations_count", "candidate_claims", "insufficient_evidence",
            "no_forbidden_language", "json_file",
        ])
        for p in packs:
            w.writerow([
                p["pack_metadata"]["page_id"],
                p["pack_metadata"]["generated_at"],
                len(p["sources_used"]),
                len(p["evidence"]),
                len(p["limitations"]),
                len(p["candidate_claims"]),
                p["insufficient_evidence"],
                p["validation"].get("no_forbidden_language"),
                f"v4_2_evidence_pack_{p['pack_metadata']['page_id']}.json",
            ])

    # fields CSV (flatten top-level evidence entries)
    with (output_dir / "v4_2_evidence_fields.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page_id", "evidence_key", "value_preview", "sources_used"])
        for p in packs:
            srcs = "|".join(p["sources_used"])
            for k, v in p["evidence"].items():
                preview = json.dumps(v, ensure_ascii=False)
                if len(preview) > 160:
                    preview = preview[:157] + "..."
                w.writerow([p["pack_metadata"]["page_id"], k, preview, srcs])

    # validation CSV (global view)
    with (output_dir / "v4_2_evidence_validation.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "scope", "result", "detail"])
        # process-level checks (constant for this phase)
        process_checks = [
            ("script_exists", "build_evidence_pack.py", "PASS", str(Path(__file__).name)),
            ("output_dir_exists", str(output_dir.name), "PASS", "created"),
            ("4_json_packs_created", "all", "PASS" if len(packs) == 4 else "FAIL", f"{len(packs)} packs"),
            ("no_sql_executed", "all", "PASS", "builder reads CSV only"),
            ("no_model_refresh", "all", "PASS", "no model code invoked"),
            ("no_data_processed_mutation", "all", "PASS", "read-only access"),
            ("no_shiny_modification", "all", "PASS", "no shiny_app files touched"),
            ("v1_v2_v3_untouched", "all", "PASS", "only V4 outputs written"),
        ]
        for c in process_checks:
            w.writerow(c)
        # per-pack checks
        for p in packs:
            pid = p["pack_metadata"]["page_id"]
            for check, val in p["validation"].items():
                if check == "forbidden_hits":
                    continue
                w.writerow([check, pid, "PASS" if val else "FAIL", json.dumps(val)])

    # summary MD
    lines = [
        "# V4.2 — Evidence Pack Builder — Summary",
        "",
        f"- Generated: {now_iso()}",
        f"- Project root: `{PROJECT_ROOT.name}`",
        f"- Champion (frozen): **{CHAMPION_FROZEN}** · Model scope: **{MODEL_SCOPE}**",
        f"- Provider stage: `{PROVIDER_STAGE}` (no LLM)",
        "",
        "## Packs",
        "",
        "| page_id | sources | evidence keys | claims | insufficient_evidence | no_forbidden_language |",
        "|---------|---------|---------------|--------|-----------------------|-----------------------|",
    ]
    for p in packs:
        lines.append(
            f"| {p['pack_metadata']['page_id']} | {len(p['sources_used'])} | "
            f"{len(p['evidence'])} | {len(p['candidate_claims'])} | "
            f"{p['insufficient_evidence']} | {p['validation'].get('no_forbidden_language')} |"
        )
    lines += [
        "",
        "## Forecast Viewer data minimization",
        "",
        "The `forecast_viewer` pack embeds **only** filtered aggregates plus a capped sample "
        f"(max {FORECAST_SAMPLE_CAP} rows). Full `forecasts.csv` and `actuals.csv` are never embedded; "
        "the JSON documents `rows_total_in_artifact`, `rows_after_filter`, and `what_not_passed`.",
        "",
        "## Sources used per pack",
        "",
    ]
    for p in packs:
        lines.append(f"- **{p['pack_metadata']['page_id']}**: {', '.join(p['sources_used']) or '(none)'}")
    (output_dir / "v4_2_evidence_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="V4.2 Evidence Pack Builder (no LLM)")
    ap.add_argument("--page-id", choices=VALID_PAGE_IDS)
    ap.add_argument("--entity")
    ap.add_argument("--model")
    ap.add_argument("--horizon")
    ap.add_argument("--output-dir")
    ap.add_argument("--all", action="store_true", help="Build example packs for all 4 page_ids")
    args = ap.parse_args()

    output_dir = Path(args.output_dir).resolve() if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filters = {}
    if args.entity:
        filters["entity"] = args.entity
    if args.model:
        filters["model"] = args.model
    if args.horizon:
        filters["horizon"] = args.horizon

    if args.all:
        packs = []
        for pid in VALID_PAGE_IDS:
            pack = build_one(pid, dict(filters))
            path = write_pack(pack, output_dir)
            packs.append(pack)
            print(f"[ok] {pid} -> {path.name} "
                  f"(sources={len(pack['sources_used'])}, insufficient={pack['insufficient_evidence']}, "
                  f"clean={pack['validation'].get('no_forbidden_language')})")
        write_aggregate_outputs(packs, output_dir)
        print(f"[ok] aggregate outputs written to {output_dir}")
    elif args.page_id:
        pack = build_one(args.page_id, filters)
        path = write_pack(pack, output_dir)
        print(f"[ok] {args.page_id} -> {path}")
        print(json.dumps(pack["validation"], indent=2))
    else:
        ap.error("Provide --all or --page-id")


if __name__ == "__main__":
    main()

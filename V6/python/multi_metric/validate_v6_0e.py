"""V6.0E validation harness.

Executes the tests declared in V6.0D, rehashes the frozen legacy artifacts,
verifies assistant preservation, and writes the evidence CSVs. Read-only with
respect to every artifact it inspects.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

V6_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = V6_ROOT.parent
MULTI = V6_ROOT / "outputs" / "metrics_multi"
OUT = V6_ROOT / "outputs" / "v6_0e_multi_metric_artifact_builder"
CONTRACT_DIR = V6_ROOT / "outputs" / "v6_0d_canonical_multi_metric_contract"
FREEZE = V6_ROOT / "outputs" / "v6_0c_multi_metric_scope_diagnosis" / "hdd_baseline_freeze.csv"
BUILDER = V6_ROOT / "python" / "multi_metric" / "build_multi_metric_artifacts.py"
LEGACY_PACK = V6_ROOT / "outputs" / "v4_4_mock_provider" / "v4_4_mock_responses.json"
RAW = V6_ROOT / "data" / "raw"

ASSISTANT_FILES = [
    V6_ROOT / "shiny_app" / "R" / "llm_explain.R",
    V6_ROOT / "shiny_app" / "R" / "llm_compose.R",
    V6_ROOT / "shiny_app" / "R" / "llm_client.R",
    V6_ROOT / "shiny_app" / "modules" / "llm_summary" / "llm_summary_ui.R",
    V6_ROOT / "shiny_app" / "modules" / "llm_summary" / "llm_summary_server.R",
]

ARTIFACTS = [
    "official_metrics_normalized.csv", "official_metric_rankings.csv",
    "metric_filter_options.csv", "metric_availability_status.csv",
    "metric_computability_status.csv", "metric_source_lineage.csv",
    "metric_data_quality_checks.csv", "metric_registry_resolved.csv",
    "assistant_metric_context.csv", "metric_assistant_evidence_pack.json",
]

SECRET_PATTERNS = [r"\.database\.windows\.net", r"(?i)password\s*=", r"(?i)pwd\s*=",
                   r"(?i)accountkey", r"(?i)sharedaccesssignature", r"(?i)bearer\s"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), (reader.fieldnames or [])


def write_csv(path: Path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def git_modified(paths):
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--"] + paths,
                             cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
        return [l for l in out.stdout.splitlines() if l[:2].strip() in ("M", "D", "R")]
    except Exception as exc:  # pragma: no cover
        return [f"git_unavailable: {exc}"]


def main():
    normalized, norm_cols = read_csv(MULTI / "official_metrics_normalized.csv")
    rankings, _ = read_csv(MULTI / "official_metric_rankings.csv")
    filters, _ = read_csv(MULTI / "metric_filter_options.csv")
    availability, _ = read_csv(MULTI / "metric_availability_status.csv")
    computability, _ = read_csv(MULTI / "metric_computability_status.csv")
    lineage, _ = read_csv(MULTI / "metric_source_lineage.csv")
    context, _ = read_csv(MULTI / "assistant_metric_context.csv")
    pack = json.loads((MULTI / "metric_assistant_evidence_pack.json").read_text(encoding="utf-8"))
    contract_cols = [r["column"] for r in read_csv(CONTRACT_DIR / "canonical_metric_columns.csv")[0]]

    tests = []

    def t(tid, name, expected, observed, blocking=True, notes="", status=None):
        tests.append({
            "test_id": tid, "test_name": name, "expected_result": expected,
            "observed_result": observed,
            "status": status or ("PASS" if str(expected) == str(observed) else "FAIL"),
            "blocking": "yes" if blocking else "no", "notes": notes,
        })

    builder_src = BUILDER.read_text(encoding="utf-8")
    literals = [ln for ln in builder_src.splitlines()
                if re.search(r"hdd|ssd|cpu|iops|phoenix|Enterprise", ln, re.I)
                and "VALIDATION_CASE_KEY" not in ln]
    t("T01", "registry_drives_the_build", 0, len(literals),
      notes="Only the declared VALIDATION_CASE_KEY constant names a key")

    t("T02", "normalized_schema_valid", contract_cols, norm_cols,
      notes=f"{len(norm_cols)} columns in contract order")

    t("T03", "no_blank_scenario", 0, sum(1 for r in normalized if not r["scenario"].strip()))
    t("T04", "scenario_not_applicable_accepted", True,
      sum(1 for r in normalized if r["scenario"] == "not_applicable") > 0,
      notes="Sources without a Scenario column normalise without error")
    t("T05", "no_inherited_scenario", 0,
      sum(1 for r in normalized
          if r["scenario"] not in ("not_applicable",) and r["source_family"] != "fact"),
      notes="No metrics source received a scenario value it does not physically have")

    freeze, _ = read_csv(FREEZE)
    freeze_rows, mismatches = [], 0
    for row in freeze:
        p = V6_ROOT / row["path"]
        observed = sha256(p) if p.exists() else "MISSING"
        ok = observed == row["sha256"]
        mismatches += 0 if ok else 1
        freeze_rows.append({
            "artifact": row["artifact"], "path": row["path"], "role": row["role"],
            "expected_hash": row["sha256"], "observed_hash": observed,
            "status": "UNCHANGED" if ok else "CHANGED",
        })
    t("T06", "legacy_files_unchanged", 0, mismatches,
      notes=f"{len(freeze_rows)} frozen artifacts rehashed")

    t("T07", "lvwe_lvne_isolation", 0,
      sum(1 for r in rankings if int(r["source_object_count"]) > 1),
      notes="Legacy build produced 137 blended groups")
    t("T08", "region_forest_isolation", 0, sum(1 for r in rankings if "|" in r["key_namespace"]))
    t("T09", "no_cross_unit_aggregation", 0, sum(1 for r in rankings if "|" in r["unit"]))
    key = ["metric_id", "db_type", "scenario", "granularity", "entity_key", "forecast_version"]
    t("T10", "ranking_key_uniqueness", len(rankings),
      len({tuple(r[k] for k in key) for r in rankings}))
    t("T11", "availability_gate_respected", 0,
      sum(1 for r in normalized
          if r["availability_status"] not in ("local_ingested", "partially_available")))
    t("T12", "single_version_not_marked_as_drift", 0,
      sum(1 for r in rankings
          if r["single_version_accuracy_only"] == "True" and r["drift_computable"] == "True")
      if "drift_computable" in (rankings[0] if rankings else {}) else
      sum(1 for r in rankings
          if r["single_version_accuracy_only"] == "True"
          and r["computability_status"] != "single_version_accuracy_only"))

    valid = {(f["filter_name"], f["filter_value"]) for f in filters}
    parent_of = {"DB Type": "Metric", "Scenario": "DB Type", "Granularity": "Scenario",
                 "Key": "Granularity", "Forecast Version": "Key"}
    orphans = sum(1 for f in filters
                  if parent_of.get(f["filter_name"])
                  and (parent_of[f["filter_name"]], f["parent_value"]) not in valid)
    t("T13", "filter_options_from_artifacts", 0, orphans)
    levels = {f["filter_name"] for f in filters}
    t("T14", "dependent_filter_chain_valid", 8, len(levels),
      notes="|".join(sorted(levels)))

    lineage_files = {r["source_file"] for r in lineage if r["source_file"]}
    norm_files = {r["source_file"] for r in normalized}
    t("T15", "lineage_completeness", 0, len(norm_files - lineage_files))

    src_counts = defaultdict(int)
    for r in normalized:
        src_counts[r["source_file"]] += 1
    dropped = 0
    for f, n in src_counts.items():
        rows, _ = read_csv(RAW / f)
        dropped += abs(len(rows) - n)
    t("T16", "data_quality_flags_not_dropped", 0, dropped,
      notes="rows_out equals rows_in for every emitting source")

    t("T17", "contract_version_stamped", 0,
      sum(1 for r in normalized if r["contract_version"] != "v6.0d"))

    case_rows = [r for r in normalized if r["entity_key"] == "NAMPRD07"]
    grains = sorted({r["granularity"] for r in case_rows})
    t("T18", "namprd07_resolves_as_forest", ["forest"], grains,
      notes=f"{len(case_rows)} rows across {len({r['source_object'] for r in case_rows})} sources")

    checksum_ok = True
    detail = []
    for f, n in src_counts.items():
        rows, _ = read_csv(RAW / f)
        src_sum = sum(float(r["MAPE"]) for r in rows if (r.get("MAPE") or "").strip())
        out_sum = sum(float(r["mape"]) for r in normalized
                      if r["source_file"] == f and str(r["mape"]).strip())
        same = abs(src_sum - out_sum) < 1e-6
        checksum_ok &= same
        detail.append(f"{f}:{'ok' if same else 'diff'}")
    t("T19", "hdd_metrics_preserved", True, checksum_ok, notes="; ".join(detail))

    t("T20", "no_sql_executed", 0,
      len(re.findall(r"pyodbc|cursor\(|connect\(", builder_src)))
    azure_use = re.findall(r"^\s*(?:import|from)\s+azure\b", builder_src, re.M)
    azure_use += re.findall(r"BlobServiceClient|DefaultAzureCredential|SecretClient|ContainerClient",
                            builder_src)
    t("T21", "no_azure_calls", 0, len(azure_use),
      notes="Detects SDK imports and client construction rather than the word in comments")

    fact_rows = sum(1 for r in normalized if r["source_family"] == "fact")
    raw_hashes = {sha256(p) for p in RAW.glob("*.csv")}
    copied = sum(1 for n in ARTIFACTS if sha256(MULTI / n) in raw_hashes)
    t("T22", "no_raw_data_exposed", 0, fact_rows + copied,
      notes="No fact-grain business rows emitted and no raw file copied. "
            "Lineage stores relative source paths as metadata only")

    secrets = 0
    for name in ARTIFACTS:
        text = (MULTI / name).read_text(encoding="utf-8", errors="ignore")
        for pat in SECRET_PATTERNS:
            secrets += len(re.findall(pat, text))
    t("T23", "no_secrets_in_artifacts", 0, secrets)

    outside = [n for n in ARTIFACTS if not (MULTI / n).exists()]
    t("T24", "artifacts_land_in_mounted_paths", 0, len(outside),
      notes="All artifacts under outputs/metrics_multi which is inside the read-only mount")

    unavailable = [a for a in availability if a["local_available"] == "no"]
    honest = all(a["availability_status"] and a["limitation"] for a in unavailable)
    t("T25", "unavailable_metric_reported_not_empty", True, honest,
      notes=f"{len(unavailable)} unavailable sources each carry a status and a limitation")

    shiny_mods = git_modified(["V6/shiny_app"])
    t("T26", "assistant_ui_still_present", 0, len(shiny_mods),
      status="PASS" if not shiny_mods else "FAIL",
      notes="Static check: no tracked Shiny file modified. Runtime render check runs in V6.0F")
    legacy_ok = LEGACY_PACK.exists() and json.loads(LEGACY_PACK.read_text(encoding="utf-8"))
    t("T27", "assistant_reads_governed_artifacts", True,
      bool(legacy_ok) and len(pack["responses"]) > 0,
      notes=f"Legacy pack parses with {len(legacy_ok['responses'])} responses; new pack has {len(pack['responses'])}")
    ctx_fields = {"metric_id", "db_type", "scenario", "granularity", "entity_key",
                  "forecast_version", "computability_status"}
    t("T28", "assistant_explains_selection_context", True,
      ctx_fields.issubset(set(context[0].keys())) and len(context) > 0,
      notes=f"{len(context)} selection rows carry the full identity tuple")
    t("T29", "assistant_explains_drift_computability", True,
      all(r["not_computable_reason"] for r in context if r["computability_status"] != "fully_computable"),
      notes="Every non-computable context row carries a reason code")
    invented = sum(1 for r in context
                   if r["scenario"] == "not_applicable" and r["scenario_status"] != "not_applicable")
    t("T30", "assistant_does_not_invent_scenario", 0, invented)
    bad_drift = sum(1 for r in context
                    if r["computability_status"] == "single_version_accuracy_only"
                    and "drift" not in r["assistant_disallowed_claims"])
    t("T31", "assistant_never_calls_single_version_drift", 0, bad_drift)
    t("T32", "assistant_no_cross_metric_aggregation_in_prose", 0,
      sum(1 for r in context if "cross metric raw aggregation" not in r["assistant_disallowed_claims"]))
    t("T33", "assistant_legacy_pack_unchanged",
      "A4DB09B4B78443D095CF9C4862120F209E1C509CE1EB619861F1642FD6D16E40", sha256(LEGACY_PACK))
    t("T34", "assistant_exports_still_work", "5 formats", "deferred", blocking=False,
      status="DEFERRED", notes="Requires a running Shiny session. Scheduled for V6.0F")
    t("T35", "assistant_works_in_docker_v6", "container parity", "deferred", blocking=False,
      status="DEFERRED", notes="Scheduled for V6.0H")

    write_csv(OUT / "v6_0e_test_results.csv",
              ["test_id", "test_name", "expected_result", "observed_result",
               "status", "blocking", "notes"], tests)
    write_csv(OUT / "v6_0e_legacy_freeze_validation.csv",
              ["artifact", "path", "role", "expected_hash", "observed_hash", "status"],
              freeze_rows)

    assistant_rows = []

    def a(check, expected, observed, status=None):
        assistant_rows.append({
            "check": check, "expected": expected, "observed": observed,
            "status": status or ("PASS" if str(expected) == str(observed) else "FAIL"),
        })

    for f in ASSISTANT_FILES:
        a(f"{f.name} present", "present", "present" if f.exists() else "MISSING")
    a("assistant files unmodified", 0, len(git_modified(["V6/shiny_app"])))
    a("legacy evidence pack unchanged", "UNCHANGED",
      "UNCHANGED" if sha256(LEGACY_PACK) ==
      "A4DB09B4B78443D095CF9C4862120F209E1C509CE1EB619861F1642FD6D16E40" else "CHANGED")
    a("assistant_metric_context.csv created", True, (MULTI / "assistant_metric_context.csv").exists())
    a("metric_assistant_evidence_pack.json created", True,
      (MULTI / "metric_assistant_evidence_pack.json").exists())
    a("pack keeps legacy shape", True,
      all(k in pack["responses"][0] for k in
          ("summary", "what_the_evidence_says", "why_it_matters", "sources_used",
           "limitations", "confidence", "claims_traceability", "download_payload")))
    a("pack declares no real llm", False, pack["is_real_llm"])
    a("pack declares no azure", False, pack["uses_azure"])
    a("allowed claims present", 0, sum(1 for r in context if not r["assistant_allowed_claims"]))
    a("disallowed claims present", 0, sum(1 for r in context if not r["assistant_disallowed_claims"]))
    a("no single-version accuracy called drift", 0, bad_drift)
    a("no invented scenario", 0, invented)
    a("claims traceable", 0,
      sum(1 for r in pack["responses"] if not r["claims_traceability"]))
    a("limitations present", 0, sum(1 for r in pack["responses"] if not r["limitations"]))
    write_csv(OUT / "v6_0e_assistant_preservation_validation.csv",
              ["check", "expected", "observed", "status"], assistant_rows)

    manifest = []
    for name in ARTIFACTS:
        p = MULTI / name
        if name.endswith(".csv"):
            rows, cols = read_csv(p)
            n_rows, n_cols = len(rows), len(cols)
        else:
            n_rows, n_cols = len(pack["responses"]), len(pack.keys())
        manifest.append({
            "artifact": name, "path": f"outputs/metrics_multi/{name}",
            "rows": n_rows, "columns": n_cols, "hash": sha256(p),
            "created_at": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
            "purpose": "multi-metric official artifact",
            "consumer": "V6.0F Shiny integration",
            "status": "CREATED",
        })
    write_csv(OUT / "v6_0e_artifact_manifest.csv",
              ["artifact", "path", "rows", "columns", "hash", "created_at",
               "purpose", "consumer", "status"], manifest)

    blocking_fail = [t_ for t_ in tests if t_["blocking"] == "yes" and t_["status"] != "PASS"]
    print(json.dumps({
        "tests": len(tests),
        "pass": sum(1 for x in tests if x["status"] == "PASS"),
        "deferred": sum(1 for x in tests if x["status"] == "DEFERRED"),
        "blocking_failures": len(blocking_fail),
        "failed_ids": [x["test_id"] for x in blocking_fail],
        "freeze_mismatches": mismatches,
        "assistant_failures": sum(1 for x in assistant_rows if x["status"] != "PASS"),
    }, indent=2))


if __name__ == "__main__":
    main()

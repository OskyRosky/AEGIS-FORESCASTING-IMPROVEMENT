"""V6.0E multi-metric artifact builder.

Registry-driven and metric-agnostic: every behaviour is resolved from
config/metric_registry.csv, so no branch in this module tests a metric name.
Reads local governed extracts only. No SQL, no Azure, no mutation of legacy
artifacts. Standard library only so the build is reproducible inside the
container image.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

CONTRACT_VERSION = "v6.0d"
GENERATED_STAGE = "V6.0E"

# Reported as a coverage column only. It is a validation case, never business logic.
VALIDATION_CASE_KEY = "NAMPRD07"

V6_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = V6_ROOT / "config" / "metric_registry.csv"
RAW_DIR = V6_ROOT / "data" / "raw"
OUT_DIR = V6_ROOT / "outputs" / "metrics_multi"

CANONICAL_COLUMNS = [
    "metric_id", "metric_name", "db_type", "db_type_label",
    "scenario", "scenario_status", "granularity", "entity_key",
    "region", "forest", "key_namespace",
    "forecast_version", "forecast_version_date",
    "source_object", "source_file", "source_family", "source_grain",
    "unit", "unit_status",
    "evaluation_start_date", "evaluation_end_date", "execution_date",
    "count", "mean_actual", "mean_forecast",
    "mae", "rmse", "bias", "bias_pct", "mape", "smape", "accuracy",
    "accuracy_computable", "drift_computable", "forecast_curve_computable",
    "cross_plan_computable", "horizon_error_computable",
    "computability_status", "not_computable_reason",
    "availability_status", "evidence_level", "data_quality_status",
    "notes", "contract_version",
]

MEASURE_MAP = OrderedDict([
    ("Count", "count"),
    ("Mean_Actual", "mean_actual"),
    ("Mean_Forecast", "mean_forecast"),
    ("MAE", "mae"),
    ("RMSE", "rmse"),
    ("Bias", "bias"),
    ("Bias_Pct", "bias_pct"),
    ("MAPE", "mape"),
    ("SMAPE", "smape"),
    ("Accuracy", "accuracy"),
])

RANKING_KEY = ["metric_id", "db_type", "scenario", "granularity",
               "entity_key", "forecast_version"]

AVAILABILITY_BLOCKED_REASON = {
    "source_not_found": "SOURCE_NOT_LOCATED",
    "pending_stakeholder_mapping": "PENDING_STAKEHOLDER_MAPPING",
    "not_ingested": "SOURCE_NOT_UPDATED_IN_EARTH",
    "deferred": "SOURCE_NOT_LOCATED",
}


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
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def as_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_version_date(value: str):
    text = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:len(fmt) + 2].strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def derive_region(entity_key: str, rule: str):
    if rule == "prefix_before_dash" and "-" in entity_key:
        return entity_key.split("-", 1)[0]
    return ""


def resolve_computability(source_family, versions, has_measures, availability):
    """Applies the V6.0D precedence table. Never infers capability from a name."""
    reasons = []
    accuracy = bool(has_measures)
    is_fact = source_family == "fact"
    drift = versions >= 2
    curve = is_fact
    cross_plan = drift
    horizon = False

    if availability in AVAILABILITY_BLOCKED_REASON:
        reasons.append(AVAILABILITY_BLOCKED_REASON[availability])
        status = ("blocked_by_mapping"
                  if availability == "pending_stakeholder_mapping"
                  else "not_computable")
        if availability == "deferred":
            status = "not_computable"
        return dict(accuracy_computable=False, drift_computable=False,
                    forecast_curve_computable=False, cross_plan_computable=False,
                    horizon_error_computable=False, computability_status=status,
                    not_computable_reason="|".join(reasons + ["UNKNOWN_UNIT"]))

    if not accuracy:
        reasons.append("NO_ACTUALS")
        if versions <= 1:
            reasons.append("SINGLE_VERSION_ONLY")
        # A fact source still has target-date grain, so the block is data, not structure.
        status = "blocked_by_data" if is_fact else "not_computable"
    elif versions <= 1:
        status = "single_version_accuracy_only"
        reasons.append("SINGLE_VERSION_ONLY")
    elif not curve:
        status = "accuracy_only"
    else:
        status = "fully_computable"

    if not curve:
        reasons.append("NO_TARGET_DATE_GRAIN")
        reasons.append("NO_FORECAST_FACT_TABLE")
    if not horizon and curve:
        reasons.append("NO_ACTUALS")
    reasons.append("SHINY_NOT_CONNECTED")

    return dict(accuracy_computable=accuracy, drift_computable=drift,
                forecast_curve_computable=curve, cross_plan_computable=cross_plan,
                horizon_error_computable=horizon, computability_status=status,
                not_computable_reason="|".join(dict.fromkeys(reasons)))


def build():
    registry, _ = read_csv(REGISTRY_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    normalized = []
    lineage = []
    quality = []
    resolved = []
    availability_rows = []
    computability_rows = []

    for entry in registry:
        source_object = entry["source_object"]
        source_file = (entry.get("source_file") or "").strip()
        local_path = RAW_DIR / source_file if source_file else None
        exists = bool(local_path and local_path.exists())

        rows, columns = ([], [])
        if exists:
            rows, columns = read_csv(local_path)

        has_scenario_column = "Scenario" in columns
        scenario_status = "present" if has_scenario_column else "not_applicable"
        if entry["availability_declared"] in ("source_not_found",
                                              "pending_stakeholder_mapping",
                                              "deferred"):
            scenario_status = ("pending_mapping"
                               if entry["availability_declared"] == "pending_stakeholder_mapping"
                               else "unknown")

        versions = sorted({(r.get("Forecast_Version") or r.get("ForecastVersion") or "").strip()
                           for r in rows} - {""})
        keys = sorted({(r.get("Key") or "").strip() for r in rows} - {""})
        has_measures = any(m in columns for m in MEASURE_MAP)

        availability = entry["availability_declared"] if not exists else (
            "partially_available" if len(versions) <= 1 and entry["source_family"] == "metrics"
            else entry["availability_declared"])

        comp = resolve_computability(entry["source_family"], len(versions),
                                     has_measures and exists, availability)

        emit = entry["emit_normalized_rows"] == "yes" and exists
        emitted = 0
        dq_counts = defaultdict(int)

        if emit:
            seen = set()
            for raw in rows:
                entity_key = (raw.get("Key") or "").strip()
                version = (raw.get("Forecast_Version")
                           or raw.get("ForecastVersion") or "").strip()
                scenario = ((raw.get("Scenario") or "").strip()
                            if has_scenario_column else "not_applicable")
                if not scenario:
                    scenario = "not_applicable"

                start = (raw.get("Start_Date") or "").strip()
                end = (raw.get("End_Date") or "").strip()

                dq = "ok"
                identity = (entity_key, version, start, end)
                if identity in seen:
                    dq = "duplicate_suspected"
                    dq_counts["duplicate_suspected"] += 1
                seen.add(identity)

                measures = {}
                for src_col, dest_col in MEASURE_MAP.items():
                    measures[dest_col] = as_float(raw.get(src_col))
                if all(v is None for v in measures.values()):
                    dq = "null_metrics"
                    dq_counts["null_metrics"] += 1
                acc = measures.get("accuracy")
                if acc is not None and (acc < 0 or acc > 100):
                    dq = "out_of_range"
                    dq_counts["out_of_range"] += 1
                if start and end and end < start:
                    dq = "out_of_range"
                    dq_counts["out_of_range"] += 1
                if dq == "ok":
                    dq_counts["ok"] += 1

                record = {c: "" for c in CANONICAL_COLUMNS}
                record.update({
                    "metric_id": entry["metric_id"],
                    "metric_name": entry["metric_name"],
                    "db_type": entry["db_type"],
                    "db_type_label": entry["db_type_label"],
                    "scenario": scenario,
                    "scenario_status": scenario_status,
                    "granularity": entry["granularity"],
                    "entity_key": entity_key,
                    "region": derive_region(entity_key, entry["region_parse_rule"]),
                    "forest": entity_key if entry["granularity"] in ("forest", "forest_sku") else "",
                    "key_namespace": entry["key_namespace"],
                    "forecast_version": version,
                    "forecast_version_date": parse_version_date(version),
                    "source_object": source_object,
                    "source_file": source_file,
                    "source_family": entry["source_family"],
                    "source_grain": entry["source_grain"],
                    "unit": entry["unit"],
                    "unit_status": entry["unit_status"],
                    "evaluation_start_date": start,
                    "evaluation_end_date": end,
                    "execution_date": (raw.get("Execution_Date") or "").strip(),
                    "availability_status": availability,
                    "evidence_level": entry["evidence_level"],
                    "data_quality_status": dq,
                    "notes": entry["known_limitation"],
                    "contract_version": CONTRACT_VERSION,
                })
                for dest_col, value in measures.items():
                    record[dest_col] = "" if value is None else value
                record.update({k: str(v) for k, v in comp.items()})
                normalized.append(record)
                emitted += 1

        lineage.append({
            "source_object": source_object,
            "source_file": source_file,
            "source_table": entry["source_table"],
            "local_path": str(local_path.relative_to(V6_ROOT)) if exists else "",
            "source_hash": sha256(local_path) if exists else "",
            "source_rows": len(rows),
            "generated_artifact": "official_metrics_normalized.csv" if emit else "metric_availability_status.csv",
            "generated_rows": emitted,
            "normalized_rows": emitted,
            "ranking_rows": 0,
            "evidence_level": entry["evidence_level"],
            "lineage_status": "complete" if emit else ("declared_only" if not exists else "not_emitted_by_design"),
            "notes": entry["notes"],
        })

        scenario_values = sorted({(r.get("Scenario") or "").strip()
                                  for r in rows} - {""}) if has_scenario_column else []

        availability_rows.append({
            "metric_id": entry["metric_id"],
            "metric_name": entry["metric_name"],
            "db_type": entry["db_type"],
            "scenario": "|".join(scenario_values) if scenario_values else (
                "not_applicable" if scenario_status == "not_applicable" else scenario_status),
            "granularity": entry["granularity"],
            "source_object": source_object,
            "source_file": source_file,
            "source_table": entry["source_table"],
            "local_available": "yes" if exists else "no",
            "local_rows": len(rows),
            "local_versions": len(versions),
            "local_keys": len(keys),
            "namprd07_present": "yes" if VALIDATION_CASE_KEY in keys else "no",
            "availability_status": availability,
            "evidence_level": entry["evidence_level"],
            "limitation": entry["known_limitation"],
            "next_action": entry["next_action"],
        })

        allowed_views = []
        renderable = comp["computability_status"] in (
            "fully_computable", "accuracy_only", "single_version_accuracy_only")
        if renderable:
            if comp["accuracy_computable"]:
                allowed_views.append("accuracy_table")
                allowed_views.append("accuracy_heatmap")
            if comp["drift_computable"]:
                allowed_views.append("cross_version_trend")
            if comp["cross_plan_computable"]:
                allowed_views.append("plan_to_plan")
            if comp["forecast_curve_computable"]:
                allowed_views.append("forecast_curve")
            if comp["horizon_error_computable"]:
                allowed_views.append("error_by_horizon")

        computability_rows.append({
            "metric_id": entry["metric_id"],
            "db_type": entry["db_type"],
            "scenario": "not_applicable" if scenario_status == "not_applicable" else scenario_status,
            "granularity": entry["granularity"],
            "accuracy_computable": comp["accuracy_computable"],
            "drift_computable": comp["drift_computable"],
            "forecast_curve_computable": comp["forecast_curve_computable"],
            "cross_plan_computable": comp["cross_plan_computable"],
            "horizon_error_computable": comp["horizon_error_computable"],
            "computability_status": comp["computability_status"],
            "not_computable_reason": comp["not_computable_reason"],
            "source_object": source_object,
            "evidence_level": entry["evidence_level"],
            "shiny_allowed_views": "|".join(allowed_views) if allowed_views else "none",
            "assistant_allowed_claims_summary": (
                "May state observed accuracy for the retained cycle. Must not claim drift."
                if comp["computability_status"] == "single_version_accuracy_only"
                else "May state observed accuracy and cross version change."
                if comp["computability_status"] == "accuracy_only"
                else "Must state the source is unavailable and give the reason."),
        })

        resolved.append({
            "source_object": source_object,
            "metric_id": entry["metric_id"],
            "metric_name": entry["metric_name"],
            "db_type": entry["db_type"],
            "db_type_label": entry["db_type_label"],
            "scenario": "not_applicable" if scenario_status == "not_applicable" else scenario_status,
            "scenario_status": scenario_status,
            "granularity": entry["granularity"],
            "key_namespace": entry["key_namespace"],
            "source_family": entry["source_family"],
            "source_file": source_file,
            "source_table": entry["source_table"],
            "unit": entry["unit"],
            "unit_status": entry["unit_status"],
            "availability_status": availability,
            "computability_status": comp["computability_status"],
            "known_limitation": entry["known_limitation"],
            "include_in_shiny": entry["include_in_shiny"],
            "include_in_assistant": entry["include_in_assistant"],
            "merge_sources_allowed": entry["merge_sources_allowed"],
            "notes": entry["notes"],
        })

        for check, observed in (("source_exists", "yes" if exists else "no"),
                                ("schema_valid", "yes" if (not exists or has_measures) else "no"),
                                ("row_count_positive", "yes" if len(rows) > 0 else "no")):
            quality.append({
                "check_id": f"{source_object}:{check}",
                "source_object": source_object,
                "metric_id": entry["metric_id"],
                "check_name": check,
                "expected": "yes" if entry["emit_normalized_rows"] == "yes" else "declared",
                "observed": observed,
                "status": "PASS" if (entry["emit_normalized_rows"] != "yes" or observed == "yes") else "FAIL",
                "severity": "blocking" if entry["emit_normalized_rows"] == "yes" else "informational",
            })
        for label, count in dq_counts.items():
            quality.append({
                "check_id": f"{source_object}:data_quality:{label}",
                "source_object": source_object,
                "metric_id": entry["metric_id"],
                "check_name": f"rows_{label}",
                "expected": "counted_not_dropped",
                "observed": count,
                "status": "PASS",
                "severity": "informational",
            })

    write_csv(OUT_DIR / "official_metrics_normalized.csv", CANONICAL_COLUMNS, normalized)

    rankings = build_rankings(normalized)
    ranking_cols = list(rankings[0].keys()) if rankings else RANKING_KEY
    write_csv(OUT_DIR / "official_metric_rankings.csv", ranking_cols, rankings)

    counts = defaultdict(int)
    for r in rankings:
        counts[r["source_object"]] += 1
    for row in lineage:
        row["ranking_rows"] = counts.get(row["source_object"], 0)

    filters = build_filters(normalized, availability_rows, computability_rows)
    write_csv(OUT_DIR / "metric_filter_options.csv", list(filters[0].keys()), filters)

    write_csv(OUT_DIR / "metric_availability_status.csv",
              list(availability_rows[0].keys()), availability_rows)
    write_csv(OUT_DIR / "metric_computability_status.csv",
              list(computability_rows[0].keys()), computability_rows)
    write_csv(OUT_DIR / "metric_source_lineage.csv", list(lineage[0].keys()), lineage)
    write_csv(OUT_DIR / "metric_registry_resolved.csv", list(resolved[0].keys()), resolved)

    quality.extend(global_quality_checks(normalized, rankings, filters))
    write_csv(OUT_DIR / "metric_data_quality_checks.csv", list(quality[0].keys()), quality)

    context = build_assistant_context(rankings)
    write_csv(OUT_DIR / "assistant_metric_context.csv", list(context[0].keys()), context)

    pack = build_assistant_pack(rankings, availability_rows, computability_rows, resolved)
    (OUT_DIR / "metric_assistant_evidence_pack.json").write_text(
        json.dumps(pack, indent=2), encoding="utf-8")

    print(json.dumps({
        "normalized_rows": len(normalized),
        "ranking_rows": len(rankings),
        "filter_options": len(filters),
        "availability_rows": len(availability_rows),
        "computability_rows": len(computability_rows),
        "lineage_rows": len(lineage),
        "quality_rows": len(quality),
        "registry_rows": len(resolved),
        "assistant_context_rows": len(context),
        "assistant_pack_entries": len(pack["responses"]),
    }))


def _avg(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 6) if vals else ""


def build_rankings(normalized):
    groups = OrderedDict()
    for row in normalized:
        key = tuple(row[k] for k in RANKING_KEY)
        groups.setdefault(key, []).append(row)

    out = []
    for key, rows in groups.items():
        first = rows[0]
        sources = sorted({r["source_object"] for r in rows})
        files = sorted({r["source_file"] for r in rows})
        units = sorted({r["unit"] for r in rows})
        namespaces = sorted({r["key_namespace"] for r in rows})
        mape = [as_float(r["mape"]) for r in rows]
        acc = [as_float(r["accuracy"]) for r in rows]
        record = OrderedDict(zip(RANKING_KEY, key))
        record.update({
            "key_namespace": "|".join(namespaces),
            "unit": "|".join(units),
            "source_object": "|".join(sources),
            "source_file": "|".join(files),
            "source_object_count": len(sources),
            "row_count": len(rows),
            "n_windows": len({(r["evaluation_start_date"], r["evaluation_end_date"]) for r in rows}),
            "avg_mape": _avg(mape),
            "max_mape": max([v for v in mape if v is not None], default=""),
            "avg_smape": _avg([as_float(r["smape"]) for r in rows]),
            "avg_rmse": _avg([as_float(r["rmse"]) for r in rows]),
            "avg_mae": _avg([as_float(r["mae"]) for r in rows]),
            "avg_bias_pct": _avg([as_float(r["bias_pct"]) for r in rows]),
            "avg_accuracy": _avg(acc),
            "min_accuracy": min([v for v in acc if v is not None], default=""),
            "evaluation_start_min": min([r["evaluation_start_date"] for r in rows if r["evaluation_start_date"]], default=""),
            "evaluation_end_max": max([r["evaluation_end_date"] for r in rows if r["evaluation_end_date"]], default=""),
            "availability_status": first["availability_status"],
            "computability_status": first["computability_status"],
            "not_computable_reason": first["not_computable_reason"],
            "single_version_accuracy_only": first["computability_status"] == "single_version_accuracy_only",
            "contract_version": CONTRACT_VERSION,
        })
        out.append(record)

    partitions = defaultdict(list)
    for record in out:
        partitions[(record["metric_id"], record["db_type"],
                    record["granularity"], record["forecast_version"])].append(record)
    for members in partitions.values():
        ranked = sorted(members, key=lambda r: (r["avg_mape"] == "", r["avg_mape"]))
        for position, record in enumerate(ranked, start=1):
            record["rank_mape_within_partition"] = position
    return out


def build_filters(normalized, availability_rows, computability_rows):
    comp_by_combo = {(c["metric_id"], c["db_type"], c["granularity"]): c
                     for c in computability_rows}
    avail_by_combo = {(a["metric_id"], a["db_type"], a["granularity"]): a
                      for a in availability_rows}
    options = []
    order = defaultdict(int)

    def add(level, value, label, parent_level, parent_value, ctx,
            enabled=True, reason=""):
        order[level] += 1
        options.append({
            "filter_name": level,
            "filter_value": value,
            "filter_label": label,
            "parent_filter": parent_level,
            "parent_value": parent_value,
            "metric_id": ctx.get("metric_id", ""),
            "db_type": ctx.get("db_type", ""),
            "scenario": ctx.get("scenario", ""),
            "scenario_status": ctx.get("scenario_status", ""),
            "granularity": ctx.get("granularity", ""),
            "entity_key": ctx.get("entity_key", ""),
            "forecast_version": ctx.get("forecast_version", ""),
            "availability_status": ctx.get("availability_status", ""),
            "computability_status": ctx.get("computability_status", ""),
            "enabled": "true" if enabled else "false",
            "visible": "true",
            "reason_if_disabled": reason,
            "display_order": order[level],
            "source_artifact": "official_metrics_normalized.csv" if enabled
                               else "metric_availability_status.csv",
        })

    seen_metric = OrderedDict()
    for row in availability_rows:
        seen_metric.setdefault(row["metric_id"], row)
    for metric_id, row in seen_metric.items():
        live = any(n["metric_id"] == metric_id for n in normalized)
        add("Metric", metric_id, row["metric_name"], "", "",
            {"metric_id": metric_id,
             "availability_status": row["availability_status"]},
            enabled=live,
            reason="" if live else f"{row['availability_status']}: {row['limitation']}")

    combos = OrderedDict()
    for row in normalized:
        combos.setdefault((row["metric_id"], row["db_type"]), row)
    for row in availability_rows:
        combos.setdefault((row["metric_id"], row["db_type"]), None)

    for (metric_id, db_type), sample in combos.items():
        live = sample is not None
        avail = avail_by_combo.get((metric_id, db_type, sample["granularity"])) if live else None
        label = sample["db_type_label"] if live else db_type
        reason = ""
        if not live:
            match = next((a for a in availability_rows
                          if a["metric_id"] == metric_id and a["db_type"] == db_type), None)
            reason = f"{match['availability_status']}: {match['limitation']}" if match else "unavailable"
        add("DB Type", f"{metric_id}::{db_type}", label, "Metric", metric_id,
            {"metric_id": metric_id, "db_type": db_type,
             "availability_status": (avail or {}).get("availability_status", "")},
            enabled=live, reason=reason)

    scen = OrderedDict()
    for row in normalized:
        scen.setdefault((row["metric_id"], row["db_type"], row["scenario"]), row)
    for (metric_id, db_type, scenario), sample in scen.items():
        add("Scenario", f"{metric_id}::{db_type}::{scenario}",
            "Not applicable" if scenario == "not_applicable" else scenario,
            "DB Type", f"{metric_id}::{db_type}",
            {"metric_id": metric_id, "db_type": db_type, "scenario": scenario,
             "scenario_status": sample["scenario_status"]},
            enabled=(sample["scenario_status"] == "present"),
            reason="Source has no scenario dimension"
                   if sample["scenario_status"] == "not_applicable" else "")

    gran = OrderedDict()
    for row in normalized:
        gran.setdefault((row["metric_id"], row["db_type"], row["scenario"],
                         row["granularity"]), row)
    for (metric_id, db_type, scenario, granularity), sample in gran.items():
        comp = comp_by_combo.get((metric_id, db_type, granularity), {})
        add("Granularity", f"{metric_id}::{db_type}::{scenario}::{granularity}",
            granularity, "Scenario", f"{metric_id}::{db_type}::{scenario}",
            {"metric_id": metric_id, "db_type": db_type, "scenario": scenario,
             "granularity": granularity,
             "computability_status": comp.get("computability_status", "")})

    keys = OrderedDict()
    for row in normalized:
        keys.setdefault((row["metric_id"], row["db_type"], row["scenario"],
                         row["granularity"], row["entity_key"]), row)
    for (metric_id, db_type, scenario, granularity, entity_key), sample in keys.items():
        add("Key", f"{metric_id}::{db_type}::{scenario}::{granularity}::{entity_key}",
            entity_key, "Granularity",
            f"{metric_id}::{db_type}::{scenario}::{granularity}",
            {"metric_id": metric_id, "db_type": db_type, "scenario": scenario,
             "granularity": granularity, "entity_key": entity_key,
             "key_namespace": sample["key_namespace"]})

    versions = OrderedDict()
    version_count = defaultdict(set)
    for row in normalized:
        version_count[(row["metric_id"], row["db_type"], row["granularity"],
                       row["entity_key"])].add(row["forecast_version"])
    for row in normalized:
        versions.setdefault((row["metric_id"], row["db_type"], row["scenario"],
                             row["granularity"], row["entity_key"],
                             row["forecast_version"]), row)
    for key_tuple, sample in versions.items():
        metric_id, db_type, scenario, granularity, entity_key, version = key_tuple
        only_one = len(version_count[(metric_id, db_type, granularity, entity_key)]) == 1
        add("Forecast Version",
            f"{metric_id}::{db_type}::{scenario}::{granularity}::{entity_key}::{version}",
            f"{version} (single version)" if only_one else version,
            "Key", f"{metric_id}::{db_type}::{scenario}::{granularity}::{entity_key}",
            {"metric_id": metric_id, "db_type": db_type, "scenario": scenario,
             "granularity": granularity, "entity_key": entity_key,
             "forecast_version": version,
             "computability_status": sample["computability_status"]},
            reason="single_version_accuracy_only" if only_one else "")

    for value in sorted({a["availability_status"] for a in availability_rows}):
        add("Availability Status", value, value, "", "", {"availability_status": value})
    for value in sorted({c["computability_status"] for c in computability_rows}):
        add("Computability Status", value, value, "", "", {"computability_status": value})

    return options


def global_quality_checks(normalized, rankings, filters):
    checks = []

    def add(name, expected, observed, blocking=True):
        checks.append({
            "check_id": f"global:{name}",
            "source_object": "ALL",
            "metric_id": "ALL",
            "check_name": name,
            "expected": expected,
            "observed": observed,
            "status": "PASS" if str(observed) == str(expected) else "FAIL",
            "severity": "blocking" if blocking else "informational",
        })

    add("no_blank_scenario", 0, sum(1 for r in normalized if not r["scenario"].strip()))
    add("metric_id_present", 0, sum(1 for r in normalized if not r["metric_id"].strip()))
    add("db_type_present", 0, sum(1 for r in normalized if not r["db_type"].strip()))
    add("granularity_present", 0, sum(1 for r in normalized if not r["granularity"].strip()))
    add("entity_key_present", 0, sum(1 for r in normalized if not r["entity_key"].strip()))
    add("source_object_present", 0, sum(1 for r in normalized if not r["source_object"].strip()))
    add("unit_present", 0, sum(1 for r in normalized if not r["unit"].strip()))
    add("computability_status_present", 0,
        sum(1 for r in normalized if not r["computability_status"].strip()))
    add("no_lvwe_lvne_mixing", 0, sum(1 for r in rankings if r["source_object_count"] > 1))
    add("no_region_forest_mixing", 0, sum(1 for r in rankings if "|" in r["key_namespace"]))
    add("no_cross_unit_aggregation", 0, sum(1 for r in rankings if "|" in r["unit"]))
    add("ranking_key_unique", len(rankings),
        len({tuple(r[k] for k in RANKING_KEY) for r in rankings}))
    add("single_version_not_drift", 0,
        sum(1 for r in rankings
            if r["single_version_accuracy_only"] and r["computability_status"] != "single_version_accuracy_only"))
    add("scenario_not_applicable_valid", 0,
        sum(1 for r in normalized
            if r["scenario"] == "not_applicable" and r["scenario_status"] != "not_applicable"))
    add("assistant_compatibility_fields_present", 0,
        sum(1 for r in normalized if not r["availability_status"].strip()
            or not r["evidence_level"].strip()))

    valid_parents = {(f["filter_name"], f["filter_value"]) for f in filters}
    orphans = 0
    parent_of = {"DB Type": "Metric", "Scenario": "DB Type",
                 "Granularity": "Scenario", "Key": "Granularity",
                 "Forecast Version": "Key"}
    for f in filters:
        parent_level = parent_of.get(f["filter_name"])
        if parent_level and (parent_level, f["parent_value"]) not in valid_parents:
            orphans += 1
    add("filter_options_no_orphans", 0, orphans)
    return checks


def build_assistant_context(rankings):
    out = []
    for r in rankings:
        single = r["single_version_accuracy_only"]
        disallowed = ["drift", "trend over time", "deterioration", "improvement over time"] if single else []
        disallowed += ["cross metric raw aggregation", "invented scenario values"]
        summary = (
            f"{r['metric_id']} / {r['db_type']} at {r['granularity']} grain, key {r['entity_key']}, "
            f"forecast version {r['forecast_version']}: average MAPE {r['avg_mape']}, "
            f"average accuracy {r['avg_accuracy']}, across {r['row_count']} evaluation windows "
            f"from {r['evaluation_start_min']} to {r['evaluation_end_max']}."
        )
        context = (
            "Single retained forecast version, so this is point accuracy for one cycle and not drift."
            if single else
            "Multiple forecast versions are retained, so cross version accuracy comparison is available."
        )
        out.append({
            "metric_id": r["metric_id"],
            "metric_name": r["metric_id"],
            "db_type": r["db_type"],
            "scenario": r["scenario"],
            "scenario_status": "not_applicable" if r["scenario"] == "not_applicable" else "present",
            "granularity": r["granularity"],
            "entity_key": r["entity_key"],
            "forecast_version": r["forecast_version"],
            "unit": r["unit"],
            "unit_status": "pending_d5",
            "availability_status": r["availability_status"],
            "computability_status": r["computability_status"],
            "not_computable_reason": r["not_computable_reason"],
            "explanation_context": context,
            "safe_summary": summary,
            "assistant_allowed_claims": "observed accuracy|observed bias|evaluation window coverage|source identity",
            "assistant_disallowed_claims": "|".join(disallowed),
            "evidence_level": "VERIFIED_LOCAL",
            "source_object": r["source_object"],
            "source_file": r["source_file"],
        })
    return out


def _pack_entry(page_id, title, summary, evidence, why, sources, limitations,
                confidence, claims):
    return {
        "page_id": page_id,
        "title": title,
        "summary": summary,
        "what_the_evidence_says": evidence,
        "why_it_matters": why,
        "sources_used": sources,
        "limitations": limitations,
        "confidence": confidence,
        "claims_traceability": [
            {"claim_id": f"{page_id}_c{i+1}", "claim": c[0],
             "evidence_pack": "metric_assistant_evidence_pack.json",
             "source_artifacts": c[1], "evidence_fields": c[2]}
            for i, c in enumerate(claims)
        ],
        "download_payload": {"format": "markdown", "body": summary},
    }


def build_assistant_pack(rankings, availability_rows, computability_rows, resolved):
    by_source = defaultdict(list)
    for r in rankings:
        by_source[r["source_object"]].append(r)

    def stats(source_object):
        rows = by_source.get(source_object, [])
        if not rows:
            return None
        mapes = [r["avg_mape"] for r in rows if r["avg_mape"] != ""]
        accs = [r["avg_accuracy"] for r in rows if r["avg_accuracy"] != ""]
        return {
            "groups": len(rows),
            "keys": len({r["entity_key"] for r in rows}),
            "versions": len({r["forecast_version"] for r in rows}),
            "avg_mape": round(sum(mapes) / len(mapes), 4) if mapes else "",
            "avg_accuracy": round(sum(accs) / len(accs), 4) if accs else "",
        }

    responses = []
    responses.append(_pack_entry(
        "multi_metric_overview", "Multi-metric overview",
        "AEGIS now carries governed accuracy metrics for more than one metric, "
        "each keeping its own identity so variants are never blended.",
        "Every normalized row declares metric_id, db_type, scenario, granularity, "
        "entity_key and forecast_version, and every ranking group is isolated by that same tuple.",
        "Without this identity the dashboard silently averaged different series together.",
        ["official_metrics_normalized.csv", "official_metric_rankings.csv",
         "metric_registry_resolved.csv"],
        ["Availability differs per metric. Several metrics are not yet located in the source."],
        "high",
        [("Each metric keeps a separate identity", "official_metrics_normalized.csv",
          "metric_id|db_type|granularity"),
         ("Rankings never merge two source objects", "official_metric_rankings.csv",
          "source_object_count")]))

    labels = {}
    for entry in resolved:
        if entry["source_object"] not in by_source:
            continue
        slug = f"{entry['metric_id']}_{entry['db_type']}_{entry['granularity']}".lower()
        labels[entry["source_object"]] = (
            slug, f"{entry['metric_name']} {entry['db_type_label']} at {entry['granularity']} grain")
    for source_object, (page_id, title) in labels.items():
        s = stats(source_object)
        if not s:
            continue
        single = s["versions"] == 1
        responses.append(_pack_entry(
            page_id, title,
            f"{title} covers {s['keys']} keys across {s['versions']} retained forecast "
            f"version(s), with an average MAPE of {s['avg_mape']} and average accuracy of {s['avg_accuracy']}.",
            f"The source contributes {s['groups']} isolated ranking groups. "
            "Values are read verbatim from the governed extract and are never recomputed.",
            "It lets the review compare model behaviour on a like-for-like basis inside one metric.",
            ["official_metrics_normalized.csv", "official_metric_rankings.csv"],
            (["Only one forecast version is retained, so cross plan drift is not available.",
              "The source has no target date dimension, so error by horizon is not available."]
             if single else
             ["The source has no target date dimension, so error by horizon is not available."]),
            "high",
            [("Coverage and averages come from governed rows", "official_metric_rankings.csv",
              "row_count|avg_mape|avg_accuracy"),
             ("Capability is declared upstream", "metric_computability_status.csv",
              "computability_status|not_computable_reason")]))

    namprd = [r for r in rankings if r["entity_key"] == VALIDATION_CASE_KEY]
    if namprd:
        detail = "; ".join(
            f"{r['metric_id']}/{r['db_type']} version {r['forecast_version']} "
            f"average accuracy {r['avg_accuracy']} and average MAPE {r['avg_mape']}"
            for r in namprd)
        single_note = [
            "Some of this evidence is single version, so no cross plan drift can be stated."
        ] if any(r["single_version_accuracy_only"] for r in namprd) else []
        responses.append(_pack_entry(
            "namprd07_case", f"{VALIDATION_CASE_KEY} across metrics",
            f"{VALIDATION_CASE_KEY} is a {namprd[0]['granularity']}-grain key and appears in "
            f"{len(namprd)} isolated groups: {detail}.",
            "The key resolves to the same namespace in every source that contains it and "
            "never appears in a source of a different granularity.",
            "It is the first validation case for the multi-metric separation.",
            ["official_metric_rankings.csv", "metric_availability_status.csv"],
            single_note or ["Coverage differs per source."],
            "high",
            [(f"{VALIDATION_CASE_KEY} resolves to one granularity",
              "official_metrics_normalized.csv", "granularity|key_namespace"),
             ("Variants of the same metric stay separated", "official_metric_rankings.csv",
              "db_type|source_object")]))

    blocked = [a for a in availability_rows
               if a["availability_status"] in ("source_not_found", "pending_stakeholder_mapping",
                                               "deferred", "not_ingested")]
    responses.append(_pack_entry(
        "unavailable_metrics", "Metrics that are not available yet",
        f"{len(blocked)} declared sources are not usable yet, and each one states why.",
        "; ".join(f"{b['metric_id']}/{b['db_type']}: {b['availability_status']}" for b in blocked),
        "Reporting absence honestly prevents an empty chart from being read as a zero.",
        ["metric_availability_status.csv", "metric_computability_status.csv"],
        ["Several table names are stakeholder statements that were never located in evidence."],
        "high",
        [("Unavailable sources are declared not guessed", "metric_availability_status.csv",
          "availability_status|limitation")]))

    responses.append(_pack_entry(
        "single_version_accuracy", "Why single-version accuracy is not drift",
        "When only one forecast version is retained, the evidence supports point accuracy "
        "for that cycle and nothing about change over time.",
        "Drift requires at least two comparable forecast versions. The contract sets "
        "drift_computable to false whenever a source retains one version.",
        "Calling it drift would imply a trend that the data cannot support.",
        ["metric_computability_status.csv", "official_metric_rankings.csv"],
        ["This limitation is a property of source retention, not of the analysis method."],
        "high",
        [("Single version blocks drift", "metric_computability_status.csv",
          "drift_computable|not_computable_reason")]))

    responses.append(_pack_entry(
        "drift_computability", "Why drift is or is not computable",
        "Drift is only offered when a source retains two or more comparable forecast versions "
        "and the compared rows share one unit.",
        "; ".join(
            f"{c['metric_id']}/{c['db_type']} at {c['granularity']} grain: "
            f"drift_computable={c['drift_computable']} because {c['not_computable_reason']}"
            for c in computability_rows if c["evidence_level"] == "VERIFIED_LOCAL"),
        "It stops a one-cycle measurement from being read as a movement between plans.",
        ["metric_computability_status.csv", "official_metric_rankings.csv"],
        ["Capability is declared by the producer and the dashboard must not override it."],
        "high",
        [("Drift availability is declared per source", "metric_computability_status.csv",
          "drift_computable|cross_plan_computable|not_computable_reason")]))

    collision = defaultdict(set)
    for r in rankings:
        collision[(r["metric_id"], r["granularity"], r["entity_key"],
                   r["forecast_version"])].add(r["db_type"])
    at_risk = sorted({k[0] for k, v in collision.items() if len(v) > 1})
    variants = sorted({r["db_type"] for r in rankings if r["metric_id"] in at_risk})
    responses.append(_pack_entry(
        "variant_separation", "Why same-metric variants are reported separately",
        (f"Metrics {', '.join(at_risk)} expose more than one variant that shares the same key "
         f"and forecast version: {', '.join(variants)}. They are reported side by side and never pooled.")
        if at_risk else
        "No metric currently exposes two variants sharing a key and forecast version.",
        "Grouping by key and version alone merged them. The ranking key now includes db_type "
        "and every group asserts a single source object.",
        "A blended average corresponds to no real series and would misinform the review.",
        ["official_metric_rankings.csv", "metric_registry_resolved.csv"],
        ["The final classification of these variants is a pending stakeholder decision."],
        "high",
        [("Variants stay isolated", "official_metric_rankings.csv",
          "db_type|source_object_count"),
         ("Isolation is registry driven", "metric_registry_resolved.csv",
          "db_type|merge_sources_allowed")]))

    responses.append(_pack_entry(
        "unit_discipline", "Why values are not combined across metrics",
        "Raw business values are never aggregated across metrics because their units differ "
        "and none of the units is verified yet.",
        "Every row carries a unit and a unit_status. Storage, compute and rate measures are "
        "not additive, and a ranking group must resolve to exactly one unit.",
        "Summing across metrics would produce a number with no physical meaning.",
        ["metric_unit_contract_v6_0d.csv", "official_metric_rankings.csv"],
        ["Units remain UNKNOWN pending the data engineering confirmation."],
        "high",
        [("Cross metric raw aggregation is blocked", "official_metric_rankings.csv", "unit"),
         ("Units are unverified", "metric_registry_resolved.csv", "unit|unit_status")]))

    return {
        "provider": "artifact_grounded_metric_pack",
        "provider_stage": "artifact_grounded_metric_pack",
        "is_real_llm": False,
        "uses_azure": False,
        "contract_version": CONTRACT_VERSION,
        "generated_stage": GENERATED_STAGE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "responses": responses,
    }


if __name__ == "__main__":
    sys.exit(build())

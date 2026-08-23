"""V6.24-P4 | Data dictionary, readable manifest, README, quality report, validation."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P3 = OUT.parent / "v6_24_p3_governed_data_extraction_to_parquet"

AUDIT = json.loads((OUT / "_p4_audit.json").read_text(encoding="utf-8"))
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
BASE = pd.read_parquet(PROC / "source_forecast_baselines_normalized.parquet", engine="pyarrow")


def write(name, fields, rows, folder=OUT):
    with (Path(folder) / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ============================================== data dictionary
F = ["artifact", "column_name", "data_type", "definition", "allowed_values_or_placeholders",
     "derived_or_verbatim", "notes"]
VERB = "VERBATIM_FROM_SOURCE"
DERIV = "DERIVED_BY_P4"
dd = []


def d(art, col, dtype, defn, allowed, kind, note=""):
    dd.append(dict(zip(F, [art, col, dtype, defn, allowed, kind, note])))


A = "cohort_manifest"
d(A, "cohort_id", "string", "Stable cohort identifier for the frozen 140-series MVP set.",
  "V6_24_MVP_0001 .. V6_24_MVP_0140", DERIV,
  "Assigned after a deterministic sort by metric, route and key.")
d(A, "series_id", "string", "Stable deterministic series identity. The join key for P5/P6/P7.",
  "HDD__<db>__<seg>__<gran>__<key> | SSD__Phoenix__Forest__<key> | "
  "<CPU|IOPS>__<scenario>__Region__<key>", DERIV,
  "Independent of row order. Does NOT distinguish LVWE from LVNE, because they are one "
  "observed series.")
d(A, "metric", "string", "Product metric.", "HDD | SSD | CPU | IOPS", VERB, "")
d(A, "db_type", "string", "Database branch axis.",
  "EDB | Basilisk | Phoenix | NOT_APPLICABLE | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE", VERB,
  "CPU carries the UNKNOWN placeholder because its source has no DB Type column. Never render "
  "that value as a filter option.")
d(A, "variant_contract", "string", "Forecast-variant contract for the series.",
  "LVWE+LVNE (forecast variants) | NOT_APPLICABLE", DERIV,
  "SSD only. Signals that two forecast baselines share one actual series.")
d(A, "scenario", "string", "Scenario axis.", "Consumed | Failover | NOT_APPLICABLE", VERB,
  "CPU and IOPS only. SSD and HDD have no scenario axis in this cohort.")
d(A, "segment", "string", "Segment axis, conditional on db_type.",
  "Consumer | Enterprise | NOT_APPLICABLE", VERB,
  "HDD only, and only under EDB. NOT_APPLICABLE under Basilisk.")
d(A, "demand_nature", "string", "Demand nature from source.",
  "Organic | Organic_adjust | source value", VERB, "Informational, not a product filter.")
d(A, "granularity", "string", "Aggregation level.", "Forest | Region", VERB, "")
d(A, "key", "string", "Series entity.", "forest name | region-environment composite", VERB,
  "Preserved exactly as it appears in source. Not case-normalized.")
d(A, "route_path", "string", "Pipe-delimited taxonomy route.", "free text", DERIV, "")
d(A, "ui_filter_path", "string", "Human-readable filter path for UI/UX.", "free text", DERIV,
  "Shows the exact axis sequence a user would traverse.")
d(A, "source_status", "string", "How the series entered the cohort.",
  "ALREADY_LOCAL_NOT_EXTRACTED | EXTRACTED_IN_P3", DERIV, "")
d(A, "source_object_or_artifact", "string", "Originating SQL table or local artifact.",
  "free text", VERB, "")
d(A, "raw_or_local_source_path", "string", "Repository-relative path to the source file.",
  "free text", DERIV, "")
d(A, "date_column_source", "string", "Source column used as the series date.",
  "End_Date | DateTime | date", VERB,
  "SSD uses End_Date, the close of the rolling window, not Start_Date.")
d(A, "actual_column_source", "string", "Source column used as the actual value.",
  "Mean_Actual | Value | actual_value", VERB, "")
d(A, "value_transformation", "string", "Transformation applied to the value.",
  "NONE | CAST_VARCHAR_TO_FLOAT", DERIV,
  "The ONLY transformation P4 performs. No scaling, smoothing or interpolation anywhere.")
d(A, "min_date / max_date", "string", "Observed date range after processing.", "ISO date", DERIV,
  "Computed from actuals_normalized, not carried from a plan file.")
d(A, "observation_count", "int", "Rows in actuals_normalized for this series.", ">= 51", DERIV, "")
d(A, "distinct_date_count", "int", "Distinct series_date values.", ">= 51", DERIV,
  "Equals observation_count for every series after deduplication.")
d(A, "duplicate_rows_removed", "int", "Exact duplicate rows removed for this series.", "0 or 1",
  DERIV, "SSD only: one exact duplicate per key on 2026-04-22.")
d(A, "freshness_status", "string", "Recency of the observed history.",
  "CURRENT | CURRENT (to 2026-08-22) | STALE (to 2023-07-20)", DERIV, "")
d(A, "caveat", "string", "Material limitation carried with the series.", "free text", DERIV,
  "Travels in the data so it cannot be lost in prose.")
d(A, "has_actuals", "string", "Whether observed actuals exist.", "TRUE", DERIV,
  "TRUE for all 140.")
d(A, "has_15_model_backtests", "string", "Whether the 15 governed backtests exist NOW.",
  "TRUE | FALSE", DERIV, "TRUE only for the 50 local HDD series.")
d(A, "has_forecast_outputs / has_accuracy_metrics", "string", "Whether those artifacts exist now.",
  "TRUE | FALSE", DERIV, "TRUE only for HDD.")
d(A, "viewer_visible_now", "string", "Whether the series may render in Shiny today.",
  "TRUE | FALSE", DERIV,
  "FALSE for all 90 non-HDD series. P7 must not expose a series lacking its backtests.")
d(A, "viewer_visible_after_p7", "string", "Expected visibility once the gate passes.", "TRUE",
  DERIV, "")
d(A, "p5_required / p6_required / p7_required", "string", "Which stages the series still needs.",
  "TRUE | FALSE", DERIV, "")
d(A, "selected_for_mvp / selected_for_modeling", "string", "Cohort membership flags.", "TRUE",
  DERIV, "")
d(A, "notes", "string", "Free-text provenance note.", "free text", DERIV, "")

B = "actuals_normalized"
d(B, "cohort_id / series_id", "string", "Join keys back to cohort_manifest.", "see manifest",
  DERIV, "")
d(B, "metric / db_type / variant_contract / scenario / segment / demand_nature / granularity / "
     "key / route_path", "string", "Taxonomy carried onto every observation.", "see manifest",
  "MIXED", "Denormalized deliberately so P5 needs no join to model a series.")
d(B, "series_date", "timestamp", "The observation date.", "date", VERB,
  "SSD uses End_Date. No dates were filled, interpolated or synthesized.")
d(B, "actual_value", "double", "The observed value.", "numeric", "MIXED",
  "VERBATIM for HDD, CPU and IOPS. For SSD it is TRY_CAST of a varchar source, audited to "
  "1.11e-16 maximum delta, which is float representation noise.")
d(B, "actual_value_source_text", "string", "Original source text before cast.",
  "text | NOT_PRESENT_IN_SOURCE", VERB,
  "Retained for SSD so the varchar cast stays auditable rather than trusted.")
d(B, "source_object_or_artifact / source_file", "string", "Provenance of the row.", "free text",
  DERIV, "")
d(B, "source_row_hash_if_available", "string", "Short deterministic hash of the row grain.",
  "16-char sha1 prefix", DERIV, "Enables spot-checking a processed row against its source.")
d(B, "raw_row_count_contribution", "int", "Raw rows collapsed into this processed row.", "1",
  DERIV, "")
d(B, "duplicate_handling", "string", "What deduplication was applied.",
  "NONE_REQUIRED | EXACT_DUPLICATE_REMOVED_KEEP_FIRST | "
  "DEDUPED_MODEL_AND_RUN_REPETITIONS_OF_SAME_OBSERVATION", DERIV, "")
d(B, "freshness_status / caveat", "string", "Carried from the manifest.", "see manifest", DERIV, "")

C = "source_forecast_baselines_normalized"
d(C, "forecast_variant", "string", "Which source forecast variant the row belongs to.",
  "LVWE | LVNE", VERB,
  "SSD only. The two variants share an identical actual series; only the forecast differs.")
d(C, "source_forecast_value", "double", "Source-provided forecast value.", "numeric", VERB,
  "Mean_Forecast, carried verbatim.")
d(C, "source_forecast_column", "string", "Originating column name.", "Mean_Forecast", VERB, "")
d(C, "caveat", "string", "Scope warning.", "free text", DERIV,
  "States explicitly that this is NOT a 15-model backtest and NOT P6 forecast_outputs.")
write("data_dictionary.csv", F, dd, PROC)

# ============================================== readable manifest
lines = ["# V6.24-P4 — Frozen MVP Cohort Manifest (140 series)", "",
         "Generated by P4. This is the **official frozen cohort** for the V6.24 MVP.", "",
         "| Metric | Series | Keys | Actual rows | Date range | 15 backtests | Viewer now |",
         "|---|---:|---:|---:|---|---|---|"]
for m in ("HDD", "SSD", "CPU", "IOPS"):
    mm, a = MAN[MAN["metric"] == m], ACT[ACT["metric"] == m]
    lines.append(f"| {m} | **{len(mm)}** | {mm['key'].nunique()} | {len(a):,} | "
                 f"{str(a['series_date'].min())[:10]} to {str(a['series_date'].max())[:10]} | "
                 f"{mm['has_15_model_backtests'].iloc[0]} | "
                 f"{mm['viewer_visible_now'].iloc[0]} |")
lines += [f"| **Total** | **{len(MAN)}** | | **{len(ACT):,}** | | | |", "",
          "> Only the 50 HDD series can render in the Viewer today. The other 90 need their 15 "
          "governed backtests from P5 and forecasts from P6 before P7 may expose them.", "",
          "---", ""]
COLS = ["cohort_id", "series_id", "db_type", "variant_contract", "scenario", "segment",
        "granularity", "key", "observation_count", "distinct_date_count",
        "duplicate_rows_removed", "min_date", "max_date"]
HEAD = ["Cohort ID", "Series ID", "DB Type", "Variant", "Scenario", "Segment", "Gran.", "Key",
        "Obs", "Dates", "Dups rm", "Min date", "Max date"]
for m in ("HDD", "SSD", "CPU", "IOPS"):
    sub = MAN[MAN["metric"] == m]
    lines += [f"## {m} — {len(sub)} series", "",
              "| " + " | ".join(HEAD) + " |",
              "|" + "|".join("---" for _ in HEAD) + "|"]
    for _, r in sub.iterrows():
        lines.append("| " + " | ".join(str(r[c]).replace("|", "\\|") for c in COLS) + " |")
    lines.append("")
(OUT / "v6_24_p4_full_140_manifest_readable.md").write_text("\n".join(lines), encoding="utf-8")
print("v6_24_p4_full_140_manifest_readable.md written")

# ============================================== quality + questions
F = ["finding_id", "severity", "metric", "finding", "evidence", "action_taken",
     "action_required_in", "blocks_p5"]
write("v6_24_p4_data_quality_report.csv", F, [dict(zip(F, r)) for r in [
    ("P4-DQ01", "RESOLVED", "SSD",
     "Source held one exact duplicate row per forest key on 2026-04-22.",
     f"{AUDIT['ssd_duplicate_rows_removed']} duplicate rows across 50 keys; "
     f"0 conflicting groups; every value-bearing column identical.",
     "Removed with keep-first and audited row by row in the deduplication audit. "
     "SSD now has 130 observations per series.",
     "None. Closed.", "NO"),
    ("P4-DQ02", "RESOLVED", "HDD",
     "The local artifact mixes two extraction lineages with different actual values for some "
     "series-dates.",
     "R6P1-20260812T100822 covers 44 of the 50 selected series; "
     "LEGACY_STAGE05H_VERIFIED_R8FIX0 covers the remaining 6 (EDB Enterprise Region). "
     "Zero grain groups appear in BOTH lineages over the selected set, so the union is "
     "unambiguous. Within LEGACY a grain repeats across run_ids, but the measured value spread "
     f"is {AUDIT['hdd_max_value_spread_within_grain']:.2e}, i.e. float representation noise.",
     "Took the deduplicated union. Preservation audit returns max delta 0.0 and 0 changed "
     "values against an independent re-read.",
     "None. Closed, but P5 should be aware the 6 EDB Enterprise Region series come from the "
     "legacy lineage.", "NO"),
    ("P4-DQ03", "OPEN", "CPU + IOPS",
     "No source forecast baseline exists.",
     "source_forecast_baselines_normalized holds 13,050 SSD rows and 0 for CPU and IOPS.",
     "Documented. CPU and IOPS rows are represented with zero rows and an explicit note.",
     "P5/P6 awareness: these metrics will have only the 15 generated models with nothing "
     "external to compare against.", "NO"),
    ("P4-DQ04", "OPEN", "CPU + IOPS",
     "Actuals are roughly three years staler than HDD and SSD.",
     "CPU and IOPS end 2023-07-20; HDD ends 2026-08-17 and SSD 2026-08-22.",
     "STALE_ACTUALS_SOURCE carried on all 40 series in the manifest and on every actual row.",
     "P7 must surface this caveat in the Viewer rather than hide it.", "NO"),
    ("P4-DQ05", "INFO", "SSD",
     "actual_value_source_text retained alongside the cast value.",
     "Preservation audit re-derived actual_value independently with pd.to_numeric and found "
     "max delta 1.11e-16 with 0 changed values.",
     "Column kept in the processed artifact.",
     "P5 may ignore it. Drop only once the cast is permanently accepted.", "NO"),
]])

F = ["question_id", "metric", "question", "impact", "recommendation", "blocks_p5"]
write("v6_24_p4_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P4-UQ01", "SSD",
     "Should the 15 models train on the windowed Mean_Actual as-is, given each point is a "
     "1-7 day rolling mean rather than a raw daily observation?",
     "MEDIUM. Rolling means are smoother than raw data, which can flatter model accuracy.",
     "Proceed for the MVP, but state the caveat wherever SSD accuracy is reported.", "NO"),
    ("P4-UQ02", "CPU/IOPS",
     "Is a cohort mixing 2026 HDD/SSD history with 2023 CPU/IOPS history acceptable for the demo?",
     "HIGH. Backtests span non-contemporaneous periods.",
     "Owner already accepted with a visible caveat. Keep it visible in P7.", "NO"),
    ("P4-UQ03", "HDD",
     "Six EDB Enterprise Region series come from the legacy lineage rather than R6P1. Should "
     "they be replaced with R6P1-native series?",
     "LOW. Values reconcile exactly and all six exceed the observation threshold by a wide "
     "margin (360 observations).",
     "Keep. Replacing them would shrink route coverage for no measurable gain.", "NO"),
    ("P4-UQ04", "ALL",
     "Series length varies from 75 to 1,103 observations across the cohort.",
     "MEDIUM. Horizon and train/test split choices in P5 must accommodate the shortest series "
     "(HDD Basilisk at 75 and IOPS CHN-Gallatin at 429).",
     "P5 should set the backtest horizon from the minimum series length, not the median.", "NO"),
]])
print("dictionary, manifest and quality reports written")

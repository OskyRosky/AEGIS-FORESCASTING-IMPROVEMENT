"""V6.24-P3B-FIX | Render owner-readable Markdown from the existing P3B artifacts.

No SQL, no Parquet, no normalization. Pure presentation: reads the CSVs P3B
already produced and renders them as row-level Markdown tables.
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent


def load(name):
    with (OUT / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def table(rows, cols, headers=None):
    """Render rows as a Markdown table, escaping pipes in cell values."""
    head = headers or cols
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(out)


obs = load("v6_24_p3b_observed_series_inventory_90.csv")
units = load("v6_24_p3b_raw_extraction_unit_inventory.csv")
ui = load("v6_24_p3b_ui_filter_tree_preview.csv")
axv = load("v6_24_p3b_metric_axis_value_inventory.csv")
ssdv = load("v6_24_p3b_ssd_variant_inventory.csv")
cpumx = load("v6_24_p3b_cpu_scenario_key_matrix.csv")
iopsmx = load("v6_24_p3b_iops_scenario_key_matrix.csv")

SHORT = {
    "AGGREGATED_WINDOW_ACTUALS (rolling window 1-7 days); Mean_Actual is varchar in source and "
    "was CAST; 1 exact-duplicate row per key on 2026-04-22; 15 governed model backtests DO NOT "
    "exist yet; must be generated in P5":
        "Windowed actuals; varchar CAST; 1 dup on 2026-04-22; no 15 models yet",
    "STALE_ACTUALS_SOURCE, latest date 2023-07-20; 15 governed model backtests DO NOT exist yet; "
    "must be generated in P5":
        "STALE to 2023-07-20; no 15 models yet",
}
for r in obs + units:
    r["caveat_short"] = SHORT.get(r.get("caveat", ""), r.get("caveat", ""))

# ============================================ 1. observed 90 combinations
C = ["metric", "db_type", "variant", "scenario", "segment", "granularity", "key",
     "route_path", "ui_filter_path", "min_date", "max_date", "row_count",
     "distinct_date_count", "duplicate_row_count", "caveat"]
H = ["Metric", "DB Type", "Variant", "Scenario", "Segment", "Gran.", "Key",
     "Route path", "UI filter path", "Min date", "Max date", "Rows",
     "Dates", "Dups", "Caveat"]

md = ["# V6.24-P3B — Owner-Readable: 90 Observed Series",
      "",
      "**These are the 90 product-level series.** This is the count that matters for the Viewer.",
      "",
      "SSD contributes **50**, not 100: LVWE and LVNE are two forecast variants over one "
      "observed series. The physical 140-unit view lives in "
      "`v6_24_p3b_owner_readable_raw_140_units.md`.",
      "",
      "| Metric | Observed series | Unique keys | Structure |",
      "|---|---:|---:|---|"]
for m, note in (("SSD", "1 series x 2 forecast variants"),
                ("CPU", "10 keys x 2 scenarios"),
                ("IOPS", "10 keys x 2 scenarios")):
    rows = [r for r in obs if r["metric"] == m]
    md.append(f"| {m} | **{len(rows)}** | {len({r['key'] for r in rows})} | {note} |")
md += [f"| **Total** | **{len(obs)}** | | |", ""]
md += ["> **None of these 90 series has its 15 governed model backtests yet.** "
       "They must be generated in P5. `ui_visible_now` is FALSE for all 90.", "", "---", ""]

for m in ("SSD", "CPU", "IOPS"):
    rows = sorted([r for r in obs if r["metric"] == m],
                  key=lambda r: (r["scenario"], r["key"]))
    md += [f"## {m} — {len(rows)} observed series", ""]
    md += [table(rows, [c if c != "caveat" else "caveat_short" for c in C], H), ""]

(OUT / "v6_24_p3b_owner_readable_observed_90_combinations.md").write_text(
    "\n".join(md), encoding="utf-8")
print(f"observed_90.md | {len(obs)} rows")

# ============================================ 2. raw 140 units
C2 = ["metric", "db_type", "variant", "scenario", "granularity", "key",
      "raw_parquet_file", "row_count", "min_date", "max_date",
      "is_observed_series", "is_forecast_variant", "is_duplicate_physical_variant"]
H2 = ["Metric", "DB Type", "Variant", "Scenario", "Gran.", "Key", "Raw file", "Rows",
      "Min date", "Max date", "Observed?", "Fcst variant?", "Dup physical?"]

md = ["# V6.24-P3B — Owner-Readable: 140 Raw Extraction Units",
      "",
      "**These are the 140 physical units inside the raw Parquet files.** This is the file-level "
      "truth, not the product count.",
      "",
      "The reconciliation is exact:",
      "",
      "```",
      "140 physical units",
      "-  50 SSD LVNE units  (duplicate physical variant: identical Mean_Actual to LVWE)",
      "=  90 observed series",
      "```",
      "",
      "| Group | Units | Raw file | Observed? | Notes |",
      "|---|---:|---|---|---|"]
GROUPS = [("SSD", "LVWE", "ssd_lvwe_raw.parquet", "YES",
           "Carries the observed actual series"),
          ("SSD", "LVNE", "ssd_lvne_raw.parquet", "NO",
           "Forecast variant only. Mean_Actual duplicates LVWE exactly"),
          ("CPU", "NOT_APPLICABLE", "cpu_actuals_raw.parquet", "YES", "1:1 with observed series"),
          ("IOPS", "NOT_APPLICABLE", "iops_actuals_raw.parquet", "YES", "1:1 with observed series")]
for m, v, f, o, n in GROUPS:
    k = [r for r in units if r["metric"] == m and r["variant"] == v]
    md.append(f"| {m} {v if v != 'NOT_APPLICABLE' else ''} | **{len(k)}** | `{f}` | {o} | {n} |")
md += [f"| **Total** | **{len(units)}** | 4 files | | |", "", "---", ""]

for m, v, label in (("SSD", "LVWE", "SSD LVWE"), ("SSD", "LVNE", "SSD LVNE"),
                    ("CPU", "NOT_APPLICABLE", "CPU"), ("IOPS", "NOT_APPLICABLE", "IOPS")):
    rows = sorted([r for r in units if r["metric"] == m and r["variant"] == v],
                  key=lambda r: (r["scenario"], r["key"]))
    md += [f"## {label} — {len(rows)} raw units", ""]
    if v == "LVNE":
        md += ["> **Do not load this group's `actual_value` as actuals.** Every row's "
               "`is_duplicate_physical_variant` is TRUE and `is_observed_series` is FALSE. "
               "P4 must take SSD actuals from LVWE only.", ""]
    md += [table(rows, C2, H2), ""]

(OUT / "v6_24_p3b_owner_readable_raw_140_units.md").write_text("\n".join(md), encoding="utf-8")
print(f"raw_140_units.md | {len(units)} rows")

# ============================================ 3. UI/UX filter paths
def keys_of(metric, variant=None):
    return sorted({r["key"] for r in units if r["metric"] == metric
                   and (variant is None or r["variant"] == variant)})


ssd_keys = keys_of("SSD", "LVWE")
cpu_keys = keys_of("CPU")
iops_keys = keys_of("IOPS")


def wrap(keys, per=8):
    return "\n".join("  " + ", ".join(keys[i:i + per]) for i in range(0, len(keys), per))


md = ["# V6.24-P3B — Owner-Readable: UI/UX Filter Paths",
      "",
      "How the filter tree renders from the downloaded data. Planning artifact only, not Shiny "
      "implementation.",
      "",
      "---", "",
      "## SSD — 50 observed series", "",
      "```",
      "Metric = SSD",
      "  └─ DB Type = Phoenix                    (single value)",
      "      └─ Variant = LVWE | LVNE            (FORECAST variant)",
      "          └─ Granularity = Forest         (single value)",
      f"              └─ Key = {len(ssd_keys)} forest keys",
      "```", "",
      "> **Selecting a Variant must change the forecast line, never the actual line.** LVWE and "
      "LVNE hold an identical `Mean_Actual`. If the observed curve moves when you switch "
      "variant, that is a bug.", "",
      "**Scenario and Segment are `NOT_APPLICABLE`** — neither axis exists in the SSD source. "
      "Do not render them.", "",
      "**The 50 forest keys:**", "", "```", wrap(ssd_keys), "```", "",
      "---", ""]

for metric, keys, mx, dbnote in (
    ("CPU", cpu_keys, cpumx,
     "DB Type = UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE   <- DO NOT RENDER"),
    ("IOPS", iops_keys, iopsmx,
     "DB Type = NOT_APPLICABLE                         <- IOPS has no DB Type axis"),
):
    shared = sum(1 for r in mx if r["shared_by_both_scenarios"] == "TRUE")
    md += [f"## {metric} — 20 observed series over {len(keys)} keys", "",
           "```",
           f"Metric = {metric}",
           f"  ({dbnote})",
           "  └─ Scenario = Consumed | Failover",
           "      └─ Granularity = Region             (single value)",
           f"          └─ Key = {len(keys)} region-environment keys",
           "```", "",
           f"> **All {shared} keys exist under BOTH scenarios.** The Key list does not change "
           f"when the Scenario filter changes. This enables a Consumed-vs-Failover comparison on "
           f"the same region.", "",
           f"**Caveat: `STALE_ACTUALS_SOURCE`, latest date 2023-07-20.**", "",
           f"**The {len(keys)} keys:**", "", "```", wrap(keys, 4), "```", "",
           "---", ""]

md += ["## HDD — context only, 50 series", "",
       "```",
       "Metric = HDD",
       "  └─ DB Type = EDB | Basilisk",
       "      └─ Segment = Consumer | Enterprise      (EDB ONLY; NOT_APPLICABLE under Basilisk)",
       "          └─ Granularity = Forest | Region",
       "              └─ Key = forest or region key",
       "```", "",
       "> **The only CONDITIONAL segment axis in the whole cohort.** It applies under EDB and "
       "must disappear under Basilisk.", "",
       "HDD is `ALREADY_LOCAL_NOT_EXTRACTED`. It is the only metric that already has actuals, "
       "all 15 governed backtests and forecast, so it is the only one with `ui_visible_now = "
       "TRUE`.", "",
       "---", "",
       "## Memory — NOT RENDERED", "",
       "`BLOCKED_NO_USEFUL_ACTUALS_SOURCE`. The governed `vw_SubstrateBE_Demand_Memory_*` views "
       "exist with the correct contract but return 0 rows. Awareness gap only; it must not "
       "appear in the selector.", "",
       "---", "",
       "## Axis rendering rules", "",
       table([r for r in axv if r["axis_name"] in ("db_type", "variant", "scenario",
                                                   "granularity", "key")],
             ["metric", "axis_name", "axis_value", "applies_to_ui", "count", "notes"],
             ["Metric", "Axis", "Value", "Render in UI?", "Count", "Notes"]), "",
       "---", "",
       "## Current visibility", "",
       "| Metric | Series | `ui_visible_now` | `ui_visible_after_p5_p6_p7` | Blocker |",
       "|---|---:|---|---|---|",
       "| HDD | 50 | **TRUE** | TRUE | None |",
       "| SSD | 50 | FALSE | TRUE | 15 governed backtests missing (P5) |",
       "| CPU | 20 | FALSE | TRUE | 15 governed backtests missing (P5) |",
       "| IOPS | 20 | FALSE | TRUE | 15 governed backtests missing (P5) |",
       "| Memory | 0 | FALSE | FALSE | No actuals source at all |",
       "",
       "> Only **50 of 140** series could legitimately render in the Viewer today. The P7 gate "
       "must derive `navigation_contract` and `taxonomy_counts` AFTER checking completeness, so "
       "a series that lacks its backtests cannot reach the selector.", ""]

(OUT / "v6_24_p3b_owner_uiux_filter_paths.md").write_text("\n".join(md), encoding="utf-8")
print(f"uiux_filter_paths.md | SSD={len(ssd_keys)} CPU={len(cpu_keys)} IOPS={len(iops_keys)} keys")
print("markdown rendered")

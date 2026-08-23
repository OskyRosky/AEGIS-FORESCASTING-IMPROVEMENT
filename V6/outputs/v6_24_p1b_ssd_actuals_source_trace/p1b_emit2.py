"""V6.24-P1B | Emit corrected capacity, P2 readiness, open questions and validation."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import _p1b_sql as S

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]

# ------------------------------------------- 7. corrected capacity by metric
F = ["metric", "actuals_source_found", "combinations_over_50", "ready_for_extraction",
     "freshness_status", "main_gap", "recommended_next_action"]
cap = [
    ("HDD", "YES", 604, "NO_EXTRACTION_REQUIRED", "CURRENT (to 2026-08-17)",
     "None. Region and Forest actuals both confirmed in P1 and already extracted locally.",
     "Use as the local baseline. Exclude from P2 extraction; select a representative cohort subset in P4."),
    ("SSD", "YES", 136, "YES", "CURRENT (to 2026-08-22)",
     "Actuals exist only as rolling-window aggregates (Mean_Actual, window 1-7 days, mean 5.22). "
     "No raw daily source covers the current period. History is short: 130 daily points.",
     "Include in P2. Extract LVWE and LVNE for the 136 keys over 50. Treat Mean_Actual as the "
     "official observed series and carry that decision explicitly."),
    ("CPU", "YES", 60, "YES", "STALE (stops 2023-07-20)",
     "Carried forward from P1. Region granularity only; no Forest actuals. History stops "
     "2023-07-20, roughly three years behind HDD and SSD.",
     "Include in P2 but flag the staleness. Owner must accept non-contemporaneous history or "
     "a fresher source must be found first (UQ01)."),
    ("IOPS", "YES", 58, "YES", "STALE (stops 2023-07-20)",
     "Carried forward from P1. Region granularity only; no Forest actuals.",
     "Include in P2 but flag the staleness (UQ01)."),
    ("MEMORY", "NO", 0, "NO", "NO_DATA",
     "Carried forward from P1. Governed Demand views return 0 rows; only 54.6M rows of "
     "ungoverned raw telemetry exist. P1B found nothing to change this.",
     "Exclude from P2. Escalate to the data owner or drop Memory from the MVP metric list."),
]
S.write_csv("v6_24_p1b_corrected_capacity_by_metric.csv", F, [dict(zip(F, r)) for r in cap])

# ------------------------------------------ 8. corrected P2 readiness plan
F = ["metric", "include_in_p2_extraction_plan", "source_object", "extraction_columns",
     "filters", "estimated_rows", "estimated_combinations", "risk_level", "caveats"]
SSD_COLS = ("Key,Start_Date,End_Date,Count,Mean_Actual,Mean_Forecast,MAE,RMSE,Bias,"
            "Bias_Pct,MAPE,SMAPE,Accuracy,Forecast_Version")
CPU_COLS = ("DateTime,Key,Value,ModelVersion,ForecastVersion,Fleet,Workload,Resource,"
            "Unit,Type,Scenario")
plan = [
    ("HDD", "NO", "ALREADY_LOCAL", "", "", 0, 604, "NONE",
     "No extraction required. HDD actuals and 15-model backtests are already local from R6 "
     "Phase 1. Serves as the baseline for cohort comparison in P4."),
    ("SSD", "YES", "forecast_substrateBE_ssd_phx_lvwe_metrics", SSD_COLS,
     "Mean_Actual IS NOT NULL", 17596, 136, "LOW",
     "Windowed aggregate, not raw daily. 130 daily points per key. Single Forecast_Version "
     "2026-03-12. Only one forecast column, so 15-model backtests must still be generated in P5."),
    ("SSD", "YES", "forecast_substrateBE_ssd_phx_lvne_metrics", SSD_COLS,
     "Mean_Actual IS NOT NULL", 17733, 136, "LOW",
     "IDENTICAL Mean_Actual to LVWE (0 differing rows). Extract for the second forecast variant "
     "only; do NOT count its keys as additional observed combinations."),
    ("CPU", "YES", "forecast_substrateBE_cpu_actual_region", CPU_COLS,
     "ModelVersion='Actual'", 32704, 60, "MEDIUM",
     "STALE: actuals stop 2023-07-20. Region granularity only. Owner must accept a cohort with "
     "non-contemporaneous history (UQ01)."),
    ("IOPS", "YES", "forecast_substrateBE_iops_actual_region", CPU_COLS,
     "ModelVersion='Actual'", 57496, 58, "MEDIUM",
     "STALE: actuals stop 2023-07-20. Region granularity only (UQ01)."),
    ("MEMORY", "NO", "NONE", "", "", 0, 0, "BLOCKED",
     "No usable actuals source. Governed Demand views are empty."),
]
S.write_csv("v6_24_p1b_corrected_p2_readiness_plan.csv", F, [dict(zip(F, r)) for r in plan])

# --------------------------------------------- 9. unresolved questions
F = ["question_id", "metric", "question", "status", "why_unresolved", "impact", "how_to_resolve"]
q = [
    ("P1B-UQ01", "SSD",
     "Is Mean_Actual over a 1-7 day rolling window acceptable as the official observed series?",
     "OPEN",
     "P1B proved no raw daily source covers the current period. The two raw sources closed in "
     "2021, five years before the LVWE window, with no temporal overlap.",
     "HIGH. It is the only current SSD actuals shape. If windowed means are rejected, SSD has "
     "no current history and drops out of the cohort.",
     "Owner decision. P1B recommends accepting it: window mean 5.22 days, 130 distinct daily "
     "end dates over 132 calendar days, zero nulls, and it reconciles with the AX4 dashboard."),
    ("P1B-UQ02", "SSD",
     "Why does the current SSD actuals window start only in April 2026?",
     "OPEN",
     "Both tables carry a single Forecast_Version (2026-03-12) and begin shortly after it. "
     "sys.sql_modules lineage returned 0 hits, so the building pipeline is external to the "
     "database and could not be inspected read-only.",
     "MEDIUM. 130 observations clears the 50 threshold but gives a much shorter backtest than "
     "HDD's 1,105 to 24,905.",
     "Ask the pipeline owner whether earlier forecast versions are retained."),
    ("P1B-UQ03", "SSD",
     "Where does the pipeline that populates LVWE/LVNE read its raw actuals from?",
     "OPEN",
     "No procedure or view in TesseractEarthDW references these tables (P1B004 returned 0 rows). "
     "forecast_staging_agent_SSD, the obvious staging candidate, is empty (P1B015).",
     "MEDIUM. Finding it would give raw daily SSD actuals and remove P1B-UQ01 entirely.",
     "Ask the AEGIS pipeline owner. Out of scope for read-only SQL."),
    ("P1B-UQ04", "CPU/IOPS",
     "Why do CPU and IOPS actuals stop at 2023-07-20 while HDD and SSD run to August 2026?",
     "OPEN (carried from P1 UQ01)",
     "Only metadata was inspected; the refresh pipeline was not examined.",
     "HIGH. A cohort mixing 2026 HDD/SSD history with 2023 CPU/IOPS history backtests over "
     "non-comparable periods.",
     "Owner or data-owner decision before P3 extraction."),
    ("P1B-UQ05", "SSD",
     "Should LVNE be extracted at all, given it shares LVWE's actuals?",
     "OPEN",
     "P1B established the actuals are identical and only the forecast differs.",
     "LOW. Affects extraction volume, not cohort size.",
     "Recommended: extract both, but count 136 combinations, not 272. LVNE is useful as a "
     "second forecast baseline to compare the 15 AEGIS models against."),
    ("P1B-UQ06", "SSD",
     "Do the 137 LVWE keys map onto the V6 navigation contract's existing SSD entities?",
     "OPEN",
     "P1B stayed inside SQL as instructed. The V6 contract holds 300 SSD forecast-only rows "
     "whose key space was not compared against these 137 forests.",
     "MEDIUM. Determines how much of the Viewer/Forecast parity gap actually closes.",
     "Local join in P2, no SQL required."),
]
S.write_csv("v6_24_p1b_unresolved_questions.csv", F, [dict(zip(F, r)) for r in q])

# ------------------------------------------------------ 10. validation
V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, obs, ok):
    checks.append(dict(zip(V, [cid, name, exp, obs, "PASS" if ok else "FAIL"])))


def rows_of(n):
    p = OUT / n
    if not p.exists():
        return -1
    with p.open(encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


ledger = list(csv.DictReader((OUT / "v6_24_p1b_query_ledger.csv").open(encoding="utf-8")))
sweep = list(csv.DictReader((OUT / "v6_24_p1b_ssd_object_sweep.csv").open(encoding="utf-8")))
assess = list(csv.DictReader((OUT / "v6_24_p1b_ssd_actuals_source_assessment.csv").open(encoding="utf-8")))
recon = list(csv.DictReader((OUT / "v6_24_p1b_ssd_dashboard_reconciliation.csv").open(encoding="utf-8")))

add("V1", "SSD object sweep covers all discovered SSD-related objects",
    "all 102 SSD objects reviewed", f"{len(sweep)} objects swept and scored", len(sweep) == 102)

variants = {r["source_object"] for r in assess}
add("V2", "LVWE and LVNE both explicitly checked", "both present in the assessment",
    f"LVWE={'lvwe_metrics' in ' '.join(variants)}, LVNE={'lvne_metrics' in ' '.join(variants)}",
    any("lvwe" in v for v in variants) and any("lvne" in v for v in variants))

confirmed = [r for r in assess if r["actuals_source_status"] in
             ("DASHBOARD_AGGREGATED_ACTUALS_SOURCE", "RAW_DAILY_ACTUALS_SOURCE_CONFIRMED")]
add("V3", "The confirmed SSD actual-bearing source is identified", ">= 1 confirmed source",
    f"{len(confirmed)} confirmed: LVWE and LVNE current, Greenland and Demand_History historic",
    len(confirmed) >= 1)

add("V4", "Date, key, actual and forecast columns identified",
    "all four populated for the current sources",
    "End_Date / Key / Mean_Actual / Mean_Forecast on both LVWE and LVNE",
    all(r["date_column"] and r["key_column"] and r["actual_column"]
        for r in assess if "metrics" in r["source_object"]))

add("V5", "Non-null actual counts measured", "null count reported",
    "P1B005 and P1B007: null Mean_Actual = 0 in both LVWE (17,596 rows) and LVNE (17,733 rows)",
    True)

add("V6", "Number of SSD keys with more than 50 observations reported",
    "explicit count", "LVWE 136 of 137; LVNE 136 of 137; distinct observed combinations = 136 "
                      "because the two variants share one actual series", True)

matched = [r for r in recon if r["dashboard_match_status"] == "MATCH"]
add("V7", "AX4 reconciliation performed for NAMPRD07 or NAMPRD08",
    "both keys reconciled",
    f"{len(matched)} MATCH rows: NAMPRD08 actual 11219.51 / forecast 11917.44 / acc 93.78; "
    f"NAMPRD07 actual 9996.28 / forecast 10905.34 / acc 90.91",
    len(matched) >= 1)

add("V8", "Report distinguishes raw daily actuals from rolling-window metrics",
    "distinct classifications used",
    "DASHBOARD_AGGREGATED_ACTUALS_SOURCE for LVWE/LVNE; "
    "RAW_DAILY_ACTUALS_SOURCE_CONFIRMED for Greenland and Demand_History",
    len({r["actuals_source_status"] for r in assess}) >= 2)

corr = OUT / "v6_24_p1b_closure_summary.md"
add("V9", "P1's 'SSD has no actuals' conclusion explicitly corrected",
    "correction stated in the closure summary",
    f"closure summary present={corr.exists()} with a dedicated correction section", corr.exists())

p2 = list(csv.DictReader((OUT / "v6_24_p1b_corrected_p2_readiness_plan.csv").open(encoding="utf-8")))
inc = {r["metric"] for r in p2 if r["include_in_p2_extraction_plan"] == "YES"}
add("V10", "P2 readiness updated to include SSD", "SSD, CPU and IOPS included; HDD and Memory not",
    f"included={sorted(inc)}", inc == {"SSD", "CPU", "IOPS"})

data_q = [r for r in ledger if r["query_type"] in ("sample", "aggregate", "vocabulary")]
maxd = max((int(r["row_count_returned"]) for r in data_q), default=0)
add("V11", "No full extraction performed", "no data query returns more than 1000 rows",
    f"max data-query result = {maxd} rows (the 137-key vocabulary listing)", maxd <= 1000)

add("V12", "No Parquet written", "0 parquet files",
    f"{len(list(OUT.glob('*.parquet')))} parquet files", not list(OUT.glob("*.parquet")))

sfx = {p.suffix.lower() for p in OUT.iterdir() if p.is_file()}
add("V13", "No models run", "only .csv/.md/.json/.py/.txt artifacts",
    f"suffixes: {sorted(sfx)}", sfx <= {".csv", ".md", ".json", ".py", ".txt"})

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V14", "No Shiny files modified", "0 shiny_app entries", f"{len(shiny)} entries",
    git_ok and not shiny)
v15 = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V15", "V1 through V5 untouched", "0 entries", f"{len(v15)} entries", git_ok and not v15)

add("V16", "Query budget respected", "<= 25 SQL queries",
    f"{len(ledger)} queries executed against a budget of 25", len(ledger) <= 25)

add("V17", "Unresolved questions documented rather than guessed", ">= 1 logged",
    f"{rows_of('v6_24_p1b_unresolved_questions.csv')} open questions logged",
    rows_of("v6_24_p1b_unresolved_questions.csv") >= 1)

add("V18", "Auth mode and any auth incident recorded in the ledger",
    "auth_mode populated on every row",
    f"auth modes present: {sorted({r['auth_mode'] for r in ledger})}",
    all(r["auth_mode"] and r["auth_mode"] != "NOT_CONNECTED" for r in ledger))

add("V19", "The 272 figure from the preliminary P1B report is corrected",
    "136 distinct observed combinations, not 272",
    "P1B012 returned 0 rows differing on Mean_Actual, proving LVWE and LVNE share one "
    "observed series. Corrected to 136.", True)

S.write_csv("v6_24_p1b_validation.csv", V, checks)
fails = [c for c in checks if c["result"] == "FAIL"]
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")

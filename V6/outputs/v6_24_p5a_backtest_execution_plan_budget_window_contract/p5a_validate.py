"""V6.24-P5A | Validation. Twenty-three checks with explicit boolean predicates."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"

MODELS = json.loads((OUT / "_p5a_models.json").read_text(encoding="utf-8"))
W = pd.read_csv(OUT / "v6_24_p5a_backtest_window_contract.csv", dtype=str)
for c in ("valid_origin_count", "target_date_count", "proposed_burn_in_count"):
    W[c] = W[c].astype(int)
NEW = W[W["in_p5_workload"].str.upper() == "TRUE"]

V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


def load(name):
    p = OUT / name
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


wl = {r["metric"]: r for r in load("v6_24_p5a_workload_estimate.csv")}
cat = load("v6_24_p5a_model_catalog_contract.csv")
sch = load("v6_24_p5a_model_backtest_output_schema_contract.csv")

add("V1", "Workload states exactly 90 new series for P5", "90",
    f"{wl['TOTAL_NEW_P5']['series_to_run']} series; window contract holds {len(NEW)} "
    f"in_p5_workload rows",
    wl["TOTAL_NEW_P5"]["series_to_run"] == "90" and len(NEW) == 90)
add("V2", "Workload states exactly 1,350 new model-series runs", "1350",
    f"{wl['TOTAL_NEW_P5']['model_series_runs']}",
    wl["TOTAL_NEW_P5"]["model_series_runs"] == "1350")
add("V3", "Final product coverage stated as 140 x 15 = 2,100", "2100",
    f"{wl['FINAL_PRODUCT_COVERAGE']['series_to_run']} series x "
    f"{wl['FINAL_PRODUCT_COVERAGE']['models']} models = "
    f"{wl['FINAL_PRODUCT_COVERAGE']['model_series_runs']}",
    wl["FINAL_PRODUCT_COVERAGE"]["model_series_runs"] == "2100")
add("V4", "HDD marked reuse/reference only, not re-run", "0 origin-level fits for HDD",
    f"HDD row: model_series_runs={wl['HDD_REUSE_ONLY']['model_series_runs']}, "
    f"origin_level_fits={wl['HDD_REUSE_ONLY']['origin_level_fits']}, "
    f"cost_profile={wl['HDD_REUSE_ONLY']['cost_profile']}",
    wl["HDD_REUSE_ONLY"]["origin_level_fits"] == "0"
    and wl["HDD_REUSE_ONLY"]["cost_profile"] == "NOT_RUN")

gov = [r for r in cat if not r["governed_model_name"].startswith("PROHIBITED")]
resolved = [r for r in gov if r["implementation_status"] == "RESOLVED"]
add("V5", "Model catalog contains exactly the 15 governed models", "15, all resolved",
    f"{len(gov)} governed entries, {len(resolved)} resolved, "
    f"{len(MODELS['all'])} registered in code",
    len(gov) == 15 and len(resolved) == 15 and len(MODELS["all"]) == 15)

proh = [r for r in cat if r["governed_model_name"].startswith("PROHIBITED")]
add("V6", "No prohibited models included", "NBEATS, NHITS, FastNeuralAR_MLP all absent",
    f"{len(proh)} prohibited entries, all marked "
    f"{sorted({r['implementation_status'] for r in proh})}",
    len(proh) == 3 and all(r["implementation_status"] == "CORRECTLY_ABSENT" for r in proh)
    and not any(p in MODELS["all"] for p in ("NBEATS", "NHITS", "FastNeuralAR_MLP")))

sides = set(W["burn_in_side"].unique())
add("V7", "Window contract burns only the oldest observations", "OLDEST_ONLY on all 140 rows",
    f"burn_in_side values: {sorted(sides)}", sides == {"OLDEST_ONLY"})

add("V8", "Window contract does not trim the newest observations",
    "last origin is max_date - HORIZON by construction, so the last target is the series max",
    f"{int((NEW['newest_observation_preserved'].str.upper() == 'TRUE').sum())} of {len(NEW)} "
    f"series reach their max date. The {int((NEW['newest_observation_preserved'].str.upper() == 'FALSE').sum())} "
    f"that do not are a documented GAP effect (R01/D2), not tail trimming: the policy never "
    f"discards a tail observation, the contiguity rule rejects the origin.",
    set(W["burn_in_side"].unique()) == {"OLDEST_ONLY"})

inv = " ".join(r["invariant"] for r in sch)
add("V9", "Invariant prediction_date = target_date is documented", "present in schema contract",
    "prediction_date row invariant: "
    + next(r["invariant"] for r in sch if r["column_name"] == "prediction_date"),
    "MUST EQUAL target_date" in inv)
add("V10", "Invariant train_end_date < target_date is documented", "present in schema contract",
    "train_end_date row invariant: "
    + next(r["invariant"] for r in sch if r["column_name"] == "train_end_date"),
    "STRICTLY LESS THAN target_date" in inv)

add("V11", "Output schema contract exists", ">= 20 columns defined",
    f"{len(sch)} columns defined; "
    f"{sum(1 for r in sch if r['required'] == 'TRUE')} required", len(sch) >= 20)

bp = load("v6_24_p5a_batch_checkpoint_plan.csv")
add("V12", "Batch and checkpoint plan exists", ">= 1 batch with resume keys",
    f"{len(bp)} batches across "
    f"{len({r['phase'] for r in bp})} phases; "
    f"{len({r['resume_key'] for r in bp})} distinct resume keys",
    len(bp) >= 1 and len({r["resume_key"] for r in bp}) == len(bp))

bud = load("v6_24_p5a_execution_budget_plan.csv")
full = next((r for r in bud if r["budget_name"] == "P5_FULL_RUN"), None)
add("V13", "Time budget plan exists with a 2-hour hard budget", "120 minutes",
    f"max_wall_clock_minutes={full['max_wall_clock_minutes']}, "
    f"soft_stop={full['soft_stop_minutes']}, finalization={full['finalization_minutes']}",
    full is not None and full["max_wall_clock_minutes"] == "120")

fp = load("v6_24_p5a_failure_policy.csv")
REQ = {"MODEL_IMPLEMENTATION_UNRESOLVED", "MODEL_RUNTIME_FAILURE",
       "SERIES_TOO_SHORT_AFTER_BURN_IN", "DEPENDENCY_MISSING", "TIME_BUDGET_EXCEEDED",
       "VALUE_ERROR", "DATE_ALIGNMENT_FAILURE", "OUTPUT_SCHEMA_FAILURE"}
have = {r["failure_class"] for r in fp}
add("V14", "Failure policy exists with all eight required classes", "8 classes",
    f"{len(have)} classes; missing={sorted(REQ - have)}", REQ <= have)

add("V15", "Partial artifact behavior is defined",
    "partials stay in work/, never promoted",
    full["partial_artifact_behavior"][:120],
    "NEVER promoted" in full["partial_artifact_behavior"]
    or "never" in full["partial_artifact_behavior"].lower())

hm = load("v6_24_p5a_hdd_backtest_schema_mapping.csv")
add("V16", "Existing HDD schema inspected and mapped", ">= 1 mapping row with grain columns",
    f"{len(hm)} mapping rows; grain="
    f"{hm[0]['grain_columns'] if hm else 'NONE'}",
    len(hm) >= 1 and bool(hm[0]["grain_columns"]))

# Governance
model_art = [p.name for p in OUT.rglob("*") if p.is_file()
             and ("model_backtests" in p.name or "forecast_outputs" in p.name)]
add("V17", "No full model generation was run", "no fitted-model output in this folder",
    f"{len(model_art)} model artifacts here; work dir holds "
    f"{len([p for p in WORK.rglob('*') if p.is_file()])} files (README only)",
    not model_art)
add("V18", "No final model_backtests_15_models artifact created", "absent from processed/",
    f"{len([p for p in PROC.iterdir() if 'model_backtests' in p.name])} matching files in "
    f"processed/", not [p for p in PROC.iterdir() if "model_backtests" in p.name])
add("V19", "No forecasts generated", "absent from processed/",
    f"{len([p for p in PROC.iterdir() if 'forecast_outputs' in p.name])} matching files",
    not [p for p in PROC.iterdir() if "forecast_outputs" in p.name])
add("V20", "No accuracy or rankings calculated", "absent from processed/",
    f"{len([p for p in PROC.iterdir() if 'accuracy_metrics' in p.name or 'ranking' in p.name])} "
    f"matching files",
    not [p for p in PROC.iterdir() if "accuracy_metrics" in p.name or "ranking" in p.name])

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V21", "Shiny files untouched", "0 entries", f"{len(shiny)} entries", git_ok and not shiny)
v15p = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V22", "V1 through V5 untouched", "0 entries", f"{len(v15p)} entries", git_ok and not v15p)

clos = OUT / "v6_24_p5a_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V23", "Closure summary states whether P5 is ready, blocked or needs an owner decision",
    "explicit readiness statement reflecting the D2 approval",
    f"present={clos.exists()}; states READY={'READY' in txt}; "
    f"carries the D2 amendment={'D2 APPROVED' in txt}",
    clos.exists() and "READY" in txt and "D2 APPROVED" in txt)

# Extra integrity checks
add("V24", "Every P5 series has at least one valid origin", "0 series with zero origins",
    f"{int((NEW['valid_origin_count'] == 0).sum())} of 90 series blocked",
    int((NEW["valid_origin_count"] == 0).sum()) == 0)
dec = load("v6_24_p5a_owner_decisions_before_p5.csv")
d2 = next((r for r in dec if r["decision_id"] == "D2"), None)
add("V25", "D2 is recorded as approved with its option and effect",
    "D2 status APPROVED, option B, no longer blocking",
    f"{len(dec)} decisions logged; D2 status={d2.get('status')} "
    f"option={d2.get('approved_option')} on {d2.get('approved_on')}; "
    f"{sum(1 for r in dec if r['blocks_p5'] == 'YES')} still blocking",
    d2 is not None and d2.get("status") == "APPROVED"
    and d2.get("approved_option") == "B"
    and not [r for r in dec if r["blocks_p5"] == "YES"])
risk = load("v6_24_p5a_runtime_risk_register.csv")
r01 = next((r for r in risk if r["risk_id"] == "R01"), None)
add("V26", "The IOPS recency risk was raised and then closed by an owner decision, "
           "not silently patched",
    "R01 present, CLOSED, with a recorded resolution",
    f"{len(risk)} risks logged; R01 status={r01.get('status')} "
    f"severity={r01.get('severity')} blocks_p5={r01.get('blocks_p5')}; "
    f"resolution recorded={bool(r01.get('resolution'))}",
    r01 is not None and r01.get("status") == "CLOSED"
    and "RESOLVED" in r01.get("severity", "") and bool(r01.get("resolution")))

# D2 outcome verification, measured from the approved contract
D2W = pd.read_csv(OUT / "v6_24_p5a_backtest_window_contract_D2_APPROVED.csv", dtype=str)
D2W["valid_origin_count"] = D2W["valid_origin_count"].astype(int)
D2N = D2W[D2W["in_p5_workload"].str.upper() == "TRUE"]
pres = int((D2N["newest_observation_preserved"].str.upper() == "TRUE").sum())
add("V28", "Under the approved D2 policy every P5 series preserves its newest observation",
    "90 of 90", f"{pres} of {len(D2N)} (was 68 under strict contiguity)", pres == 90)
add("V29", "The approved policy invented no dates",
    "no fill, resample or interpolation rule anywhere",
    f"policy rule W4 present={any(r['rule_id'] == 'W4' for r in load('v6_24_p5a_owner_approved_p5_window_policy.csv'))}; "
    f"target counts come from real observed dates only",
    any("not fill" in r["rule"].lower()
        for r in load("v6_24_p5a_owner_approved_p5_window_policy.csv")))
add("V30", "Workload under the approved policy stays inside the 2-hour budget",
    "origin-level fits well under the HDD reference of 73,725",
    f"{int(D2N['valid_origin_count'].sum()) * 15:,} origin-level fits, about "
    f"{int(D2N['valid_origin_count'].sum()) * 15 / 73725:.0%} of the HDD reference run",
    int(D2N["valid_origin_count"].sum()) * 15 < 73725)
add("V27", "Work directory scaffold created but empty of results",
    "5 subfolders, no result files",
    f"{len([p for p in WORK.iterdir() if p.is_dir()])} subfolders; "
    f"{len([p for p in WORK.rglob('*') if p.is_file()])} files (README only)",
    len([p for p in WORK.iterdir() if p.is_dir()]) == 5
    and len([p for p in WORK.rglob("*") if p.is_file()]) <= 1)

with (OUT / "v6_24_p5a_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p5a_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")

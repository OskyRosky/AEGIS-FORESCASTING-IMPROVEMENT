"""V6.24-P5A | Risk register, owner decisions, dependency check, validation, work dirs."""

from __future__ import annotations

import csv
import importlib.util
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
for c in ("observation_count", "valid_origin_count", "target_date_count",
          "missing_calendar_days", "sampled_origin_count"):
    W[c] = W[c].astype(int)
NEW = W[W["in_p5_workload"].str.upper() == "TRUE"]
notpres = NEW[NEW["newest_observation_preserved"].str.upper() == "FALSE"]


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# --------------------------------------------- work directory scaffold
for sub in ("checkpoints", "logs", "failures", "temp_outputs", "runtime_ledger"):
    (WORK / sub).mkdir(parents=True, exist_ok=True)
(WORK / "README.md").write_text(
    "# V6.24-P5 work directory\n\n"
    "Scratch space for the P5 backtest run. **Nothing here is a product artifact.**\n\n"
    "| Folder | Contents |\n|---|---|\n"
    "| `checkpoints/` | Per-batch partial results, resumable |\n"
    "| `logs/` | Runtime logs |\n"
    "| `failures/` | Failure ledger: series_id, model_name, error_type, message, timestamp |\n"
    "| `temp_outputs/` | Intermediate CSV before promotion |\n"
    "| `runtime_ledger/` | Per-batch timing and row counts |\n\n"
    "**Partial results must never be promoted to `processed/` and Shiny must never read this "
    "folder.** Promotion happens only after P5 validation passes.\n",
    encoding="utf-8")
print(f"work dirs created under {WORK.relative_to(V6)}")

# --------------------------------------------- dependency check
F = ["dependency", "required_by", "import_status", "version", "notes"]
deps = []
for mod, by in (("numpy", "all models"), ("pandas", "all models"),
                ("sklearn", "LinearRegression, FNAR-V2, SMLP-TCN, NLIN-DLIN_FIXED"),
                ("statsmodels", "ARIMA_Fixed, AutoARIMA, ETS Explicit, ETS_Current, Theta"),
                ("lightgbm", "LightGBM"), ("xgboost", "XGBoost"),
                ("pmdarima", "AutoARIMA (optional path)"), ("pyarrow", "Parquet IO")):
    try:
        m = importlib.import_module(mod)
        deps.append(dict(zip(F, [mod, by, "OK", getattr(m, "__version__", "unknown"), ""])))
    except Exception as e:
        deps.append(dict(zip(F, [mod, by, "MISSING", "-", f"{type(e).__name__}: {str(e)[:90]}"])))
for d in deps:
    print(f"  {d['dependency']:<14} {d['import_status']:<8} {d['version']}")
write("v6_24_p5a_dependency_check.csv", F, deps)
missing = [d["dependency"] for d in deps if d["import_status"] == "MISSING"]

# --------------------------------------------- risk register
F = ["risk_id", "severity", "area", "risk", "evidence", "impact", "mitigation",
     "blocks_p5", "owner_decision_required"]
write("v6_24_p5a_runtime_risk_register.csv", F, [dict(zip(F, r)) for r in [
    ("R01", "HIGH", "Backtest window / recency",
     "IOPS backtests never reach the recent data. All 20 IOPS series stop predicting around "
     "December 2022 while their actuals run to 2023-07-20.",
     f"{len(notpres)} of 90 series have newest_observation_preserved=FALSE: all 20 IOPS and 2 "
     f"CPU (CHN-Gallatin). IOPS carries 8-23 missing calendar days per series, so late origins "
     f"fail the contiguous-window test and only 5-6 of 11 sampled origins survive.",
     "Roughly seven months of the most recent IOPS history would never be backtested. That "
     "directly contradicts the owner rule that the newest observations must be preserved for "
     "validation.",
     "Adopt Decision D2 below: relax the test window from 'exactly 30 contiguous days' to 'at "
     "least N observations inside the 30-day window', and always force an origin at "
     "max_date - 30 so the newest data is always the last thing predicted.",
     "YES", "YES"),
    ("R02", "HIGH", "Reference implementation reuse",
     "The reference generator RAISES on a non-contiguous test window instead of skipping it.",
     "run_v6_17_viewer_backtests.py, training_and_test(): "
     "`if len(training) < LAGS+HORIZON+5 or len(test) != HORIZON_DAYS: raise ValueError`. "
     "HDD has 0 calendar gaps so this never fired. SSD has 2, CPU 1-7, IOPS 8-23.",
     "Reusing the reference code unmodified would crash on the very first gappy origin rather "
     "than degrade gracefully.",
     "P5 must wrap origin evaluation in the failure policy and pre-filter origins using the "
     "window contract produced here, instead of discovering invalid origins at fit time.",
     "YES", "NO"),
    ("R03", "MEDIUM", "Model naming",
     "The governed catalog spells the champion ETS_Explicit; the code and the HDD artifact both "
     "use 'ETS Explicit' with a space.",
     "Registry key is 'ETS Explicit'; the HDD parquet model_name column also uses the space.",
     "A naive lookup by the governed name would raise KeyError, and a naive union with the HDD "
     "artifact would create two distinct model identities for one model.",
     "Map explicitly in P5 and write the space form so P5 output unions cleanly with HDD. "
     "Recorded in the model catalog contract; never substitute silently.",
     "NO", "NO"),
    ("R04", "MEDIUM", "Neural model runtime",
     "The 3 neural models dominate runtime and are the least stable.",
     "FNAR-V2, NLIN-DLIN_FIXED and SMLP-TCN are MLP-based. The HDD reference isolated them in a "
     "separate phase with its own budget.",
     "A neural failure late in the run could consume the budget and leave the cheap models "
     "incomplete.",
     "Two-phase execution: run the 12 non-neural models first and checkpoint, then the 3 neural "
     "models. Mirrors the HDD reference structure.",
     "NO", "NO"),
    ("R05", "MEDIUM", "Series length asymmetry",
     "Valid origins per series vary from 5 to 10 across the cohort.",
     "SSD 10 of 11, CPU 8-10 of 11, IOPS 5-6 of 11.",
     "Accuracy is averaged over different numbers of origins per metric, so cross-metric "
     "comparisons are not like-for-like.",
     "Record valid_origin_count per series in the output and surface it wherever accuracy is "
     "reported in P6/P7.",
     "NO", "NO"),
    ("R06", "LOW", "Output volume",
     "Prediction row volume is modest and not a risk.",
     f"{int(NEW['target_date_count'].sum()):,} target dates x 15 models = "
     f"{int(NEW['target_date_count'].sum()) * 15:,} rows, roughly "
     f"{round(int(NEW['target_date_count'].sum()) * 15 * 250 / 1e6, 1)} MB uncompressed. The "
     f"HDD artifact alone is 2.4M rows at 13.6 MB compressed.",
     "None.", "No mitigation required.", "NO", "NO"),
    ("R07", "LOW", "Dependencies",
     "Model libraries must be importable.",
     f"Import check: {len(deps) - len(missing)} of {len(deps)} OK"
     + (f"; MISSING: {missing}" if missing else "; none missing."),
     "An abort at startup rather than mid-run.",
     "Startup capability check before any fitting, per the failure policy.",
     "YES" if missing else "NO", "NO"),
    ("R08", "MEDIUM", "Date alignment",
     "A one-day offset between predicted_value and actual_value would be invisible but would "
     "corrupt every accuracy number downstream.",
     "The HDD artifact stores target date in `date` while also carrying forecast_start_date and "
     "horizon_days, so an off-by-one is easy to introduce when renaming columns.",
     "Every accuracy metric and ranking in P6 would be wrong while looking plausible.",
     "Mandatory post-batch assertion: join predictions back to actuals_normalized on "
     "(series_id, target_date) and require an exact actual_value match, plus "
     "prediction_date == target_date and train_end_date < target_date on every row.",
     "NO", "NO"),
]])

# --------------------------------------------- owner decisions
F = ["decision_id", "decision", "options", "recommendation", "reason", "blocks_p5",
     "affects_series"]
write("v6_24_p5a_owner_decisions_before_p5.csv", F, [dict(zip(F, r)) for r in [
    ("D1", "Origin count per series.",
     "A) 11 sampled origins per series, matching the HDD reference. "
     "B) More origins for denser backtests. C) Fewer, for speed.",
     "A) 11 sampled origins.",
     "Matches the existing HDD artifact exactly, so P5 output unions with it without a "
     "methodology footnote. Volume is comfortable at roughly 360,000 prediction rows.",
     "NO", "all 90"),
    ("D2", "How to handle non-contiguous test windows caused by missing calendar days.",
     "A) Keep the strict rule that a test window must hold exactly 30 contiguous days. "
     "B) Require at least N observations within the 30-day window (suggest N=20) and always "
     "force an origin at max_date - 30. "
     "C) Resample every series to a daily grid.",
     "B) Relax to a minimum count and force a final origin at max_date - 30.",
     "Option A leaves all 20 IOPS series with no backtest after roughly December 2022, seven "
     "months short of their newest actuals, which contradicts the recency rule. Option C is "
     "forbidden outright: it would mean filling dates, which P4 explicitly did not do and P5 "
     "must not either. Option B preserves recency without inventing a single observation.",
     "YES", "22 of 90, mainly IOPS"),
    ("D3", "Champion model name spelling.",
     "A) Write 'ETS Explicit' with a space, matching the code and the HDD artifact. "
     "B) Rename to ETS_Explicit and migrate the HDD artifact.",
     "A) Keep the space form in P5 output.",
     "The HDD artifact is frozen and P4 must not be modified. Writing the space form lets the "
     "two union cleanly. A rename can happen later as a presentation-layer mapping.",
     "NO", "all 90"),
    ("D4", "Behavior if a model fails for some series.",
     "A) Mark the whole P5 run incomplete. B) Promote a partial artifact. "
     "C) Substitute a different model.",
     "A) Mark the run incomplete and escalate.",
     "C is prohibited by the governance rules. B would put a cohort with silent holes in front "
     "of Shiny, which is exactly the V6.23 failure mode. A keeps the failure visible.",
     "NO", "all 90"),
    ("D5", "Whether to re-run HDD for methodological consistency.",
     "A) Reuse the existing 750 HDD model-series from local artifacts. B) Regenerate HDD.",
     "A) Reuse. Do not re-run.",
     "Explicitly required by the P5A brief, and HDD backtests already exist and are validated. "
     "Regenerating would risk changing values P4 already froze and audited.",
     "NO", "50 HDD"),
]])

# --------------------------------------------- dry-run readiness
F = ["check", "expected", "observed", "result"]
dr = []


def add_dr(c, e, o, ok):
    dr.append(dict(zip(F, [c, e, o, "PASS" if ok else "FAIL"])))


add_dr("Processed actuals available", "actuals_normalized.parquet exists",
       f"exists={(PROC / 'actuals_normalized.parquet').exists()}",
       (PROC / "actuals_normalized.parquet").exists())
add_dr("Cohort manifest available", "cohort_manifest.parquet exists",
       f"exists={(PROC / 'cohort_manifest.parquet').exists()}",
       (PROC / "cohort_manifest.parquet").exists())
add_dr("Model registry imports", "15 models registered",
       f"{len(MODELS['all'])} registered: {len(MODELS['base'])} baseline + "
       f"{len(MODELS['chal'])} challenger + {len(MODELS['neural'])} neural",
       len(MODELS["all"]) == 15)
add_dr("Dependencies importable", "0 missing",
       f"{len(missing)} missing" + (f": {missing}" if missing else ""), not missing)
add_dr("Every P5 series has at least one valid origin", "0 series with zero origins",
       f"{int((NEW['valid_origin_count'] == 0).sum())} of 90 series with zero valid origins",
       int((NEW["valid_origin_count"] == 0).sum()) == 0)
add_dr("Work directory scaffold", "5 subfolders",
       f"{len([p for p in WORK.iterdir() if p.is_dir()])} subfolders created",
       len([p for p in WORK.iterdir() if p.is_dir()]) == 5)
add_dr("Newest observation preserved for every series",
       "90 of 90", f"{90 - len(notpres)} of 90; {len(notpres)} affected by calendar gaps",
       len(notpres) == 0)
write("v6_24_p5a_dry_run_readiness_check.csv", F, dr)
print(f"dry-run readiness: {sum(1 for x in dr if x['result'] == 'PASS')}/{len(dr)} PASS")

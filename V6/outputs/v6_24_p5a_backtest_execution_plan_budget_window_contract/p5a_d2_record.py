"""V6.24-P5A-D2 | Record the owner-approved window policy and update affected artifacts.

Amends, rather than rewrites, the P5A deliverables so the pre-approval state stays
visible in the audit trail.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
D2 = json.loads((OUT / "_p5a_d2.json").read_text(encoding="utf-8"))
W = pd.read_csv(OUT / "v6_24_p5a_backtest_window_contract_D2_APPROVED.csv", dtype=str)
for c in ("valid_origin_count", "target_date_count", "prev_strict_target_dates"):
    W[c] = W[c].astype(int)
NEW = W[W["in_p5_workload"].str.upper() == "TRUE"]

APPROVED = "2026-08-23"


def load(name):
    with (OUT / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ---------------------------------------- 1. the durable policy record
F = ["policy_id", "rule_id", "rule", "rationale", "enforcement_point", "violation_class"]
P = "V6_24_P5_WINDOW_POLICY_D2_OPTION_B"
write("v6_24_p5a_owner_approved_p5_window_policy.csv", F, [dict(zip(F, r)) for r in [
    (P, "W1", "Burn-in is taken from the OLDEST side of the series only.",
     "The newest observations are the most valuable validation evidence and must never be "
     "consumed as warm-up.",
     "Origin selection: first origin = min_date + 64 days.",
     "SERIES_TOO_SHORT_AFTER_BURN_IN"),
    (P, "W2", "The latest origin is FORCED at max_date - 30 whenever it qualifies.",
     "Guarantees the newest observations are the last thing predicted rather than the first "
     "thing lost. This is what lifted newest-preservation from 68 to 90 of 90 series.",
     "Origin selection: append max_date - 30 to the sampled origin list.",
     "DATE_ALIGNMENT_FAILURE"),
    (P, "W3", "A valid origin requires at least 20 REAL OBSERVED target dates inside the "
              "30-day horizon.",
     "Replaces the strict 'exactly 30 contiguous days' rule, which discarded late origins on "
     "gappy series and left all 20 IOPS series with no backtest after December 2022.",
     "Origin validity test, alongside the 65-row minimum training requirement.",
     "SERIES_TOO_SHORT_AFTER_BURN_IN"),
    (P, "W4", "Do NOT fill, resample, interpolate or invent dates.",
     "Sparse windows are handled by accepting fewer real targets, never by manufacturing "
     "observations. P4 refused to fill dates and P5 must not either.",
     "No resampling step exists anywhere in the P5 pipeline.",
     "VALUE_ERROR"),
    (P, "W5", "prediction_date MUST EQUAL target_date.",
     "Prevents a visual offset between the actual line and the model estimate.",
     "Row-level assertion before every checkpoint write.",
     "DATE_ALIGNMENT_FAILURE"),
    (P, "W6", "actual_value MUST come from actuals_normalized for that same "
              "(series_id, target_date).",
     "The actual is joined, never recomputed or carried from the model's own training frame.",
     "Post-batch join assertion against actuals_normalized with an exact-match requirement.",
     "DATE_ALIGNMENT_FAILURE"),
    (P, "W7", "train_end_date MUST be strictly less than target_date.",
     "Prevents leakage of future actuals into training.",
     "Row-level assertion before every checkpoint write.",
     "DATE_ALIGNMENT_FAILURE"),
    (P, "W8", "Minimum training rows per origin remains 65 (LAGS + HORIZON + 5).",
     "Unchanged from the HDD reference implementation, so P5 output stays comparable.",
     "Origin validity test.", "SERIES_TOO_SHORT_AFTER_BURN_IN"),
]])

# ---------------------------------------- 2. mark D2 approved
dec = load("v6_24_p5a_owner_decisions_before_p5.csv")
F = list(dec[0].keys()) + ["status", "approved_on", "approved_option", "effect"]
for r in dec:
    if r["decision_id"] == "D2":
        r.update({
            "status": "APPROVED", "approved_on": APPROVED, "approved_option": "B",
            "effect": f"Newest observation preserved rose from 68 to {D2['preserved']} of 90 "
                      f"series. IOPS valid origins rose from 5-6 to 10-11 and its target dates "
                      f"roughly doubled. Total targets {D2['prev_targets']:,} -> "
                      f"{D2['total_targets']:,}. Recorded as "
                      f"V6_24_P5_WINDOW_POLICY_D2_OPTION_B.",
        })
    else:
        r.update({"status": "RECOMMENDED_NOT_YET_FORMALLY_APPROVED", "approved_on": "PENDING",
                  "approved_option": "NOT_APPLICABLE",
                  "effect": "Recommendation stands; none of these block P5."})
    r["blocks_p5"] = "NO" if r["decision_id"] == "D2" else r["blocks_p5"]
write("v6_24_p5a_owner_decisions_before_p5.csv", F, dec)

# ---------------------------------------- 3. close R01, keep the history
risk = load("v6_24_p5a_runtime_risk_register.csv")
F = list(risk[0].keys()) + ["status", "resolution"]
for r in risk:
    if r["risk_id"] == "R01":
        r.update({
            "severity": "RESOLVED (was HIGH)", "blocks_p5": "NO",
            "owner_decision_required": "NO",
            "status": "CLOSED",
            "resolution": f"Owner approved D2 Option B on {APPROVED}. Recomputed contract: "
                          f"{D2['preserved']} of 90 series now reach their max actual date, up "
                          f"from 68. All 20 IOPS series recovered: last target moved from around "
                          f"2022-12-26 to 2023-07-20. No dates were filled or invented.",
        })
    elif r["risk_id"] == "R02":
        r.update({"status": "OPEN_ENGINEERING",
                  "resolution": "P5 must pre-filter origins using "
                                "v6_24_p5a_backtest_window_contract_D2_APPROVED.csv rather than "
                                "letting training_and_test() raise. No owner decision needed."})
    else:
        r.update({"status": "OPEN", "resolution": "Mitigation as stated; not blocking."})
write("v6_24_p5a_runtime_risk_register.csv", F, risk)

# ---------------------------------------- 4. refresh workload under D2
wl = load("v6_24_p5a_workload_estimate.csv")
F = list(wl[0].keys()) + ["window_policy", "targets_under_d2", "prediction_rows_under_d2",
                          "newest_preserved"]
for r in wl:
    m = r["metric"]
    if m in ("SSD", "CPU", "IOPS"):
        g = NEW[NEW["metric"] == m]
        t = int(g["target_date_count"].sum())
        r.update({"window_policy": P, "targets_under_d2": t,
                  "prediction_rows_under_d2": t * 15,
                  "newest_preserved": f"{int((g['newest_observation_preserved'].str.upper() == 'TRUE').sum())}/{len(g)}"})
    elif m == "TOTAL_NEW_P5":
        r.update({"window_policy": P, "targets_under_d2": D2["total_targets"],
                  "prediction_rows_under_d2": D2["total_targets"] * 15,
                  "newest_preserved": f"{D2['preserved']}/90"})
    else:
        r.update({"window_policy": "NOT_APPLICABLE", "targets_under_d2": "NOT_APPLICABLE",
                  "prediction_rows_under_d2": "NOT_APPLICABLE",
                  "newest_preserved": "NOT_APPLICABLE"})
write("v6_24_p5a_workload_estimate.csv", F, wl)

# ---------------------------------------- 5. refresh readiness
F = ["check", "expected", "observed", "result"]
dr = load("v6_24_p5a_dry_run_readiness_check.csv")
for r in dr:
    if r["check"].startswith("Newest observation preserved"):
        r["observed"] = (f"{D2['preserved']} of 90 under the approved D2 Option B policy "
                         f"(was 68 under strict contiguity)")
        r["result"] = "PASS" if D2["preserved"] == 90 else "FAIL"
dr.append(dict(zip(F, ["Owner-approved window policy recorded",
                       "policy artifact exists with all 8 rules",
                       f"v6_24_p5a_owner_approved_p5_window_policy.csv, 8 rules, id {P}",
                       "PASS"])))
write("v6_24_p5a_dry_run_readiness_check.csv", F, dr)
print(f"\nreadiness: {sum(1 for x in dr if x['result'] == 'PASS')}/{len(dr)} PASS")
print(f"D2 recorded as {P}")

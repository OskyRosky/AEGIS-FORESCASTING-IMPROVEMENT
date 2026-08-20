# V6.23-P1 — Viewer Data Availability Audit and Selector Correction

## Result

`V6_23_P1_VIEWER_DATA_AVAILABILITY_COMPLETED`

All ten acceptance criteria pass. The Viewer now offers **596 cases and every
one of them renders a real backtest**. No selection ends in "unavailable".

## The rule, now enforced by construction

> **Viewer** = only cases with observed actuals **and** the 15 governed model
> estimates.
> **Forecast** = every case with a forward forecast.

`viewer_visible` is now literally the same condition as `viewer_eligible`, so
the two cannot drift apart. This is not a convention that a future change could
quietly violate; it is the same boolean.

## What I got wrong in P0

P0 made SSD visible in the Viewer because hiding 298 local cases looked like
hiding scope. That reasoning was half right. The cases should be
**discoverable** — but not **selectable as backtest cases**, because selecting
one produced exactly the dead end you saw.

The right distinction is not visible versus hidden. It is *selectable as a
backtest* versus *listed as forecast-only*.

## Audit: what every case actually has

| Route group | Cases | Observed actuals | 15-model backtest | Forecast | Class |
|---|---:|---|---|---|---|
| HDD Basilisk | 202 | 202 / 202 | 202 / 202 | 202 / 202 | **VIEWER_COMPLETE** |
| HDD EDB Consumer | 197 | 197 / 197 | 197 / 197 | 197 / 197 | **VIEWER_COMPLETE** |
| HDD EDB Enterprise | 197 | 197 / 197 | 197 / 197 | 197 / 197 | **VIEWER_COMPLETE** |
| SSD Phoenix No Efficiency | 147 | **0 / 147** | **0 / 147** | 147 / 147 | FORECAST_ONLY |
| SSD Phoenix With Efficiency | 151 | **0 / 151** | **0 / 151** | 151 / 151 | FORECAST_ONLY |

Classification totals: **596 VIEWER_COMPLETE**, **298 FORECAST_ONLY**,
**0 DATA_GAP_CAN_BUILD**, 2 quarantined (`PROD`).

That third number is the important one: **nothing that is missing can be built
from local artifacts.** There is no consolidation shortcut.

## Does SSD Viewer data exist anywhere locally? No.

I searched every local artifact rather than assuming:

| Artifact | SSD rows found | SSD actual values found |
|---|---:|---:|
| `forecast_viewer_model_outputs_v2_full.parquet` | **0** | 0 |
| `forecast_forward_outputs_v6_17_full.parquet` | 219,600 | **0** — every row is a forecast record |
| `v6_21b_accuracy_metrics.parquet` | 0 | 0 |
| `data/processed/forecast_viewer_model_outputs.csv` (legacy) | 0 | 0 — single-route HDD, 39 series |

**Conclusion:** SSD Phoenix has no observed history and no backtest anywhere on
this machine. The Forecast page works for it because the forward artifact
carries prepared forecast values only.

## What it would take to make SSD Viewer-complete

Two steps, in order, and neither is a repackaging job:

1. **Governed SQL extraction** of SSD-Phoenix observed actual history.
   This is the blocker. The data does not exist locally in any form.
2. **A 15-model backtest run** over that history, producing rows in the same
   shape as the HDD cases: `actual_value`, `forecast_value`, `model_name`,
   `horizon_days`, rolling origins.

Cost signal from the comparable HDD work: V6.17 produced 596 cases with 15
models in roughly 75 minutes of model execution. SSD's 298 cases would be
broadly half that, **after** the extraction exists.

Neither step is authorised by this stage, and neither was performed.

## Verification, route by route

Every one of the six Viewer routes was swept end to end:

| Route | Entities | Backtest available | Analyze enabled | Models |
|---|---:|---|---|---:|
| EDB Consumer Region | 45 | Yes | Yes | 15 |
| EDB Consumer Forest | 152 | Yes | Yes | 15 |
| EDB Enterprise Region | 45 | Yes | Yes | 15 |
| EDB Enterprise Forest | 152 | Yes | Yes | 15 |
| Basilisk Region | 47 | Yes | Yes | 15 |
| Basilisk Forest | 155 | Yes | Yes | 15 |
| **Total** | **596** | **0 unavailable** | **0 disabled** | |

45+152+45+152+47+155 = 596, matching the header exactly.

Forecast re-verified: HDD and SSD both selectable, SSD renders 30 forward points
with the `Forecast start` boundary at 2026-08-12, `PROD` absent, 147 entities on
the No Efficiency variant.

## Selector behaviour now

| Page | Normal selectable | Forecast-only | Disabled / unavailable |
|---|---:|---:|---:|
| Viewer | **596**, all complete | 298, shown as a callout, not selectable | **0** |
| Forecast | **894** | n/a | CPU, IOPS, Memory as explicit backend gaps |

## One change beyond the Viewer

`PROD` is now excluded from the **Forecast** selector too. In P0 I removed it
from the Viewer only and flagged the Forecast exposure as an open finding. This
stage's acceptance criteria require it excluded, so it now is: Forecast went
from 896 to 894 visible cases. `forecast_eligible` is untouched at 896, so the
underlying data statement is unchanged.

## Governance

No SQL. No model run. No recomputation. No fabricated actuals or estimates.
Productive Parquet unchanged. V6.22 manifest untouched. V1 through V5 untouched.
Nothing pushed.

## Next step

The Viewer is now honest and usable. Two decisions remain, both yours:

1. **Should SSD become Viewer-complete?** If yes, it needs a governed SQL
   extraction plus a 15-model backtest run — a real generation stage, not a fix.
2. **`FORECAST_MODEL_VOCABULARY_UNGOVERNED`** still blocks V6.23 generation:
   the forward artifact uses 30 model names disjoint from the governed 15.

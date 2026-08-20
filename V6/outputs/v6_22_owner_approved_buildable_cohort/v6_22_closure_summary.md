# V6.22 Owner-Approved Buildable Cohort — Closure Summary

> **This is not the E11 cohort.** E11 remains missing.
> `V6_19_COHORT_SOURCE_OF_TRUTH_GATE_BLOCKED_E11_SOURCE_MISSING` stands
> unmodified. Nothing here is recovered, reconstructed or equivalent to the
> 130-case E11 cohort.

## Recommended thresholds — read this first

| Parameter | Recommended value |
|---|---|
| `history_depth` | **60** distinct dates carrying a non-null actual |
| `staleness_days` | **no limit** |
| `threshold_recommendation_status` | **OWNER_CONFIRM** |
| Routes eliminated by this recommendation | **none** |

To change them, re-run with two arguments; nothing else needs redoing:

```
python V6/outputs/v6_22_owner_approved_buildable_cohort/build_v6_22_cohort_manifest.py 90 30
```

(first argument `history_depth`, second `staleness_days` or the literal `none`)

### Why 60, and what other values would cost

The measured distribution, not a value copied from E11:

| Route | Cases | history_depth | staleness (days) |
|---|---:|---|---|
| HDD Basilisk Forest | 155 | 79 | 55 |
| HDD Basilisk Region | 47 | 75–79 | 55–57 |
| HDD EDB Consumer Forest | 152 | 211–277 | 0 |
| HDD EDB Consumer Region | 45 | 193–276 | 1–84 |
| HDD EDB Enterprise Forest | 152 | 211–277 | 0 |
| HDD EDB Enterprise Region | 45 | 210–360 | 1–83 |

60 is the highest value in the grid that eliminates no route while still acting
as a real guard on future thin series.

**The E11 gate would have been actively harmful here.** Its `>=150` threshold
eliminates **both HDD Basilisk routes entirely** — 202 cases, the very routes
owner decision D3 instructs to include. The same happens at 90. Likewise, any
staleness limit of 60 days or tighter removes Basilisk, whose actuals stop
55–57 days before the artifact anchor date of **2026-07-19**.

Both Basilisk routes stay **forecast-buildable regardless of any threshold**,
because thresholds gate only the viewer/accuracy side.

## A. How many — every unit, labelled

| Unit | Count |
|---|---:|
| Buildable **route × key cases** | **894** |
| Buildable **distinct entity tokens** (case-sensitive) | **396** |
| Buildable **distinct physical entities** (case-insensitive) | **205** |
| **Viewer**-buildable cases | 596 |
| **Accuracy**-buildable cases | 596 |
| Total forecast cases **before** quarantine | 896 |
| Forecast-**only** candidates | 300 |
| Forecast-only **quarantined** | 2 |
| Forecast-only **buildable** | 298 |
| Total **forecast-buildable after quarantine** | 894 |

Never write "894 entities" or "596 keys". The three units are different
numbers measuring different things, and conflating them is the defect this
sequence has been correcting.

## B. Exactly which — per-route breakdown

| route_id | Cases | Entity tokens | build_viewer | build_forecast | Alignment | Exception |
|---|---:|---:|---:|---:|---|---|
| `HDD\|Organic\|Basilisk\|Forest` | 155 | 155 | 155 | 155 | OPERATIONAL_SOURCE_PRECEDENCE | Basilisk |
| `HDD\|Organic\|Basilisk\|Region` | 47 | 47 | 47 | 47 | OPERATIONAL_SOURCE_PRECEDENCE | Basilisk |
| `HDD\|Organic\|EDB\|Consumer\|Forest` | 152 | 152 | 152 | 152 | OPERATIONAL | — |
| `HDD\|Organic\|EDB\|Consumer\|Region` | 45 | 45 | 45 | 45 | OPERATIONAL | — |
| `HDD\|Organic\|EDB\|Enterprise\|Forest` | 152 | 152 | 152 | 152 | OPERATIONAL | — |
| `HDD\|Organic\|EDB\|Enterprise\|Region` | 45 | 45 | 45 | 45 | OPERATIONAL | — |
| `SSD\|Phoenix\|LEGACY_VARIANT\|Low Volume No Efficiency\|Forest` | 147 | 147 | 0 | 147 | LEGACY_VARIANT | — |
| `SSD\|Phoenix\|LEGACY_VARIANT\|Low Volume With Efficiency\|Forest` | 151 | 151 | 0 | 151 | LEGACY_VARIANT | — |
| **Total** | **894** | | **596** | **894** | | |

The SSD Phoenix zeros are **data, not exclusion**: those cases carry no actuals,
so there is nothing to backtest. They are fully forecast-buildable.

The full list is in `v6_22_final_selection_list.csv` (894 rows, sorted by route
then entity). A 10-row sample of `selection_display_path` appears in the final
response.

## Governed exceptions

| Exception | Cases | What it means | What it does **not** mean |
|---|---:|---|---|
| Basilisk `CATALOG_SERVING_EMPTY_BUT_OPERATIONAL_ARTIFACT_AVAILABLE` | 202 | A working artifact exists locally, so source precedence applies | The catalog was not corrected or reconciled; not marked UI_ONLY |
| SSD Phoenix `LEGACY_VARIANT` | 298 | Inherited variant names preserved verbatim | No Organic/Inorganic alignment is claimed |
| `PROD` quarantine | 2 | Excluded; not a forest identifier | Not asserted invalid forever, only unsupported |

## The four unresolved records

| record_id | Status | Decision due |
|---|---|---|
| **FORECAST_MODEL_VOCABULARY_UNGOVERNED** | UNRESOLVED | **BEFORE_V6_23_GENERATION** |
| SSD_PHOENIX_152_144_MISMATCH | UNRESOLVED | DEFERRED_PENDING_SQL_OR_OWNER |
| ENTITY_CASING_INCONSISTENT_ACROSS_ROUTES | UNRESOLVED | BEFORE_ANY_CROSS_ROUTE_ENTITY_ROLLUP |
| HDD_BASILISK_CATALOG_SERVING_EMPTY_BUT_OPERATIONAL_ARTIFACT_AVAILABLE | UNRESOLVED | DEFERRED_PENDING_SQL_OR_OWNER |

### The one that must be decided before V6.23

The Viewer backtest artifact uses **15** model names, all governed. The forward
forecast artifact uses **30** — and the intersection is **exactly zero**.

> Note: the stage brief cited 29 forward model names. The measured value is
> **30**. The discrepancy is reported rather than forced to match.

`ARIMA` and `Arima` are the same model under two casings. Nothing was renamed
or merged. The consequence is blunt: **the "15 governed models" invariant does
not hold on the Forecast page**, and generating 894 cases on that vocabulary
would industrialise an ungoverned model set. Three options are recorded in
`v6_22_unresolved_records.csv`; none was chosen here.

## Entity casing

396 distinct entity tokens resolve to 205 distinct physical entities. **191 of
the 205 exist under more than one casing** — the Basilisk routes use lower case
while the EDB and SSD Phoenix routes use upper case.

Worked example: `NAMPRD07` appears in 4 routes, `namprd07` in 1. They are the
same physical forest.

No data or join column was case-folded. `entity_token_upper` exists for
**counting only**. Normalising the join columns would break every join to the
V6.17 artifacts, which is exactly the discovery rule.

## What CPU and IOPS would need

Both are **declared, never fabricated**: zero rows exist for them in the cohort
manifest. They need an authorised read-only SQL extraction to produce a governed
local artifact. Memory has no routable source at all and is out of scope.

## Exact next step

1. **Decide `FORECAST_MODEL_VOCABULARY_UNGOVERNED`.** This is the only record
   that blocks V6.23 generation.
2. Confirm or change `history_depth = 60` and `staleness = no limit`. The
   recommendation eliminates no route, so this is a confirmation, not a trade-off.
3. Review `v6_22_final_selection_list.csv` and authorise V6.23.

V6.23 must not start before step 1.

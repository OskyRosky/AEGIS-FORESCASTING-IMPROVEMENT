# AEGIS - Full Pre-Delivery Status

Date: 2026-08-18 · Owner review and manager presentation document

---

## 1. Executive summary

**Discovery is complete. Product delivery starts now.**

Across stages E0 to E11 we reconstructed, from physical evidence and with no assumptions, the
real SubstrateBE forecast taxonomy in `TesseractEarthDW`. The result is not a list of metrics: it
is a conditional navigation tree containing **6,383 logical leaf cases**, backed by
**38 route contracts** and **20 forecast source objects** identified one by one.

The current dashboard exposes **9 top-level labels**. The issue is not that it covers "little":
it uses a different structure. Today's labels flatten navigable axes into the label text
(`CPU Failover` mixes metric and scenario; `SSD MCDB` mixes metric and DB Type).

Rather than jumping from 9 destinations to 6,383 at once, we froze an **initial cohort of
130 cases** across **29 route artifacts**, covering CPU, HDD, IOPS and SSD (SSD Phoenix
included), with demonstrable conditional navigation. It is small, defensible and expandable
without redesign.

---

## 2. What AEGIS solves

The work started from a concrete problem: a forecast-drift analysis that did not cover every
possible case. Only a handful of scenarios had been specified, while the platform actually serves
many more, with different rules per metric.

AEGIS answers three questions that previously had no single answer:

1. **Which combinations actually exist** (not which are conceivable).
2. **Where each forecast comes from** and which columns read it correctly.
3. **Which ones have enough real history** to model or to measure accuracy.

---

## 3. Project evolution

| Stage | Scope | Closure |
|---|---|---|
| E0 / E0.1 | Structural inventory and candidate boundary | closed |
| E1 | Base metric universe | `RM-E1-CLOSED` |
| E2 | Canonical DB Types | `RM-E2-CLOSED` |
| E3 | Metric x DB Type matrix | `RM-E3-CLOSED` |
| E4 | Canonical granularities | `RM-E4-CLOSED` |
| E5 | Metric x DB Type x Granularity | `RM-E5-CLOSED` |
| E6 | Scenario, Segment, Organic/Inorganic | `RM-E6-CLOSED` |
| E7 | Region universe | `RM-E7-CLOSED` |
| E8 | Branch x Region | `RM-E8-CLOSED` |
| E9 | Key semantics | `RM-E9-CLOSED` |
| PRE-E10 | Forest / Forest_SKU / SKU pair completion | complete |
| E10 | Canonical serving source contract | `RM-E10-CLOSED` |
| E11 | Eligibility profiling against actuals | profiling complete |
| **This phase** | **Initial cohort + report + prototype** | **in review** |

---

## 4. E0-E11 discovery status

Every stage closed with a capped SQL budget, durable CSV evidence and no silent normalisation of
physical values. No conclusion rested on an object name: we proved repeatedly that names
contradict content in this database.

---

## 5. What was discovered

- **5 base metrics**: CPU, HDD, IOPS, SSD, Memory.
- **5 DB Types**: Phoenix, NonPhoenix, EDB, Basilisk, MCDB, with different applicability per metric.
- **3 granularities**: Region, Forest, Forest_SKU.
- **35 canonical regions** (33 routable), **11 environments**.
- **173 reference Forests**, 164 observed in serving, **4 outside the reference universe**.
- **9 observed SKU values** and **714 unique Forest x SKU combinations**.
- **There is no generic "Key" axis**: every `Key`/`MyKey` column holds an already-modelled
  dimension.

---

## 6. Current taxonomy magnitude

| Concept | Value |
|---|---:|
| Current dashboard labels | 9 |
| Route contracts | 38 |
| Routable routes | 34 |
| Selected forecast source objects | 20 |
| **Logical leaf cases** | **6,383** |
| With a resolved actuals source | 5,887 |
| With observed data | 5,438 |
| Resolved but empty (`NO_DATA`) | 449 |
| Actuals source unresolved | 496 |
| >=150 periods and provisionally recent | 4,680 |

> **Important distinction:** `NO_DATA` (449) and `ACTUALS_SOURCE_UNRESOLVED`
> (496) **must not be added together** as "no data". The first means the series is
> empty; the second means we do not yet know where to read it from.

---

## 7. Metric summary

| Metric | Logical leaves | With data | In the initial cohort |
|---|---:|---:|---:|
| CPU | 2,333 | 2,035 | 48 |
| HDD | 1,259 | 1,057 | 32 |
| IOPS | 1,196 | 1,176 | 20 |
| SSD | 1,594 | 1,170 | 30 |
| Memory | 1 | 0 | 0 |

Memory stays in the catalog but is **not analytically routable**: it has no granularity column and
its demand views are `WHERE 1=0` markers.

---

## 8. Conditional UI/UX behaviour

This is the main functional difference from the current dashboard: **each metric has a different
filter sequence**.

| Metric | Sequence | Filters that never appear |
|---|---|---|
| CPU | Metric > DB Type > Scenario > Granularity > entity | Organic/Inorganic, Segment |
| IOPS | Metric > Scenario > Granularity > entity | **DB Type**, Organic/Inorganic, Segment |
| HDD organic | Metric > Organic > DB Type > Segment > Granularity > entity | Scenario |
| HDD inorganic | Metric > Inorganic > Granularity > entity | **DB Type and Segment** |
| SSD Phoenix organic | Metric > DB Type > Organic > Granularity > entity | Scenario, Segment |
| SSD Phoenix inorganic | Metric > DB Type > Inorganic > Forest | Scenario, Segment and **Region** |
| Memory | no analytical route | all of them |

Additional rules verified in the prototype:

- The entity selector is labelled **Region**, **Forest** or **Forest + SKU** according to grain.
  A generic dropdown called "Key" is never shown.
- Changing an upstream filter **clears** every downstream one. A selected SKU does not survive a
  DB Type change.

---

## 9. Forecast source architecture (E10)

The 20 serving objects belong to **three schema families**, and the contract changes with the
family:

| Family | Value | Target period | Forecast cycle | Objects |
|---|---|---|---|---|
| A | `Value` | `Datetime` / `DateTime` | `ForecastVersion` | 14 |
| B | `Value` | `DataDate` | `ForecastRunId` | 5 |
| C | `forecast_mean` | `target_date` | `write_time` | 1 |

---

## 10. Actuals and history findings (E11)

- **Actuals source**: `SubstrateBE_M2CP_Demand_History` (1.18M rows). It is **not** one of the 20
  forecast sources: the contracts are independent.
- **Measured cadence: DAILY**, with 2,600 periods between 2019-07-01 and 2026-08-16.
- **The history threshold barely discriminates**: between 30 and 150 observations only 26 leaves
  are lost out of 5,432. The real constraint is **freshness**, not depth.
- **The reduction concentrates in Forest_SKU** and it is caused by freshness: 2,964 of 3,587 reach
  >=90 observations, but only 2,322 are current. These are retired hardware combinations.

---

## 11. Important technical discoveries

**1. `ForecastRunId` is not always a forecast cycle.**
In `SubstrateBE_DemandForecast_CPU_Forest` and `..._IOPS_Forest` we proved that
`COUNT(*) = COUNT(DISTINCT ForecastRunId)`: it is a **per-row identifier**. Those four routes
**cannot support drift** from their current object. In the other three objects of the same family
it is a genuine run (560, 50 and 14 values).

**2. The actuals source is different from the forecast source.** Assuming otherwise would have
produced an accuracy calculation comparing the forecast against itself.

**3. The SKU crosswalk already existed in the data.** The actuals source `SKU` column uses
`Gen8_AMD`; the `Full_SKU` column of the same table uses `WCS Gen8`, which is the taxonomy
vocabulary. It is a many-to-one relation, so counting was grouped at the source. Without that
check, 3,587 leaves would have been declared unprofilable.

**4. Memory is not routable**, confirmed independently in E10 and E11.

**5. CPU Phoenix / NonPhoenix: `DERIVABLE_ACTUALS_SPLIT_CONFIRMED`.**
Physically distinct columns exist (`GCycles_consumed_SSD` with 851 observations against
`GCycles_consumed_HDD` with 563), so the series **are** separable. But the SSD→Phoenix and
HDD→NonPhoenix correspondence is a **derivation** from the storage tier, not a physical label.
These routes are therefore marked `UI_DEMO_READY` but **not** `ANALYTICS_DELIVERY_READY` for
accuracy. The split was not fabricated.

**6. Freshness: `SSD|Legacy` is discontinued, not slow-cadence.**
It publishes daily (implied cadence 1.06 days) but stopped on **2026-07-01**, 48 days ago. This
matches E10, where its forecast source had its latest vintage in 2023-11-01. It is excluded from
the initial cohort. Every other route is active with a 2-3 day lag.

---

## 12. Current dashboard vs discovered system

| | |
|---|---|
| **Current view** | 9 top-level labels |
| **Discovered system** | 38 route contracts · 34 routable · 6,383 logical leaf cases |
| **Initial delivery** | **130 cases** across **29 route artifacts** |

Capabilities missing today: conditional navigation, granularity switching, logical entity
selection (Region/Forest/SKU), exclusion rules and source traceability.

Full detail: `evidence/E11/E11_current_dashboard_vs_discovered_scope.md`.

---

## 13. Initial delivery cohort

**`INITIAL_DELIVERY_CASE_COUNT` = 130**
**`INITIAL_ROUTE_ARTIFACT_COUNT` = 29**

Gate applied (for this delivery only, not a final policy):

- route routable in E10 and **active** per the per-route freshness check;
- actuals source resolved and carrying data;
- **>= 150 distinct observed periods**;
- leaf fresh relative to its freshness anchor.

| Metric | Cases |
|---|---:|
| CPU | 48 |
| HDD | 32 |
| IOPS | 20 |
| SSD | 30 |
| **Total** | **130** |

| Granularity | Cases |
|---|---:|
| Region | 62 |
| Forest | 44 |
| Forest_SKU | 24 |

Of the 130 cases, **98** are `ANALYTICS_DELIVERY_READY`; the remaining 32 are the CPU
Phoenix/NonPhoenix routes, valid for navigation but with accuracy pending confirmation of the
actuals mapping.

SSD Phoenix is included as required. NAMPRD07 appears in the cohort wherever it passes the gate.

---

## 14. What is deliberately NOT in the first delivery

- **Memory**: no analytical route.
- **Basilisk** (CPU and HDD): `LABEL_ONLY` and `SERVING_EMPTY` respectively.
- **Inorganic branches** (HDD and SSD Phoenix): navigable in the UI, but with no resolved actuals
  source. They are shown as `UI_ONLY`.
- **SSD Legacy**: discontinued on 2026-07-01.
- **Real accuracy and drift**: E10 and E11 prepared the contracts; the computation has not been
  done.

---

## 15. Scale-up strategy

```
Full taxonomy (6,383)
      |
Eligibility profile (E11)
      |
Cohort manifest        <- expands by adding rows
      |
Route artifacts (29)
      |
Dynamic UI manifest    <- drives navigation from data
      |
Dashboard
```

Expanding the cohort means **adding manifest rows**, not rewriting UI logic. The prototype already
reads its behaviour from the manifest, not from per-metric hardcoded rules.

---

## 16. Risks and open items

| Item | Impact | Status |
|---|---|---|
| CPU Phoenix/NonPhoenix actuals mapping | 4 routes without confirmed accuracy | derived, not labelled |
| 4 routes with no vintage dimension | CPU Total and IOPS cannot support drift | documented in E10 |
| Inorganic branches without actuals | 335 leaves outside analytics | documented |
| 4 Forests outside the reference universe | minor | documented, not added |
| 159 Forest_SKU tokens with no SKU component | not matchable in actuals | preserved |
| Final history threshold | pending decision | **owner** |
| Final recency policy | pending decision | **owner** |

---

## 17. Immediate next steps

1. Review and approve the 130-case cohort.
2. Materialise the 29 route artifacts as real queries.
3. Wire the dynamic UI manifest into AEGIS/Grafana.
4. Decide the history threshold and the recency policy.
5. Resolve the CPU Phoenix/NonPhoenix actuals mapping.
6. Compute real accuracy over the cohort.

---

## 18. Status table

| Item | Status |
|---|---|
| Taxonomy discovery E1-E9 | **COMPLETE** |
| Forecast source contracts E10 | **COMPLETE** |
| Eligibility profiling E11 | **COMPLETE** |
| Reconciliation with the current dashboard | **COMPLETE** |
| Initial delivery cohort | **COMPLETE - frozen at 130** |
| Dynamic UI manifest | **COMPLETE** |
| HTML prototype | **COMPLETE** |
| Real route artifacts | **NEXT** |
| Grafana wiring | **NEXT** |
| Production accuracy / drift | **NEXT** |
| Final history threshold | **DEFERRED - owner decision** |
| Final recency policy | **DEFERRED - owner decision** |
| Memory analytics | **DEFERRED - no route** |
| Basilisk analytics | **DEFERRED - no serving** |

---

## Presentation block

> **CURRENT DASHBOARD**
> 9 top-level labels.
>
> **DISCOVERED SYSTEM**
> 38 route contracts · 34 routable routes · 6,383 logical leaf cases.
>
> **INITIAL OPERATIONAL DELIVERY**
> 130 selected cases across 29 route artifacts.
> CPU + HDD + IOPS + SSD, including SSD Phoenix.
> Dynamic conditional navigation, verified journey by journey.
>
> **SCALE-UP**
> Expand from the curated cohort using the same manifests and route contracts,
> with no UI redesign.

Navigable prototype: `AEGIS_Dynamic_Taxonomy_Dashboard_Mockup.html`
(series values are **simulated**; taxonomy identifiers are **real**).

# V6.24-P2 — Selection Methodology

**Purpose:** document the selection of the 140-series MVP cohort so it is fully reproducible.
Re-running `p2_select_cohort.py` on the same inputs produces byte-identical output.

---

## 1. Principles

| Principle | Implementation |
|---|---|
| **Never "first N"** | No selection step takes the head of a list. |
| **Deterministic** | Every sort has an explicit tie-breaker; no step depends on input file order. |
| **Representative** | Two strategies: even *stride sampling* across the observation-count range, and *round-robin* across geographic prefixes. |
| **Auditable** | Each selected row records its own `selection_reason`. |

Two reusable primitives are used.

**`spread(items, n, sort_key)`** — sorts stably, then samples at stride `len/n`.
Guarantees coverage of the whole sort-key range instead of clustering at one extreme.
Used for HDD, where observation counts vary widely within a route (211–277, 193–360).

**`round_robin_by_prefix(items, n, prefix_of, rank_key)`** — groups by prefix, sorts each
group, then takes one per group in rotation. Guarantees no prefix dominates while others go
unrepresented. Used for SSD (forest prefix) and CPU/IOPS (region prefix).

---

## 2. HDD — 50 of 596, already local

**Source:** `v6_24_p0_product_complete_candidates.csv`. All 596 rows are product-complete:
actuals, all 15 governed models, and forecast.

**Allocation.** Equal base across all six routes (`50 // 6 = 8`), remainder of 2 to the two
largest pools, ties broken by route name ascending.

| Route | Pool | Allocated | Observation range |
|---|---:|---:|---|
| `HDD\|Organic\|Basilisk\|Forest` | 155 | **9** | 79–79 |
| `HDD\|Organic\|Basilisk\|Region` | 47 | **8** | 75–79 |
| `HDD\|Organic\|EDB\|Consumer\|Forest` | 152 | **9** | 211–277 |
| `HDD\|Organic\|EDB\|Consumer\|Region` | 45 | **8** | 193–276 |
| `HDD\|Organic\|EDB\|Enterprise\|Forest` | 152 | **8** | 211–277 |
| `HDD\|Organic\|EDB\|Enterprise\|Region` | 45 | **8** | 210–360 |

All six route families are represented, and Forest (26) versus Region (24) is near-balanced.

**Within each route:** `spread` on `(actual_observation_count, key_entity)`.

---

## 3. SSD — 50 of 136, to extract in P3

**Source:** `forecast_substrateBE_ssd_phx_lvwe_metrics`, confirmed in P1B.
Eligible pool: 136 of 137 forest keys clearing 50 observations.

**Step 1 — force-include dashboard reference keys.**
`NAMPRD07` and `NAMPRD08` are included unconditionally. Both clear the threshold and both were
reconciled against the owner's AX4 Security dashboard in P1B, so the demo can be validated
directly against a known-good reference.

**Step 2 — geographic round-robin for the remaining 48.**
Group by the first three characters of the forest key, sort each group by
`(-observation_count, key)`, then rotate.

Result: **32 distinct geographic prefixes** across 50 keys —
`APC, ARE, AUS, AUT, BRA, CAN, CHE, CHL, DEU, DNK, ESP, EUR, FRA, GBR, IDN, IND, ISR, ITA,
JPN, KOR, LAM, MEX, MYS, NAM, NOR, NZL, POL, QAT, SGP, SWE, TWN, ZAF`.

**Critical rule — no double counting.** LVWE and LVNE hold an *identical* `Mean_Actual`
(P1B012 returned 0 differing rows) and differ only in `Mean_Forecast` (P1B013: 6,720 differing
rows). Each forest key therefore appears **exactly once** as an observed series, with
`variant = LVWE+LVNE`.

**Storage decision — long format.** P3 writes two raw files, one per variant, each tagged with
`forecast_variant`. In `processed/`:

- `actuals_normalized.parquet` loads `Mean_Actual` from **LVWE only** — 50 series.
- `forecast_outputs.parquet` loads **both** variants as two forecast baselines.

The LVNE actual column is emitted in P3 as `actual_value_DO_NOT_LOAD_AS_ACTUALS` so the
constraint is enforced by the column name itself, not by documentation alone.

---

## 4. CPU — 20 of 60, to extract in P3

**Source:** `forecast_substrateBE_cpu_actual_region` where `ModelVersion = 'Actual'`.

**Scenario balance:** exactly 10 `Consumed` + 10 `Failover`.

**Within each scenario:** round-robin on the region prefix of the composite key
(`CHN-Gallatin` → `CHN`), ranked by `(-observation_count, key)`.

**DB Type.** The table carries no DB Type column, so every CPU row records
`UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE`. It is not invented and not left blank.

**Caveat:** `STALE_ACTUALS_SOURCE`, latest observation `2023-07-20`.

---

## 5. IOPS — 20 of 58, to extract in P3

Identical method to CPU: 10 `Consumed` + 10 `Failover`, region-prefix round-robin.

**DB Type** is `NOT_APPLICABLE` — IOPS has no DB Type axis by design.

**Caveat:** `STALE_ACTUALS_SOURCE`, latest observation `2023-07-20`.

---

## 6. Memory — 0 series

`BLOCKED_NO_USEFUL_ACTUALS_SOURCE`. The governed `vw_SubstrateBE_Demand_Memory_*` views exist
with the correct contract but return 0 rows. The only populated object is 54.6M rows of
ungoverned raw telemetry with no key/value/scenario contract. Awareness and gap only.

---

## 7. What the cohort does NOT yet have

**Only HDD has 15 governed model backtests today.**

| Metric | Actuals | 15 governed backtests | Forecast |
|---|---|---|---|
| HDD | Local | **Present** | Present |
| SSD | P3 | **Absent — P5** | 2 external baselines (LVWE/LVNE) |
| CPU | P3 | **Absent — P5** | **None in source** |
| IOPS | P3 | **Absent — P5** | **None in source** |

The cohort becomes Viewer-complete **only after P5 and P6**. Until then, 90 of the 140 series
would fail the "actuals + 15 models" Viewer rule. The completeness gate in P7 is what enforces
this — no series may reach the Viewer selector before it passes.

---

## 8. Reproducibility

| Input | Provenance |
|---|---|
| HDD pool | `v6_24_p0_product_complete_candidates.csv`, 596 rows |
| SSD pool | `P2Q004` — per-key counts, dates, non-numeric detection |
| CPU pool | `P2Q005` — 60 scenario × key rows |
| IOPS pool | `P2Q006` — 58 scenario × key rows |

Deterministic because: sorts are stable with explicit tie-breakers; allocation uses integer
division with a documented remainder rule; stride sampling uses integer arithmetic only; and
round-robin iterates prefixes in sorted order. No randomness, no timestamps, no hashing.

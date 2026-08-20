# Multi-Metric / Multi-Scenario Expansion — Handoff Guide

**Purpose:** enable the AEGIS *Forecast Generation Code Improvement* project to expand from HDD-only to **all Metrics and Scenarios**, reusing evidence already produced and verified in the sibling project **AEGIS Forecast Drift (Feature 6986096)**.

**Audience:** the AI agent working in the Code Improvement repository.

**Status of the evidence cited here:** produced across stages V4.1 – V4.8 of the Drift project, each closed with a validator at exit 0. Current regression: **997 checks passing across 12 validators**.

---

## PART 0 — Read this first: what is already known and must not be re-derived

The Drift project spent five stages establishing the scenario/metric landscape. **Do not re-discover it. Consume it.**

### 0.1 Where the source-of-truth documents live

Sibling repository root (note the **U+2011 non-breaking hyphen** in "Cross‑Functional" — ordinary search tools will not match it; use absolute paths):

```
...\Microsoft - Projects\2026\Integrate Cross‑Functional Capacity Feedback Signals
    to Align and Improve Capacity Mitigation Actions (Feature 6986096)\
```

| Question you need answered | Document |
| --- | --- |
| **What source tables exist at all?** | `engineering\E1_source_discovery_profiling\E1A_source_profiling.md` |
| **What was verified live in the source?** | `engineering\E1_source_discovery_profiling\E1B_live_data_validation.md` |
| **Column-level dictionary** | `engineering\E1_source_discovery_profiling\E1A_data_dictionary.csv` |
| **Which scenarios exist, mapped to tables** | `engineering\E8_cloud\V4_1_multi_scenario_discovery\scenario_source_inventory.csv` |
| **AX4S scenario → table lineage** | `...\V4_1_multi_scenario_discovery\ax4s_accuracy_lineage.md` |
| **What is hardcoded to one scenario today** | `...\V4_1_multi_scenario_discovery\multi_scenario_hardcode_inventory.csv` |
| **The canonical multi-scenario data contract** | `...\V4_2_multi_scenario_data_contract\canonical_data_contract.md` |
| **Scenario entity definition (30 fields)** | `...\V4_2_multi_scenario_data_contract\canonical_scenario_entity.md` |
| **What to do when only a metrics table exists** | `...\V4_2_multi_scenario_data_contract\metrics_only_scenario_options.md` |
| **THE TAXONOMY — start here for scope** | `...\V4_3B_stakeholder_scope_taxonomy_alignment\canonical_taxonomy.md` |
| **Metric × dimension matrix** | `...\V4_3B_stakeholder_scope_taxonomy_alignment\metric_taxonomy_matrix.csv` |
| **Per-metric mappings** | `...\V4_3B...\hdd_edb_taxonomy_mapping.md`, `cpu_taxonomy_mapping.md`, `ssd_phoenix_taxonomy_mapping.md`, `ssd_mcdb_taxonomy_mapping.md` |
| **What is still undecided by stakeholders** | `...\V4_3B_stakeholder_scope_taxonomy_alignment\pending_stakeholder_decisions.md` |
| **Which computations are possible per metric** | `...\V4_4_drift_family_semantic_review\metric_family_computability_matrix.md` |
| **Grain requirements (fact vs metrics)** | `...\V4_5_metric_candidate_review\grain_requirement_matrix.md` |
| **Source availability and retention depth** | `...\V4_5_metric_candidate_review\source_availability_and_retention.md` |
| **Unit / scale compatibility rules** | `...\V4_5_metric_candidate_review\unit_and_scale_compatibility.md` |
| **Filter / dropdown design already agreed** | `...\V4_6_plan_to_plan_dropdown_design\metric_selector_design.md`, `dbtype_scenario_design.md` |

### 0.2 The complete list of source tables discovered

Eleven `forecast_substrateBE_*` objects are named in the evidence:

| Table | Metric | Type | Grain |
| --- | --- | --- | --- |
| `forecast_substrateBE_hdd_region` | HDD-EDB | **FACT** | region, per target date |
| `forecast_substrateBE_hdd_region_metrics` | HDD-EDB | metrics | region, per key |
| `forecast_substrateBE_hdd_forest_metrics` | HDD-EDB | metrics | **forest** (155 keys, e.g. `APCP150`, `NAMP108`) |
| `forecast_substrateBE_ssd_phx_lvwe_metrics` | SSD-Phoenix | metrics | Low-Vol **with** Efficiency |
| `forecast_substrateBE_ssd_phx_lvne_metrics` | SSD-Phoenix | metrics | Low-Vol **no** Efficiency |
| `forecast_substrateBE_SSD_TotalForecast` | SSD (shared?) | **NOT LOCATED** | — |
| `forecast_substrateBE_SSD_Phoenix_Organic` | SSD-Phoenix | **NOT LOCATED** | — |
| `forecast_substrateBE_cpu` | CPU | unverified | — |
| `forecast_substrateBE_cpu_region` | CPU | unverified | region |
| `forecast_substrateBE_cpu_byDB_region` | CPU | unverified | region × DB |
| `forecast_substrateBE_cpu_byDB_forest` | CPU | unverified | forest × DB |

E1B recorded that **roughly 40 `substrateBE` tables exist** in the source. Only the eleven above have been named in evidence.

### 0.3 The single most important structural fact

> **Only `forecast_substrateBE_hdd_region` is a FACT table. Everything else discovered is a `_metrics` table.**

A metrics table stores **aggregated accuracy per key per version** — MAPE, Bias, Accuracy and so on. It has **no target-date dimension**.

Consequences, verified in V4.4 and V4.5:

| Computation | Needs | Works on a metrics table? |
| --- | --- | --- |
| Accuracy / error metrics (MAPE, Bias, RMSE…) | key × version | **Yes** |
| Anything comparing forecast **curves** over time | key × version × **target date** | **No** |
| Anything measuring revision **per horizon point** | same | **No** |

**This is a grain problem, not a volume problem.** No amount of extra rows fixes it. If the Code Improvement project needs per-horizon analysis for SSD or CPU, a **fact table must be located or built** — that is the blocking prerequisite.

### 0.4 Retention depth — the second blocking constraint

| Table | Versions retained | Verified |
| --- | --- | --- |
| `forecast_substrateBE_hdd_region` (fact) | **48** (2021-06 → 2026-05) | E1B |
| `_hdd_region_metrics` | **3** | E1B |
| `_hdd_forest_metrics` | **3** (155 forest keys) | E1B |
| **`_ssd_phx_lvwe_metrics`** | **1** (2026-03-12) | E1A / E1B |
| **`_ssd_phx_lvne_metrics`** | **1** (2026-03-12) | E1A / E1B |

**One version cannot support any cross-version comparison.** Two versions is the absolute minimum for any change-over-time measure.

---

## PART 1 — EXPLAIN: what we need and why

Use this section to brief stakeholders or to frame the work.

### 1.1 The ask

Sihui and Chinmay asked that the work cover **all Metrics and Scenarios**, not HDD alone. The Drift project translated that into a governed taxonomy. **The Code Improvement project should adopt the same taxonomy** so both projects speak one language.

### 1.2 The taxonomy (adopt verbatim)

Seven ordered layers, each depending only on its ancestors:

```
Metric → DB Type → Scenario → Granularity → Key / Region / Forest
       → Current Forecast Cycle → Compare Against
```

| Layer | Meaning | Example values |
| --- | --- | --- |
| **Metric** | The principal entity. **Single-select, never "All".** | HDD-EDB, SSD-Phoenix, SSD-MCDB, CPU |
| **DB Type** | Sub-partition of the metric | EDB, Phoenix, MCDB, Total, Organic |
| **Scenario** | Planning segment | Enterprise, Consumer, (CPU: Consumed / Failover — unconfirmed) |
| **Granularity** | Aggregation grain. **Single-select.** | Region, Forest |
| **Entity** | The key itself | `APC-MULTITENANT` (region), `NAMP108` (forest) |
| **Current cycle** | The plan being examined | a `ForecastVersion` |
| **Compare against** | An **earlier** compatible plan | strictly prior version |

**Critical rule:** never aggregate across Metrics. Different Metrics carry different units — TB, PB, GCycles — and summing them is meaningless. See `unit_of_measure_contract.md`.

### 1.3 The four Metrics in initial scope

| Metric | Canonical id | Status |
| --- | --- | --- |
| HDD-EDB | `hdd_edb` | **Ingested and working** |
| SSD-Phoenix | `ssd_phoenix` | Metrics tables only, 1 version |
| SSD-MCDB | `ssd_mcdb` | Source not identified |
| CPU | `cpu` | Tables named, never profiled |

Also recorded: **HDD-Basilisk is being phased out** (1 version observed); **IOPS is deferred**; **AD is future discovery**.

### 1.4 Terminology trap — do not repeat this mistake

The word **"Scenario"** means two different things:

| Context | Meaning |
| --- | --- |
| **AX4S portal** | A whole product line + resource + grain, e.g. *"HDD EDB Region"* |
| **AEGIS data model** | A planning segment only, e.g. *Enterprise* or *Consumer* |

The Drift project resolved this by introducing **`metric_id`** as a layer *above* scenario, and keeping `scenario` for the planning segment alone. **Adopt the same separation.** Overloading one column with both meanings will cause silent, hard-to-diagnose defects.

Reference: `V4_1...\terminology_and_semantics.md` and `V4_3B...\v4_2_taxonomy_addendum.md`.

---

## PART 2 — DIAGNOSE: how to assess any Metric before implementing

Run this checklist per Metric. **Do not write code until a Metric passes.**

### 2.1 The diagnostic sequence

| # | Question | How to answer | Blocks if |
| --- | --- | --- | --- |
| D1 | Does a table exist? | Query source catalogue for `forecast_substrateBE_*` | Not found → stop, escalate |
| D2 | **Is it a FACT or a `_metrics` table?** | Does it have a **target-date** column? | Metrics-only → only accuracy measures are possible |
| D3 | **How many versions are retained?** | `COUNT(DISTINCT ForecastVersion)` | **1 version → no comparison possible at all** |
| D4 | What is the key grain? | Inspect `Key` format | Region and forest keys are **not** interchangeable |
| D5 | What Scenario values exist? | `SELECT DISTINCT Scenario` | Unknown values → confirm with stakeholders |
| D6 | What is the unit? | **Not in the data dictionary** — ask | Unknown → cannot compare or aggregate raw values |
| D7 | Are there extra dimensions? | CPU tables carry **Fleet** and **Workload**, absent in HDD | Yes → the canonical key must be decided first |
| D8 | Do realised actuals exist? | Check the actuals source for overlap | No → accuracy cannot be computed yet |

### 2.2 Decision table — what is possible given D2 and D3

| Fact table? | Versions | What you can build |
| --- | --- | --- |
| Yes | ≥ 4 | Everything |
| Yes | 2–3 | Comparison and curve analysis; not multi-version dispersion |
| Yes | 1 | Nothing comparative |
| **No (metrics only)** | ≥ 2 | **Accuracy trends only** |
| **No (metrics only)** | **1** | **Nothing** |

### 2.3 Current diagnosis per Metric

| Metric | D1 table | D2 grain | D3 versions | Verdict |
| --- | --- | --- | --- | --- |
| **HDD-EDB region** | ✅ | **FACT** | 48 | **Fully workable** |
| HDD-EDB forest | ✅ | metrics | 3 | Accuracy only, 155 keys |
| **SSD-Phoenix LVWE** | ✅ | metrics | **1** | **Blocked — nothing computable** |
| **SSD-Phoenix LVNE** | ✅ | metrics | **1** | **Blocked — nothing computable** |
| SSD-Phoenix Total / Organic | ❌ not located | — | — | Blocked — find the table |
| SSD-MCDB | ❌ not identified | — | — | Blocked — identify the source |
| CPU | Named, unprofiled | unknown | unknown | **Profile first** — most tractable |

**CPU is the best next candidate.** Its tables are named and it plausibly has a fact-grain table (`forecast_substrateBE_cpu_region`). What is missing is a *decision* about the canonical key given Fleet and Workload, not data.

### 2.4 Open stakeholder decisions that block implementation

| ID | Question | Blocks |
| --- | --- | --- |
| **D2** | Are PHX-Total / Organic / Low-Vol±Efficiency **DB Types**, **Scenarios**, or a variant flag? | SSD-Phoenix modelling |
| **D3** | Are CPU Consumed / Failover Scenarios or DB Types? Where do Fleet and Workload belong? | CPU modelling |
| **D4** | Exact table names for CPU, SSD-Total, MCDB | All three |
| **D5** | Units per metric (TB / PB / GCycles) | Any raw-value comparison |
| **D10** | Is `SSD_TotalForecast` shared between Phoenix and MCDB? If so, what discriminates them? | Both SSD metrics |

Full text in `V4_3B...\pending_stakeholder_decisions.md`.

---

## PART 3 — IMPLEMENT: how to build it

### 3.1 Golden rule

> **Make the code data-driven and configuration-driven. Never branch on a metric name.**

Anything shaped like `if metric == "hdd"` will have to be rewritten for every new Metric. The Drift project designed a declarative adapter contract precisely to avoid this: `V4_2...\source_adapter_contract.md`.

### 3.2 Find and remove the hardcoding

The Drift project's engine had exactly four blocking hardcodes. **Expect the same pattern in Code Improvement.**

| Constant | Was | Severity |
| --- | --- | --- |
| `FACT_TABLE` | fixed to `hdd_region` | **Blocker** |
| `METRICS_TABLE` | fixed to `hdd_region_metrics` | **Blocker** |
| `RESOURCE_SCOPE` | fixed to `"HDD"` | **Blocker** |
| `SCENARIO_SCOPE` | fixed to `"Enterprise"` | High |
| `VALUE_TYPE` | fixed to `"Forecast-Mean"` | Medium |

Full inventory with line references: `V4_1...\multi_scenario_hardcode_inventory.csv`.

**Do the same audit in Code Improvement**: grep the configuration and query layer for any literal table name, resource string or scenario string, and catalogue every one before changing anything.

### 3.3 Recommended architecture

```
Source tables (per Metric)
        ↓
   Metric adapter          ← declarative, one config entry per Metric
        ↓
  Canonical row schema     ← identical shape regardless of source
        ↓
     Computation           ← metric-agnostic
        ↓
   Governed outputs        ← carry metric_id, scenario_id, contract_version
        ↓
      Dashboard            ← filters only
```

The canonical row must carry, at minimum: `metric_id`, `db_type`, `scenario`, `granularity`, `key`, `region`, `forest`, `forecast_version`, `target_date`, `value`, `value_type`, `unit`, `source_object`, `contract_version`.

Field-by-field specification: `V4_2...\canonical_data_contract.md`.

### 3.4 Registry pattern

Keep one configuration entry per Metric. A worked, non-productive example with sentinel values and **no credentials** is at `V4_2...\scenario_registry.example.yaml`.

Each entry should declare: canonical id, display name, fact table, metrics table, scenario values, granularity, key pattern, unit, available families/computations, retention depth, and status.

### 3.5 Isolation rules — non-negotiable

| Rule | Statement |
| --- | --- |
| R1 | **Never** compute across two Metrics |
| R2 | Never compare a region key against a forest key |
| R3 | Never compare across DB Types |
| R4 | Never sum raw values with different units |
| R5 | Every output row carries its `metric_id` |
| R6 | A Metric with insufficient data is reported as **unavailable**, never silently defaulted |

R6 matters most in practice. When SSD-Phoenix cannot be computed, the correct behaviour is an explicit *"not computable — insufficient version history"*, **not** an empty chart and **not** a zero.

### 3.6 Backward compatibility

**HDD-EDB output must remain byte-identical after the refactor.** The Drift project treated this as a hard gate: same rows, same values, same hashes, no recomputation.

Approach: refactor to the canonical shape, re-run, and diff against the pre-refactor output. **Any difference is a defect until proven otherwise.**

Reference: `V4_2...\backward_compatibility_mapping.md`.

### 3.7 Suggested order of work

| Phase | Work | Gate |
| --- | --- | --- |
| 1 | Hardcode audit and inventory | Every literal catalogued |
| 2 | Define the canonical schema | Reviewed |
| 3 | Refactor HDD-EDB onto it | **Output byte-identical** |
| 4 | Build the adapter and registry | HDD still identical |
| 5 | Profile CPU (diagnostic only) | D1–D8 answered |
| 6 | Onboard CPU | Isolation rules hold |
| 7 | SSD-Phoenix | **Blocked** until retention and grain are resolved |

**Do not start phase 5 before phase 3 passes.** Onboarding a second Metric onto an unproven abstraction is how both Metrics end up broken.

---

## PART 4 — Answering Boon's specific question

> *"I saw some forecasting error with SSD-Phoenix for NAMPRD07. Want to see if your accuracy portal registers anything."*

**Short answer: no, and here is exactly why.**

| Reason | Evidence |
| --- | --- |
| **1. SSD-Phoenix was never ingested.** The pipeline reads `forecast_substrateBE_hdd_region` only. | `multi_scenario_hardcode_inventory.csv` |
| **2. Only metrics tables exist for SSD-Phoenix** — `_ssd_phx_lvwe_metrics` and `_ssd_phx_lvne_metrics`. No fact table has been located. | `ssd_phoenix_taxonomy_mapping.md` |
| **3. Both retain a single version (2026-03-12).** One version cannot support any cross-version comparison. | E1A / E1B |
| **4. `NAMPRD07` looks like a forest-grain key.** Documented forest keys follow the same shape (`APCP150`, `NAMP108`) and live in `_hdd_forest_metrics`. Current HDD processing runs at **region** grain. | `E1A_data_dictionary.csv`, E1B §6.3 |

**Point 4 needs confirming rather than asserting.** `NAMPRD07` matches the forest key shape, but no evidence in this repository ties that identifier to an SSD-Phoenix table. Worth asking Boon which table or portal view he was looking at.

### Suggested reply to Boon

> No — the accuracy portal wouldn't show anything for that yet. It currently only ingests HDD-EDB at region grain.
>
> For SSD-Phoenix specifically there are two blockers. The only tables we've found are the Low-Vol metrics tables (`lvwe` / `lvne`), and each retains a **single** forecast version from 2026-03-12 — so there's nothing to compare against. Second, those are metrics tables with no target-date dimension, so per-horizon error analysis isn't possible from them at all; we'd need a fact table.
>
> Also, `NAMPRD07` looks like a **forest**-level key, and today we run at region grain. Could you confirm which table or view you saw the error in? That would tell us whether there's an SSD-Phoenix source we haven't catalogued.
>
> We've already mapped all four Metrics and their sources as part of the drift work — happy to walk through it. The gap for SSD-Phoenix is source availability, not analysis capability.

**Do not tell Boon that "nothing is wrong".** The honest statement is that **we cannot see it yet**, which is a different claim.

---

## PART 5 — What the receiving agent must not do

| Prohibition | Reason |
| --- | --- |
| Do not fabricate results for SSD-Phoenix, SSD-MCDB or CPU | No governed data exists. The Drift project classified all three `UNKNOWN_PENDING_EVIDENCE`. |
| Do not assume a metrics table can support curve analysis | Grain problem, not volume |
| Do not assume forest and region keys are interchangeable | 155 forest keys against 45 region keys |
| Do not aggregate raw values across Metrics | Different units |
| Do not resolve D2/D3/D4/D5/D10 unilaterally | Stakeholder decisions |
| Do not change HDD-EDB behaviour while adding Metrics | Backward compatibility gate |
| Do not branch on metric names in code | Defeats the whole exercise |

---

## Appendix — Verified figures worth reusing

| Fact | Value | Source |
| --- | --- | --- |
| HDD region keys | 45 in source, 12 governed | E1B |
| HDD forest keys | **155** | E1B §6.3 |
| Fact table versions | 48 monthly, 2021-06 → 2026-05 | E1B |
| Metrics table retention | 3 versions (HDD), **1** (SSD-Phoenix) | E1A / E1B |
| Scenario values observed | Enterprise (48v), Consumer (47v), Basilisk (1v) | E1B |
| Fact table columns | DateTime, Key, Value, ModelVersion, ForecastVersion, Scenario, Resource, ValueType | E1A |
| Region is **embedded in `Key`** | no separate Region column | E1A |
| No `Service` column exists | — | E1A |
| CPU tables carry Fleet and Workload | absent in HDD | E1B §6.5 |
| `substrateBE` tables in source | ~40 | E1B §6.4 |

**Every figure above is traceable to a named document.** If a number is needed that is not in this table, derive it from the source and cite it — do not estimate.

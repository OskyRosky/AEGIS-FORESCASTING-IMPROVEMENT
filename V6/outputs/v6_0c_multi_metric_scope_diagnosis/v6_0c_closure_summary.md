# AEGIS V6.0C — Closure Summary

**Stage:** V6.0C — Multi-Metric Scope Diagnosis
**Status:** `V6_0C_MULTI_METRIC_SCOPE_DIAGNOSIS_COMPLETED`
**Date:** 2026-08-11
**Nature:** Diagnosis and evidence freeze only. No functional change, no SQL, no Azure resource, no Shiny edit, no producer re-run.

---

## 1. What this stage established

The premise that SSD-Phoenix "was never ingested" is false for this repository.
Both SSD-Phoenix metrics tables are present locally with 7,776 and 7,913 rows
covering 137 forest keys each. The real problem is that the pipeline destroys
source identity during consolidation and never exposes the result in Shiny.

Three findings change the plan:

1. **SSD-Phoenix grain is now verified, not inferred.** All 137 LVWE keys and all
   137 LVNE keys are a strict subset of the 155 HDD forest keys, with zero
   intersection against the 45 region keys.
2. **Scenario cannot be a mandatory filter level.** It exists only on the fact
   table. Four of the six local sources have no Scenario column at all.
3. **The local HDD fact snapshot holds a single forecast version.** Cross-plan and
   drift work is currently impossible for HDD as well, not only for SSD.

## 2. The ranking defect, measured

`_build_rankings` groups by `Key` and `Forecast_Version`. LVWE and LVNE share
both. The result is 137 ranking rows that average two distinct series.

- 137 of 736 groups are contaminated.
- 15,689 of 27,067 rows are folded, which is 58.0 percent of the dataset.
- `baseline_rankings.csv` has no column that can separate them after the fact.

For `NAMPRD07` the published value 4.5058 sits between LVNE 4.4984 and LVWE
4.5133 and corresponds to no real series.

## 3. Computability, honestly stated

| Capability | HDD region metrics | HDD forest metrics | SSD-Phoenix LVWE and LVNE |
| --- | --- | --- | --- |
| Point accuracy | Yes | Yes | Yes |
| Cross-plan comparison | Yes, 3 versions | Yes, 3 versions | No, 1 version |
| Forecast curve by target date | No | No | No |
| Exposed in Shiny today | No | No | No |

## 4. Deliverables

Ten artifacts in `V6/outputs/v6_0c_multi_metric_scope_diagnosis/`, covering the
full known universe of 17 metric and source combinations across HDD-EDB,
SSD-Phoenix, SSD-MCDB, CPU, IOPS and the retired HDD-Basilisk scenario.

## 5. Governance

All six frozen artifacts rehash unchanged. Git reports no modification to any
tracked file under `V6/python`, `V6/shiny_app`, `V6/data` or `V6/outputs/metrics`.
The only repository addition is this output folder.

## 6. Blockers carried forward

Nothing blocks the closure of V6.0C. Four stakeholder decisions block later
construction: the SSD-Phoenix classification, the CPU classification, the exact
table names for CPU, SSD-Total and MCDB, and the shared-table discriminator
question. Units remain undocumented for every metric, including HDD.

## 7. Next stage

**V6.0D — Canonical Multi-Metric Contract.** Not authorised yet. It must define
the column contract, the isolation rules, Scenario optionality and the unit rules,
and it must cover every row of the inventory rather than the SSD case alone.

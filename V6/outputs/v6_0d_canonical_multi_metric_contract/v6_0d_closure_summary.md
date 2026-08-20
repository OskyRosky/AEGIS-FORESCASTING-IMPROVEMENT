# AEGIS V6.0D — Closure Summary

**Stage:** V6.0D — Canonical Multi-Metric Contract
**Status:** `V6_0D_CANONICAL_MULTI_METRIC_CONTRACT_COMPLETED`
**Date:** 2026-08-11
**Nature:** Contract design and governance only. No builder, no Shiny change, no legacy artifact modified, no SQL, no Azure.

---

## 1. What this stage produced

A complete, metric-agnostic contract that makes the V6.0C defects structurally
impossible rather than individually patched.

The central object is the **identity tuple**:

```
metric_id + db_type + scenario + granularity + entity_key + forecast_version
```

Aggregation is legal only when all six components match. LVWE and LVNE share five
of the six and differ in `db_type`, so the 137-group blend measured in V6.0C
cannot recur under this contract. A second guard asserts that a ranking row draws
from exactly one `source_object` unless the registry explicitly allows merging,
which keeps the guarantee intact even if stakeholder decision D2 reclassifies the
SSD variants later.

## 2. Design decisions worth highlighting

| Decision | Rationale |
| --- | --- |
| Scenario is optional with `not_applicable` as a real value | Verified in V6.0C that four of six local sources have no Scenario column at all |
| `unit` is mandatory and defaults to `UNKNOWN` | No unit is documented for any metric including HDD; assuming TB or PB would be fabrication |
| Capability is declared by the producer, not inferred by the UI | Keeps Shiny metric-agnostic and prevents charts that misrepresent single-version data |
| New artifacts live in `outputs/metrics_multi/` | Already inside the container read-only mount, so they are visible locally and in Azure later. Answers Q17 |
| Ranks are computed within a metric partition | A cross-metric rank has no meaning when units differ |
| Failing quality rows are flagged and kept | Silent dropping is the failure mode this whole workstream exists to remove |

## 3. Deliverables

Fifteen artifacts in `V6/outputs/v6_0d_canonical_multi_metric_contract/`,
covering the canonical column contract (44 columns), nine artifact contracts for
V6.0E, the Shiny filter contract, the computability and availability vocabularies,
the unit contract, the lineage contract, the assistant grounding contract, 35
required tests, the marker plan and the preliminary Boon draft.

## 3b. Assistant preservation invariant

The AI explanation layer is treated as a product feature that must survive the
expansion. Inventoried in this stage: `llm_explain.R` at 860 lines,
`llm_compose.R` at 282 lines, the `llm_summary` module, and a 74 KB evidence pack
holding 11 page responses, 108 traceable claims and 78 source references.

The contract preserves it and extends it additively. The frozen pack keeps
answering page-level questions; a new `metric_assistant_evidence_pack.json`
supplies multi-metric selection context using the same field shapes. Ten grounding
rules keep the assistant artifact-only: no live SQL, no training, no
recalculation, no mutation, no unsupported claims, no cross-metric raw
aggregation, no invented scenarios, and never describing single-version accuracy
as drift. Tests T26 to T35 verify UI presence, artifact reading, selection
context, drift justification, scenario honesty, exports and Docker parity.

## 4. Markers updated

Both stale markers found in V6.0C defect D-08 were corrected as documentation:

- `V6/VERSION_INFO.md` now names V6.0D as current, V6.0E as next, records the
  Azure pause, and corrects the rule that still told readers to work inside V5.
- `V6/config/project_root_policy.json` now points to V6.0E and records
  `azure_deployment_status = paused_until_v6_0h` and
  `multi_metric_contract_version = v6.0d`. The file still parses as valid JSON.

No logic, no governance field and no legacy artifact was touched.

## 5. Governance

All six frozen artifacts rehash unchanged. Git reports modifications to exactly
two files, both markers, both documentation-only. No entry appears under
`V6/shiny_app`, `V6/python`, `V6/data` or `V6/outputs/metrics`.

## 6. What remains blocked

The contract is deliberately valid under every possible resolution of the open
decisions, so none of them blocks V6.0E from building the sources that already
exist locally. They do block onboarding new metrics:

| Decision | Blocks |
| --- | --- |
| D2 SSD-Phoenix Total, Organic and Low-Vol classification | Only the registry label, not the isolation guarantee |
| D3 CPU Consumed and Failover plus Fleet and Workload | CPU onboarding |
| D4 Exact table names for CPU, SSD-Total and MCDB | CPU and MCDB onboarding |
| D5 Real units for every metric | Any raw value comparison |
| D10 Shared table discriminator | Separating MCDB from Phoenix |

## 7. Next stage

**V6.0E — Multi-Metric Artifact Builder.** Not authorised yet. It must build the
eight contracted artifacts from a declarative registry, pass all 25 tests, and
leave every frozen artifact byte-identical.

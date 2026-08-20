# V6.0C — Stage Map Update

**Status:** proposed in V6.0C. Azure work is paused, not cancelled.

## Revised V6 sequence

| Order | Stage | Name | Objective | Exit gate |
| --- | --- | --- | --- | --- |
| 1 | **V6.0A** | Baseline Clone | Clone V5 into V6 with parity | CLOSED `V6_0A_BASELINE_CLONE_COMPLETED` |
| 2 | **V6.0B** | Azure Readiness Decisions | Hosting, auth, storage, registry decisions | CLOSED `V6_0B_AZURE_READINESS_DECISIONS_COMPLETED` |
| 3 | **V6.0C** | Multi-Metric Scope Diagnosis | Inventory, coverage, computability, defects, baseline freeze | This stage |
| 4 | **V6.0D** | Canonical Multi-Metric Contract | Column contract, isolation rules, Scenario optionality, unit rules | Contract covers every source in the inventory, not only SSD |
| 5 | **V6.0E** | Multi-Metric Artifact Builder | Registry plus adapters producing new normalized artifacts | HDD legacy artifacts byte-identical; rankings isolated by metric and db_type |
| 6 | **V6.0F** | Shiny Multi-Metric Integration | Dependent filters and Accuracy bound to official metrics | Smoke visual plus functional cases; read-only preserved |
| 7 | **V6.0G** | Boon Evidence Pack | SSD-Phoenix and NAMPRD07 evidence with explicit limits | Numbers validated against source tables |
| 8 | **V6.0H** | Docker V6 Revalidation | Container runs with the expanded universe | HTTP 200, filters, downloads, no mutation, no raw, no secrets |
| 9 | **V6.1+** | Azure Deployment Resume | Identity, RBAC, Key Vault, ACR, ACA | Only after V6.0H passes |

## Rules carried into every following stage

1. No implementation may branch on a metric name.
2. `NAMPRD07` is a validation case, never a coded special case.
3. Legacy governed CSVs are additive-only: new dimensions live in new artifacts.
4. Scenario is optional and resolves to `not_applicable` when the source has no column.
5. Raw values are never aggregated across `metric_id`.
6. A metric with insufficient data is reported as unavailable with a reason, never as zero or an empty chart.
7. New artifacts must land under `data/processed` or `outputs`, the only paths mounted into the container.

## Marker files to update at closure

Both files below are documentation-only updates. No functional change is implied.

| File | Current | Should become |
| --- | --- | --- |
| `V6/VERSION_INFO.md` | `next_stage = V6.1`; active-root rules still name V5 | `next_stage = V6.0D`; active root is V6 |
| `V6/config/project_root_policy.json` | `next_stage = V6.0A`, `next_block = V6.0B` | `next_stage = V6.0C closed`, `next_block = V6.0D` |

These updates are **proposed** by V6.0C and were not applied, because the stage
rules restrict changes to documentation produced by this stage. Apply them on
explicit authorisation together with the V6.0D kickoff.

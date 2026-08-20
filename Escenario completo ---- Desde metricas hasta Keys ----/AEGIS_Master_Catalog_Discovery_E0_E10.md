# AEGIS Master Catalog Discovery E0-E10

## Executive Status

| Field | Value |
|---|---|
| Project | Microsoft AEGIS / Feature 6986096 |
| Empirical source | `TesseractEarthDW` |
| Database mode | READ ONLY |
| Completed stages | E0, E0.1, E1.P0, E1 Candidate Boundary Qualification, E1.CF, E1.2-E1.4, E2, E3, E4, E5, E6, E7, E8, E9 |
| Roadmap | E0-E11 (master filename intentionally unchanged) |
| Current stage | E9 COMPLETE, awaiting authorization |
| E1 status | CLOSED BY OWNER SCOPE DECISION |
| Roadmap markers | `RM-E1-CLOSED` through `RM-E9-CLOSED` |
| Current MVP base Metrics | 5: CPU, HDD, IOPS, SSD, Memory |
| Canonical DB Types | 5: Phoenix, NonPhoenix, EDB, Basilisk, MCDB |
| Canonical Granularities | 3: Forest, Forest_SKU, Region |
| Canonical Scenarios | 2: Consumed, Failover (CPU and IOPS only) |
| Canonical Segments | 2: Consumer, Enterprise (HDD organic branch only) |
| Canonical demand natures | 2: Organic, Inorganic |
| Canonical Regions | 35, of which 33 are physically routable |
| Environments embedded in Region tokens | 11 |
| Region-capable branches | 17 (16 routable + 1 serving-empty) |
| Logical Key axis | NONE: `NO_GLOBAL_KEY_UNIVERSE` |
| Key/MyKey actual semantics | Region token, Forest alias, or Forest+SKU composite |
| Forests | 173, rolling up to 35 regions with no multi-region forest |
| E3 branches | 12, all classified for Granularity and for the three E6 axes |
| Metrics with a DB Type axis | 3: CPU, HDD, SSD |
| Metrics without | 2: IOPS, Memory |
| Navigation contract | 41 nodes: 23 show, 6 skip, 1 terminal, 11 unresolved |
| Extra axes detected, not modelled | SKU, Stripe, DAG, Environment |
| Current MVP operational labels | 9 |
| Master table scoped rows | 15 (9 dashboard labels + 6 CPU coverage-gap combinations) |
| Deferred active families | 5: ROPS, AD, P95ItemsPerShard, P95ShardCpuUtil, P95ShardSizeInGb |
| E2 query budget | 28 / 30 |
| E3 query budget | 4 / 30 |
| E4 query budget | 9 / 20 |
| E5 query budget | 14 / 30 |
| E6 query budget | 8 / 20 |
| E7 query budget | 5 / 12 |
| E8 query budget | 7 / 10 |
| E9 query budget | 3 / 10 |
| Last executed step | E9 Key semantics |
| Next action | E10 Source Table, on authorization |
| E10 status | NOT STARTED |
| Last updated | 2026-08-17 |

## Current Master Taxonomy

The investigation tree remains:

```text
Metric
  -> DB Type
  -> Granularity
  -> Region
  -> Key
```

`Scenario` remains physically preserved as evidence but is not currently a
master-table axis. `Source Table` will be appended in E9.

The boundary-discovery candidate boundary closed at 535 objects, and E1.2-E1.4
executed and closed under owner scope decision `RM-E1-CLOSED`.

### Product scope versus discovery scope

These are two different things and must never be conflated:

| Concept | Value | Meaning |
|---|---|---|
| `CURRENT_MVP_BASE_METRIC_COUNT` | 5 | PRODUCT-SCOPE ANNOTATION |
| `MASTER_TABLE_SCOPED_ROW_COUNT` | 15 | PRODUCT-SCOPE ANNOTATION |
| Discovery scope for E2-E10 | ALL data-evidenced families | TAXONOMY SCOPE |

```text
PRODUCT_SCOPE_ANNOTATION != DISCOVERY_LIMIT
```

E2 through E10 must discover the **complete** set of values on every axis
(DB Type, Granularity, Region, Key) across **all** metric families that have
data evidence, including ROPS, AD, P95ItemsPerShard, P95ShardCpuUtil and
P95ShardSizeInGb.

The goal of this catalog is to know every filter and every valid combination
that exists in the data. The final table will contain more than 15 rows, and
that is the expected outcome, not a scope violation.

The five-Metric and 15-row annotations mark what the current product implements.
They mark nothing about what the discovery must find.

## Method

Each level follows:

```text
UNIVERSE
  -> REAL CROSS
  -> VALIDATION
  -> FREEZE LEVEL
  -> NEXT LEVEL
```

Evidence classifications:

```text
CONFIRMED
SUPPORTED_HYPOTHESIS
HYPOTHESIS
AMBIGUOUS
NOT_FOUND
NOT_APPLICABLE
```

The database evidence takes precedence over historical taxonomy assumptions.

## E0 Historical Record

### Purpose

Determine where Metric, DB Type, Scenario, Granularity, Region, Forest, Key and
ForecastVersion physically live.

### Boundary evolution

| Sweep | Objects | Result |
|---|---:|---|
| `forecast_substrateBE_*` / `substrateBE_*` prefixes | 153 | Incomplete |
| Objects containing `SubstrateBE` | 366 | Found additional views and Memory |
| `forecast_*`, `vw_forecast_*`, or containing `SubstrateBE` | 490 | Initial E0 scope |
| Broad `forecast` or `substrateBE` sweep | 550 | Inspected in E0.1 |

The Memory objects that proved the prefix boundary incomplete included:

```text
vw_SubstrateBE_Demand_Memory_Forest
vw_SubstrateBE_Demand_Memory_Region
vw_SubstrateBE_MemoryRawData
```

### E0 structural findings

| Finding | Count |
|---|---:|
| Objects in initial final scope | 490 |
| Tables | 300 |
| Views | 190 |
| Column metadata rows | 4,849 |
| Exact `Metric` column | 3 objects |
| `MetricName` column | 16 objects |
| `DBType` column | 2 objects |
| `Scenario` column | 65 objects |
| `ScenarioId` column | 5 objects |
| `Granularity` column | 16 objects |
| `Region` column | 206 objects |
| `Key` column | 134 objects |
| `ForecastVersion` column | 107 objects |
| `Forecast_Version` column | 6 objects |
| `ModelVersion` column | 35 objects |

Structural populations:

| Population | Objects |
|---|---:|
| Explicit-column driven | 19 |
| Table-name / contract driven | 376 |
| Other ambiguous | 95 |

## E0.1 Historical Record

### Inspected 550-object boundary

| Judgment | Objects |
|---|---:|
| IN_SCOPE | 405 |
| AMBIGUOUS | 140 |
| OUT_OF_SCOPE | 5 |
| Total | 550 |

The conservative E1 candidate boundary was:

```text
405 IN_SCOPE + 140 AMBIGUOUS = 545
```

### Previously excluded 60

| Judgment | Objects |
|---|---:|
| IN_SCOPE | 10 |
| AMBIGUOUS | 45 |
| OUT_OF_SCOPE | 5 |

### Third population

The 95 structurally ambiguous objects collapsed into 63 exact column-signature
families:

| Structural judgment | Families | Objects |
|---|---:|---:|
| FACT_TABLE | 36 | 57 |
| AGGREGATE | 15 | 21 |
| DIMENSION_LOOKUP | 2 | 3 |
| STAGING_ARTIFACT | 3 | 3 |
| CANNOT_DETERMINE_FROM_METADATA | 7 | 11 |

### Legacy correction

```text
81 substring matches
  -> 57 confirmed legacy-token objects
  -> 24 false positives caused by "Latest"
```

The legacy objects were marked and not deleted.

## E1 Status

### Authorization

E1 only. E2 was not authorized.

### Required order

```text
E1.P0
  -> E1.0
  -> E1.1
  -> E1.2
  -> E1.3
  -> E1.4
```

E1.P0 contained a mandatory stopping rule:

```text
If NEW_CANDIDATE > 30:
  preserve evidence
  mark E1 PARTIAL
  stop before business-value discovery
```

The stopping rule triggered.

## E1.P0 - Global Structural Assurance

### Purpose

Independently test the previous naming boundary against every user table and
view in `TesseractEarthDW`.

### Queries

Only `sys.objects`, `sys.schemas`, `sys.columns` and `sys.types` were queried.
No business values were read.

### Results

| Result | Count |
|---|---:|
| All user tables/views | 1,204 |
| Inside previous 550 | 550 |
| Outside previous 550 | 654 |
| NEW_CANDIDATE | 33 |
| AMBIGUOUS | 23 |
| NOT_FORECAST_LIKE | 598 |

All 1,204 objects received:

```text
ObjectName
ObjectType
CompleteColumnSignature
ForecastLikeStructuralSignals
InsidePrevious550
Judgment
Reason
```

### Reproducible candidate rules

Generic columns such as `Key`, `Value`, or a date were insufficient alone.

An outside object became `NEW_CANDIDATE` only when its metadata satisfied one
of these combinations:

```text
P0-R1:
  Metric/MetricName
  + forecast version, Scenario, Granularity, forecast field,
    or geo plus date

P0-R2:
  ForecastVersion/ModelVersion
  + Scenario, Granularity, geo, Key, or forecast field

P0-R3:
  Scenario
  + forecast field
  + geo, Key, Metric, or date

P0-R4:
  Forecast field
  + date
  + geo, Key, or Granularity
```

### New candidates

The 33 objects are:

```text
ad_tesseract_ditsize_af_today
binpackedresults_v2
cloudcache_monarch_inorganic
CPG_DemandPlan_SubstrateAD_DitSize_Demand_V2
EOP_FT_retro_MAPE
Finance_CopilotSeats_Projection
Finance_CopilotSeats_Projection_Region
history_cops_gallatin
HLC_BE_FutureSupplyTimeseries
HLC_BE_InOrganicDemandTimeseries
HLC_BE_Installed_Supply_Timeseries
HLC_BE_InstalledSupplyTimeseries
Hotspot_RCA_DemandHistory
Hotspot_RCA_InorganicDemand
Hotspot_RCA_SupplyHistory
Hotspot_RCA_SupplySchedule
Hotspot_RCA_TotalSupplyDemand
JAWS_Azure_Heatmap_clean
JAWS_Azure_HeatmapV2_clean
JAWS_Cosmic_Services_clean
M2CP_Demand_CPU
M2CP_Demand_Forest
M2CP_Demand_HDD
M2CP_Demand_IOPS
M2CP_Demand_SSD
perturbation_config
vw_DAG_Metrics
vw_HLC_BE_SupplyTimeseries
vw_HLC_BE_SupplyTimeseries_History
vw_PBI_CPG_SubstrateAD_Demand_V2
zTempBinpacked
zTempBinpackedresults_20221122
zTempBinpackedresults_v5
```

These are structural candidates only. E1.P0 did not declare any of them a
Metric.

### Decision

```text
NEW_CANDIDATE = 33
Stopping threshold = more than 30
Stopping rule = TRIGGERED
E1 = PARTIAL
```

E1.0 through E1.4 were not executed during the initial P0 run. E1 later resumed
under a dedicated Candidate Boundary Qualification authorization.

## Current Master Taxonomy Status

The candidate-object boundary is closed. The evidence currently suggests six
potential base Metric families:

```text
CPU
HDD
IOPS
SSD
Memory
ROPS
```

This is:

```text
PROVISIONAL - NOT FINAL METRIC COUNT
```

CPU/HDD/IOPS/SSD/Memory have strong evidence. ROPS remains possible pending
full E1 liveness and vocabulary work.

The nine dashboard observations remain observations:

```text
HDD - Basilisk
HDD - EDB
CPU
CPU Failover
IOPS
IOPS Failover
SSD - Phoenix
SSD - MCDB
Memory
```

No final E1 dashboard reconciliation was performed. However,
`Hotspot_RCA_DemandHistory` contains all nine observed labels verbatim, and
`vw_DAG_Metrics` defines those families and multiple variants as SQL constants.

## Open Questions

| Question | Status |
|---|---|
| Which of the 33 candidates should be absorbed into E1? | RESOLVED: 11 in, 20 out, 2 carry |
| Should the 23 P0 ambiguous objects enter value discovery? | RESOLVED: 2 in, 19 out, 2 carry |
| HLC relationship | RESOLVED structurally: five objects participate in confirmed core lineage; one variant carried |
| Hotspot RCA relationship | High-value vocabulary/support evidence; SQL usage remains unresolved |
| M2CP relationship | Consolidated four-family supporting fact; no SQL path to forecast core |
| JAWS and Finance | Outside E1 scope for AEGIS Metric discovery |
| Complete Metric / MetricName vocabulary | NOT EXECUTED |
| Scenario vocabulary | NOT EXECUTED |
| CPU Failover mapping | NOT EXECUTED |
| IOPS Failover mapping | NOT EXECUTED |
| HDD / EDB / Basilisk semantics | Carried to E3 |
| SSD / Phoenix / MCDB semantics | Carried to E3 |
| ROPS scope and currentness | NOT EXECUTED |
| DemandPlan relationship | NOT EXECUTED |
| Legacy currentness | NOT EXECUTED |
| Liveness | NOT EXECUTED |
| Counting contract | NOT EXECUTED |

## E1 Candidate Boundary Qualification

### Owner-level result for the 33

| Measure | Count |
|---|---:|
| Reviewed | 33 |
| NONEMPTY | 28 |
| EMPTY | 5 |
| Data presence unresolved | 0 |
| Connected to confirmed forecast core | 6 |
| Connected only to candidate/ambiguous objects | 3 |
| No dependency path found | 24 |
| Usage unresolved | 0 |
| IN_E1_SCOPE | 11 |
| OUT_OF_E1_SCOPE | 20 |
| AMBIGUOUS_CARRY_FORWARD | 2 |

Direct owner answers:

```text
28 of the 33 actually contain data.
6 of the 33 have dependency evidence connecting them to the active/credible
SubstrateBE forecast core.
```

### B1 - M2CP checkpoint

```text
M2CP_Demand_CPU: EMPTY
M2CP_Demand_HDD: EMPTY
M2CP_Demand_IOPS: EMPTY
M2CP_Demand_SSD: EMPTY
M2CP_Demand_Forest: NONEMPTY, 5,795 rows
```

`M2CP_Demand_Forest` contains raw Metric values:

```text
CPU
HDD
IOPS
SSD
```

No SQL dependency path proves that `M2CP_Demand_*` duplicates, feeds, or is fed
by `forecast_substrateBE_*`. The surviving table is a parallel/supporting
demand-supply planning contract, not evidence of four additional Metrics.

### B2 - HLC

Confirmed lineage:

```text
HLC_BE_InOrganicDemandTimeseries
  -> vw_SubstrateBE_Demand_Forest_Current
  -> vw_SubstrateBE_Demand_Region_Current

HLC_BE_FutureSupplyTimeseries
HLC_BE_InstalledSupplyTimeseries
  -> vw_HLC_BE_SupplyTimeseries
  -> vw_SubstrateBE_MonthsToLive*
```

`HLC_BE_Installed_Supply_Timeseries` is nonempty but has no resolved SQL
consumer. Its latest `CreatedDate` is 2025-12-03. The referenced variant
`HLC_BE_InstalledSupplyTimeseries` has `CreatedDate` 2026-08-16. Without an
approved freshness threshold, the older variant remains carry-forward rather
than being declared stale.

### B3 - Hotspot RCA

`Hotspot_RCA_DemandHistory` contains all nine observed dashboard labels
verbatim, plus variants:

```text
CPU
CPU Failover
IOPS
IOPS Failover
HDD - Basilisk
HDD - EDB
SSD - Phoenix
SSD - MCDB
Memory
```

It also includes Phoenix, NonPhoenix, Basilisk and EDB Consumer/Enterprise
variants. This is high-value taxonomy evidence, but no SQL dependency proves
active dashboard use.

### B4 - Configuration and registry

`perturbation_config` contains 201 rows and raw `MetricName=HDD`. It is a
high-value configuration source, but no SQL dependency to ROPS was found.

`vw_DAG_Metrics` is both:

1. an operational measurement view; and
2. an explicit SQL mapping of Metric labels.

It is directly consumed by numerous dashboard-facing
`vw_SubstrateBE_Demand_*` views and therefore belongs to the confirmed core.

### B5-B7 exclusions

SubstrateAD/DitSize, binpacked service compute, Finance Copilot seats,
CloudCache, EOP traffic, JAWS compute and Cosmic compute were excluded only
when both domain divergence and disconnection from the confirmed SubstrateBE
core were established.

`EOP_FT_retro_MAPE` and CAFE MAPE objects remain relevant as Forecast Accuracy
supporting evidence, but not as AEGIS Metric families.

### 598 heuristic audit

| Measure | Result |
|---|---:|
| P0 NOT_FORECAST_LIKE objects audited | 598 |
| Strong-signal false negatives | 0 |
| Boundary threshold | Not triggered |

### 23 ambiguous objects

| Measure | Count |
|---|---:|
| Reviewed | 23 |
| NONEMPTY | 21 |
| EMPTY | 2 |
| IN_E1_SCOPE | 2 |
| OUT_OF_E1_SCOPE | 19 |
| AMBIGUOUS_CARRY_FORWARD | 2 |

Retained:

```text
IN_E1_SCOPE:
  demandplan_be_demand
  M2CP_Demand_Completed

AMBIGUOUS_CARRY_FORWARD:
  keystone_fulfillment_SupplyDetailLatest
  SM_MLBPhoenixStatsGlobal
```

### Dependency expansion

Only three additional dependency objects appeared, below the guard of 10:

| Object | Judgment |
|---|---|
| `vw_COPSMultitenant_Extend` | IN_E1_SCOPE |
| `vw_HLC_CapacityOrders` | AMBIGUOUS_CARRY_FORWARD |
| `vw_CosmicActualcores` | OUT_OF_E1_SCOPE |

### Final per-object boundary

| Final judgment | Objects |
|---|---:|
| IN_E1_SCOPE | 419 |
| AMBIGUOUS_CARRY_FORWARD | 145 |
| OUT_OF_E1_SCOPE | 640 |
| All user objects | 1,204 |
| Final E1 candidate boundary | **564** |

The 564 count is derived from per-object structural, lineage, presence, domain
and limited operational evidence. It is not produced by a naming `LIKE` rule.

### Provisional Metric-family evidence

| Family | Current status |
|---|---|
| CPU | STRONG_METRIC_FAMILY_EVIDENCE |
| HDD | STRONG_METRIC_FAMILY_EVIDENCE |
| IOPS | STRONG_METRIC_FAMILY_EVIDENCE |
| SSD | STRONG_METRIC_FAMILY_EVIDENCE |
| Memory | STRONG_METRIC_FAMILY_EVIDENCE |
| ROPS | POSSIBLE_METRIC_FAMILY |

Multiple objects support the same family. Dashboard variants such as Failover,
Phoenix, NonPhoenix, EDB, Basilisk and MCDB are not counted as separate base
families at this stage.

## E1 Evidence

Durable directory:

[`evidence/E1/`](evidence/E1/)

| Artifact | Purpose |
|---|---|
| [`E1_P0_all_user_objects.csv`](evidence/E1/E1_P0_all_user_objects.csv) | All 1,204 user objects |
| [`E1_P0_all_user_object_columns.csv`](evidence/E1/E1_P0_all_user_object_columns.csv) | All 17,087 metadata rows |
| [`E1_global_structural_assurance_all_objects.csv`](evidence/E1/E1_global_structural_assurance_all_objects.csv) | Full 1,204-object classification |
| [`E1_global_structural_assurance_outside_550.csv`](evidence/E1/E1_global_structural_assurance_outside_550.csv) | All 654 objects outside the prior boundary |
| [`E1_global_structural_new_candidates.csv`](evidence/E1/E1_global_structural_new_candidates.csv) | Complete 33-candidate list and signatures |
| [`E1_global_structural_ambiguous.csv`](evidence/E1/E1_global_structural_ambiguous.csv) | Complete 23-object ambiguous list |
| [`E1_status_partial.csv`](evidence/E1/E1_status_partial.csv) | Machine-readable partial status |
| [`E1_P0_validation.csv`](evidence/E1/E1_P0_validation.csv) | P0 validation results |
| [`E1_33_new_candidate_detailed_classification.csv`](evidence/E1/E1_33_new_candidate_detailed_classification.csv) | Required per-object review of 33 |
| [`E1_33_owner_summary.csv`](evidence/E1/E1_33_owner_summary.csv) | Owner-level counts for 33 |
| [`E1_598_heuristic_audit_status.csv`](evidence/E1/E1_598_heuristic_audit_status.csv) | 598-object audit status |
| [`E1_23_ambiguous_detailed_classification.csv`](evidence/E1/E1_23_ambiguous_detailed_classification.csv) | Required per-object review of 23 |
| [`E1_expansion_3_detailed_classification.csv`](evidence/E1/E1_expansion_3_detailed_classification.csv) | Dependency expansion review |
| [`E1_boundary_data_presence_results.csv`](evidence/E1/E1_boundary_data_presence_results.csv) | Consolidated presence and row-count evidence |
| [`E1_boundary_liveness_results.csv`](evidence/E1/E1_boundary_liveness_results.csv) | Consolidated version/publication/target-date evidence |
| [`E1_boundary_dependency_relationships.csv`](evidence/E1/E1_boundary_dependency_relationships.csv) | Consolidated lineage and connectivity evidence |
| [`E1_provisional_metric_family_evidence.csv`](evidence/E1/E1_provisional_metric_family_evidence.csv) | Provisional family evidence |
| [`E1_final_candidate_boundary_1204.csv`](evidence/E1/E1_final_candidate_boundary_1204.csv) | Final decision for all 1,204 objects |
| [`E1_final_candidate_boundary_decision.csv`](evidence/E1/E1_final_candidate_boundary_decision.csv) | Final boundary counts |
| [`E1_boundary_qualification_validation.csv`](evidence/E1/E1_boundary_qualification_validation.csv) | Closure validation |

## E1 Validation

| Validation | Result |
|---|---|
| All user objects have complete signatures | PASS |
| Previous 550 reconciled | PASS |
| All 654 outside objects classified | PASS |
| All 33 candidates have signals and reasons | PASS |
| Stopping rule applied | PASS |
| Minimal business-value queries followed authorization | PASS |
| Database remained read-only | PASS |
| Durable evidence created as produced | PASS |
| 33 candidates reviewed | PASS |
| 598 heuristic audit completed | PASS |
| 23 ambiguous objects reviewed | PASS |
| Expansion guard respected | PASS |
| Final 1,204-object boundary unique and complete | PASS |
| Target dates not used as liveness | PASS |

## Governance

```text
Database read-only
No DB mutation
No production-code mutation
No Forecast Drift methodology change
No dashboard change
No governed CSV change
No Shiny change
No Docker/Azure change
No hypothesis promoted to fact
No overlapping row counts summed
No target date used as liveness
E2 not executed
```

## E1.CF - Final Carry-Forward Boundary Review

### Corrected dependency expansion guard

The resumed authorization corrected the guard so that previously classified
objects do not count as new merely because they reappear as dependencies.

| Measure | Result |
|---|---:|
| Total dependency objects | 29 |
| Previously classified | 29 |
| Prior classifications contradicted | 0 |
| Genuinely never reviewed | 0 |
| Corrected expansion count | 0 |

All 29 had already been classified in E0.1 or E1.P0. Dependency recurrence alone
did not contradict their prior role as support/infrastructure or outside active
Metric discovery. The corrected guard therefore allowed E1.CF to continue.

### Complete Dashboard9 vs vw_DAG_Metrics vs Hotspot_RCA comparison

No normalization or raw-value equivalence was applied. `HotspotRows` is retained
per supporting object to avoid summing overlapping objects.

| RawValue | Dashboard9 | DAG | Hotspot | HotspotRows | Hotspot min/max | DAG type | DAG related base measures | Preliminary interpretation |
|---|---|---|---|---|---|---|---|---|
| `CPU` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagAvgCPU; DagNumberOfServers; LogicalCores; Processor_FrequencyGHz; SkuGeneration | Dashboard display label; semantics unresolved |
| `CPU Basilisk` | NO | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagAvgCPU; DagNumberOfServers; DagType; LogicalCores; Processor_FrequencyGHz; SkuGeneration; SsdRopsRatio | DAG/Hotspot display label; not a new base family |
| `CPU Basilisk Failover` | NO | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand | CpuModel_DagLoadUtilizationHdd; DagNumberOfServers; DagType; LogicalCores; Processor_FrequencyGHz | Composite display label; not a new base family |
| `CPU Failover` | YES | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand | DagLoadUtilizationPercent; DagNumberOfServers; LogicalCores; Processor_FrequencyGHz | Dashboard display label; Scenario semantics unresolved |
| `CPU NonPhoenix` | NO | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagAvgCPU; DagNumberOfServers; DagPhoenixDBMaxStorageTB; DagType; GCyclesPerPhoenixTB; LogicalCores; Processor_FrequencyGHz; SkuGeneration; SsdRopsRatio | Composite display label; not a new base family |
| `CPU NonPhoenix Failover` | NO | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand | CpuModel_DagLoadUtilizationHdd; DagNumberOfServers; DagType; LogicalCores; Processor_FrequencyGHz | Composite display label; not a new base family |
| `CPU Phoenix` | NO | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagAvgCPU; DagNumberOfServers; DagPhoenixDBMaxStorageTB; DagType; GCyclesPerPhoenixTB; LogicalCores; Processor_FrequencyGHz; SkuGeneration; SsdRopsRatio | Composite display label; not a new base family |
| `CPU Phoenix Failover` | NO | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand | CpuModel_DagLoadUtilizationSsd; DagNumberOfServers; LogicalCores; Processor_FrequencyGHz | Composite display label; not a new base family |
| `CPU-NonPhoenix` | NO | NO | YES | DemandForecast=72838; SupplyForecast=81567 | 2025-09-02 / 2026-12-31 |  |  | Hotspot-only raw label/spelling; no equivalence asserted |
| `CPU-Phoenix` | NO | NO | YES | DemandForecast=72838; SupplyForecast=81567 | 2025-09-02 / 2026-12-31 |  |  | Hotspot-only raw label/spelling; no equivalence asserted |
| `HDD - Basilisk` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | BasiliskDbConsumedStorageTB; BasiliskDbMaxSellableStorageTB | Dashboard display label; DB Type semantics unresolved |
| `HDD - EDB` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | Basilisk/DAG/Phoenix consumer and enterprise storage measures; HddDBMaxStorageTB; SkuGeneration | Dashboard display label; DB Type semantics unresolved |
| `HDD - EDB Consumer` | NO | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand | Consumer mailbox/storage measures | Composite display label; not a new base family |
| `HDD - EDB Enterprise` | NO | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand | Enterprise mailbox/storage measures | Composite display label; not a new base family |
| `HDD-EDB` | NO | NO | YES | DemandForecast=72140; InorganicDemand=24320; SupplyForecast=81567 | 2025-09-01 / 2026-12-31 |  |  | Hotspot-only raw label/spelling; no equivalence asserted |
| `IOPS` | YES | YES | YES | DemandHistory=297238 | 2024-09-02 / 2026-06-23 | Demand, Supply | Dag_Avg_DBDisk_IOPS; DagMaxMountedDatabases; DBDisk_IOPS_Limit | Dashboard display label; semantics unresolved |
| `IOPS Failover` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand | Dag_Avg_DBDisk_LoadRatio; DagMaxMountedDatabases; DBDisk_IOPS_Limit | Dashboard display label; Scenario semantics unresolved |
| `Memory` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagAvgPercentAvailableBytes; DagNumberOfServers; SKU_PhysicalMemoryInGB | Dashboard display label |
| `SSD - MCDB` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | HddMcdbDemandSizeTB; HddMcdbMaxSizeTB | Dashboard display label; DB Type semantics unresolved |
| `SSD - Phoenix` | YES | YES | YES | DemandHistory=297238; SupplyHistory=297238; TotalSupplyDemand=102486 | 2024-09-02 / 2026-06-23 | Demand, Supply | DagPhoenixDBConsumedStorageTB; DagPhoenixDBMaxStorageTB | Dashboard display label; DB Type semantics unresolved |
| `SSD-MCDB` | NO | NO | YES | DemandForecast=72377; SupplyForecast=81567 | 2025-09-02 / 2026-12-31 |  |  | Hotspot-only raw label/spelling; no equivalence asserted |
| `SSD-PhoenixDB` | NO | NO | YES | DemandForecast=71916; SupplyForecast=81567 | 2025-09-02 / 2026-12-31 |  |  | Hotspot-only raw label/spelling; no equivalence asserted |

Explicit answers:

- DAG but not Dashboard9: `CPU Basilisk`, `CPU Basilisk Failover`,
  `CPU NonPhoenix`, `CPU NonPhoenix Failover`, `CPU Phoenix`,
  `CPU Phoenix Failover`, `HDD - EDB Consumer`, `HDD - EDB Enterprise`.
- Hotspot but not Dashboard9: the eight preceding values plus
  `CPU-NonPhoenix`, `CPU-Phoenix`, `HDD-EDB`, `SSD-MCDB`,
  `SSD-PhoenixDB`.
- ROPS in Dashboard9: **NO**.
- ROPS in `vw_DAG_Metrics`: **NO**.
- ROPS in Hotspot_RCA: **NO**.
- New base family beyond CPU/HDD/IOPS/SSD/Memory/ROPS from these three
  vocabularies: **NO**.
- Sue/Xinmei Excel comparison: **DEFER_TO_E10**; no unsupported absence claim
  was made.

The complete machine-readable table is
[`E1_CF_taxonomy_three_source_union.csv`](evidence/E1/E1_CF_taxonomy_three_source_union.csv).

### 140-object processing

The inherited population contains 97 tables and 43 views in 97 canonical
structural families. Every object received independent operational and taxonomy
conclusions.

| Measure | Count |
|---|---:|
| Carry-forward reviewed | 140 |
| NONEMPTY | 123 |
| EMPTY | 6 |
| UNRESOLVED presence | 11 |
| CURRENT | 0 |
| STALE | 0 |
| DORMANT_LEGACY_CANDIDATE | 6 |
| LIVENESS_UNCALIBRATED | 134 |
| Connected to confirmed forecast core | 7 |
| No directionally consistent dependency path | 133 |
| IN_E1_SCOPE | 2 |
| OUT_OF_E1_SCOPE | 29 |
| AMBIGUOUS_CARRY_FORWARD | 109 |
| Objects with `Metric` vocabulary | 0 |
| Objects with `MetricName` vocabulary | 3 |
| Objects with `Scenario`/`ScenarioId` vocabulary | 2 |
| Objects with `Granularity` vocabulary | 2 |

The 11 unresolved presence results are bounded TOP(1) timeouts on complex
views. They were not treated as empty, stale, or exclusion evidence.

Lineage was corrected to require a directionally consistent path:

```text
object -> upstream -> confirmed core
or
object -> downstream -> confirmed core
```

A path was not accepted if it changed direction around a shared table.

### Liveness results

Cadence was inferred only when at least three repeated publication/version
intervals existed and their central cadence was sufficiently stable. Target and
forecast-horizon dates were retained separately and never used for liveness.

| Object | Event column | Events / intervals | Median cadence | Last event | Elapsed | Missed cycles | Result |
|---|---|---:|---:|---|---:|---:|---|
| `Core_Prod_Forecast_Metric` | WriteTime | 5 / 4 | 31 days | 2023-10-06 | 1045.678 days | 32 | DORMANT_LEGACY_CANDIDATE |
| `CPG_DemandPlan_SubstrateBE_Supply_Region_V2` | CreatedDate | 91 / 90 | 1 day | 2024-08-22 | 724.386 days | 723 | DORMANT_LEGACY_CANDIDATE |
| `HumanIntervention_capsense_forecast_update_event_log` | execution_time | 339 / 338 | 0.003 day | 2022-01-04 | 1685.051 days | 584691 | DORMANT_LEGACY_CANDIDATE |
| `M365_MAU_Forecast_12M` | SnapshotDate | 122 / 121 | 7 days | 2024-07-03 | 774.678 days | 109 | DORMANT_LEGACY_CANDIDATE |
| `SubstrateBE_DagDecomPlanPrediction` | CreatedDate | 465 / 464 | 1 day | 2024-03-20 | 879.678 days | 878 | DORMANT_LEGACY_CANDIDATE |
| `Teams_WAU_Country_Forecast` | SnapshotDate | 10 / 9 | 14 days | 2021-10-30 | 1751.678 days | 124 | DORMANT_LEGACY_CANDIDATE |

No object was labeled STALE or DORMANT from a bare old date.

### Taxonomy findings from the 140

The complete raw values are preserved in
[`E1_CF_taxonomy_values_140_raw.csv`](evidence/E1/E1_CF_taxonomy_values_140_raw.csv).
Important observations:

- `MetricName=AllMAU` appears in M365 objects.
- `MetricName=AllWAU` appears in the Teams object.
- These are structurally proven collaboration-usage domain labels, not
  SubstrateBE capacity families. They are `SUPPORTING_ONLY`, not new AEGIS base
  Metric families.
- `Granularity` raw values include `Forest`, `Region`, `Environment`, and `Sku`.
  This is evidence for later granularity work, not a new Metric family.
- Two Semantic Fabric metadata tables preserve 59 raw ScenarioId rows across
  current and old copies. They are supporting non-SubstrateBE Scenario evidence.

Operational and taxonomy results remain independent. Three OUT objects preserve
cadence-supported historical taxonomy:

1. `CPG_DemandPlan_SubstrateBE_Supply_Region_V2`
2. `M365_MAU_Forecast_12M`
3. `Teams_WAU_Country_Forecast`

### Boundary update

| Population | Previous | After E1.CF |
|---|---:|---:|
| IN_E1_SCOPE | 419 | 421 |
| OUT_OF_E1_SCOPE | 640 | 669 |
| AMBIGUOUS_CARRY_FORWARD | 145 | 114 |
| Candidate boundary | 564 | 535 |

```text
Previous candidate boundary = 564
New candidate boundary = 535
Delta = -29
```

Delta explanation:

| Category | Count |
|---|---:|
| Removed: EMPTY + disconnected | 6 |
| Removed: dormant + disconnected | 6 |
| Removed: domain divergent + disconnected | 17 |
| Retained: active and core-connected | 2 |
| Retained: taxonomy evidence + unresolved operational status | 22 |
| Retained: insufficient exclusion/positive evidence | 87 |

All 29 OUT objects have at least two independent exclusion evidence types.
Unresolved objects remain visible; they were not forced OUT.

### Owner-level answers

1. Operationally relevant: **2**.
2. Clearly stale/dormant legacy: **6**.
3. Nonempty but disconnected: **121**.
4. OUT while preserving useful cadence-supported historical taxonomy: **3**.
5. Potentially active NEW SubstrateBE base Metric family: **NO**.
6. **PROVISIONAL - E1 NOT YET FINAL:** CPU, HDD, IOPS, SSD, Memory, ROPS.
   ROPS remains possible rather than vocabulary-confirmed because it has
   forecast-object evidence but is absent from Dashboard9, DAG labels, and
   Hotspot MetricName.

### Residual OPEN_QUESTION items

Residual uncertainty is carried forward without creating another boundary
sub-stage:

- 11 complex views have unresolved TOP(1) presence after bounded timeouts.
- 134 objects remain liveness-uncalibrated.
- 109 objects remain operationally ambiguous because fewer than two exclusion
  evidence types apply and active relevance is not proven.
- Metric vs Scenario vs DB Type semantics remain deferred to their authorized
  stages.
- ROPS vocabulary reconciliation remains open.

See [`E1_CF_open_questions.csv`](evidence/E1/E1_CF_open_questions.csv).

### E1.CF durable evidence

| Artifact | Purpose |
|---|---|
| [`E1_CF_taxonomy_three_source_union.csv`](evidence/E1/E1_CF_taxonomy_three_source_union.csv) | Complete 22-value Dashboard/DAG/Hotspot union |
| [`E1_CF_corrected_expansion_guard_summary.csv`](evidence/E1/E1_CF_corrected_expansion_guard_summary.csv) | Corrected guard count of zero |
| [`E1_CF_structural_families.csv`](evidence/E1/E1_CF_structural_families.csv) | 97 canonical structural families |
| [`E1_CF_object_classification.csv`](evidence/E1/E1_CF_object_classification.csv) | Full 140-object decisions |
| [`E1_CF_data_presence.csv`](evidence/E1/E1_CF_data_presence.csv) | Presence and row-count evidence |
| [`E1_CF_dependency_lineage.csv`](evidence/E1/E1_CF_dependency_lineage.csv) | Directed lineage and core connectivity |
| [`E1_CF_cadence_analysis.csv`](evidence/E1/E1_CF_cadence_analysis.csv) | Cadence and liveness evidence |
| [`E1_CF_taxonomy_values.csv`](evidence/E1/E1_CF_taxonomy_values.csv) | Combined raw taxonomy summary |
| [`E1_CF_metric_family_summary.csv`](evidence/E1/E1_CF_metric_family_summary.csv) | Active/historical/supporting family evidence |
| [`E1_CF_summary_140.csv`](evidence/E1/E1_CF_summary_140.csv) | Required 140-object summary |
| [`E1_CF_owner_answers.csv`](evidence/E1/E1_CF_owner_answers.csv) | Owner-level answers |
| [`E1_CF_final_boundary_1204.csv`](evidence/E1/E1_CF_final_boundary_1204.csv) | Recalculated complete population |
| [`E1_CF_final_boundary.csv`](evidence/E1/E1_CF_final_boundary.csv) | Final counts and delta |
| [`E1_CF_validation.csv`](evidence/E1/E1_CF_validation.csv) | Method validation |
| [`E1_CF_final_cross_validation.csv`](evidence/E1/E1_CF_final_cross_validation.csv) | Independent count/invariant checks |
| [`E1_CF_query_log.csv`](evidence/E1/E1_CF_query_log.csv) | 146 read-only query attempts |
| [`E1_CF_open_questions.csv`](evidence/E1/E1_CF_open_questions.csv) | Residual questions carried forward |

## Closure

```text
E0: CLOSED
E0.1: COMPLETE
E1.P0: COMPLETE
E1 CANDIDATE BOUNDARY QUALIFICATION: COMPLETE
E1.CF: COMPLETE
FINAL BOUNDARY-DISCOVERY CANDIDATE BOUNDARY: 535
PROVISIONAL BASE METRIC FAMILIES AT E1.CF CLOSE: CPU, HDD, IOPS, SSD, Memory, ROPS
E1.2-E1.4: SUBSEQUENTLY AUTHORIZED; SEE NEXT SECTION
E2: NOT EXECUTED
E1_CF_COMPLETE_AWAITING_AUTHORIZATION
```

## E1.2-E1.4 - Metric Universe Analysis

### Cost-governance state

The in-flight cost addendum arrived after substantial execution. The durable
ledger reconstructs:

```text
Executed SQL queries = 292
Authorized stage budget = 250
Budget delta = +42
Queries issued after correction = 0
```

See [`E1_query_budget_ledger.csv`](evidence/E1/E1_query_budget_ledger.csv).

| Priority section | State | Reason |
|---|---|---|
| Data behind 17 DAG labels | COMPLETE | All 27 MetricName/MetricType branches returned non-null data |
| Failover mechanism | COMPLETE | All 72 Scenario/ScenarioId sources profiled |
| ROPS | COMPLETE | All nine objects profiled |
| Segment axis | PARTIAL | Physical tables and critical CPU views covered; 43 duplicate/multi-layer views truncated |
| Basilisk / DB-Type-like evidence | COMPLETE | Data probes and Basilisk empty-view definitions captured |
| Metric / MetricName vocabularies | COMPLETE | 37 sources inventoried |
| Spelling collision map | COMPLETE | Five required collisions mapped |
| Counting contract | COMPLETE | Branch-specific version rules documented |

See
[`E1_section_completion_status.csv`](evidence/E1/E1_section_completion_status.csv).

### E1.2 - Data behind all 17 DAG labels

Every distinct DAG label is data backed:

```text
17 DATA_BACKED_ACTIVE
0 DEFINED_BUT_NO_DATA_FOUND
```

For every label:

- each MetricName/MetricType branch returned a non-null MetricValue;
- `Hotspot_RCA_DemandHistory` independently contains exactly 297,238 rows;
- the Hotspot count is reported as one canonical object and is not added to
  DAG or downstream-view rows;
- `vw_DAG_Metrics.UpdateTime` has 1,822 events through 2026-08-16 and is
  CURRENT.

Evidence:
[`E1_2_DAG_label_data_evidence.csv`](evidence/E1/E1_2_DAG_label_data_evidence.csv).

#### Six CPU combinations not visible in Dashboard9

| Combination | Data/forecast result | Classification |
|---|---|---|
| CPU Phoenix | DAG/Hotspot plus CPU by-DB rows through 2026-04-01 | DATA_BACKED_NOT_DASHBOARD_REACHABLE |
| CPU Phoenix Failover | Physical `DBType=Phoenix`, `Scenario=Failover` rows | DATA_BACKED_NOT_DASHBOARD_REACHABLE |
| CPU NonPhoenix | DAG/Hotspot plus CPU by-DB rows through 2026-04-01 | DATA_BACKED_NOT_DASHBOARD_REACHABLE |
| CPU NonPhoenix Failover | Physical `DBType=NonPhoenix`, `Scenario=Failover` rows | DATA_BACKED_NOT_DASHBOARD_REACHABLE |
| CPU Basilisk | 297,238 canonical rows; serving views explicitly `WHERE 1=0` | DATA_BACKED_NOT_DASHBOARD_REACHABLE; FORECAST_VIEW_EMPTY |
| CPU Basilisk Failover | 297,238 canonical rows; serving views explicitly `WHERE 1=0` | DATA_BACKED_NOT_DASHBOARD_REACHABLE; FORECAST_VIEW_EMPTY |

The overall conclusion is `REAL_COVERAGE_GAP` because the four Phoenix and
NonPhoenix forecast combinations are populated but absent from Dashboard9.
Basilisk is data backed at the DAG/actual layer, but its forecast-serving views
are empty; its Forecast Accuracy issue is therefore actual/label-only.

### E1.3 - Scenario and Failover

The 535-object boundary contains:

```text
67 Scenario columns
5 ScenarioId columns
72 physical Scenario/ScenarioId sources
```

CPU and IOPS use parallel mechanisms:

1. physical `Scenario='Failover'` in forecast objects;
2. `CPU_type='failover'` / `IOPS_type='failover'` in base outputs;
3. hardcoded DAG MetricName and dashboard Resource labels.

Results:

```text
CPU + Scenario=Failover -> CPU Failover = CONFIRMED
IOPS + Scenario=Failover -> IOPS Failover = CONFIRMED
Dual modeling = YES
```

`CPU Failover` and `IOPS Failover` are Scenario-driven/composite labels, not
separate base Metrics.

Evidence:

- [`E1_3_scenario_sources.csv`](evidence/E1/E1_3_scenario_sources.csv)
- [`E1_3_raw_scenario_values.csv`](evidence/E1/E1_3_raw_scenario_values.csv)
- [`E1_3_failover_evidence.csv`](evidence/E1/E1_3_failover_evidence.csv)

### Segment evidence

No physical Segment/TenantSegment column carries Consumer, Enterprise, or
Greenland.

- Physical `Workload` exists, but observed values such as `BE`, `Backend`,
  `Enterprise`, `EDU`, `SMC - Corporate`, `SMC - SMB`, `Unknown`, and NULL do
  not implement the Consumer/Enterprise/Greenland split.
- Consumer and Enterprise are separate `demandplan_be_demand` measures and DAG
  label constants.
- Greenland has non-null forecast and telemetry measures but no demonstrated
  row-level membership in the same physical axis.

Owner classification:

```text
SEGMENT_CONCEPT_CONFIRMED_BUT_NOT_PHYSICAL_COLUMN
```

The strongest applicability evidence is HDD/EDB. Greenland is a supported
parallel-segment hypothesis. The master tree was not changed.

The section is PARTIAL because 43 duplicate/multi-layer Workload views were not
reprofiled after budget exhaustion. This is carried as `OPEN_QUESTION_E3`.

Evidence:
[`E1_3_segment_axis_evidence.csv`](evidence/E1/E1_3_segment_axis_evidence.csv).

### Observed DB-Type-like evidence

| Base Metric | Observed DB-Type-like evidence |
|---|---|
| CPU | Phoenix, NonPhoenix, Basilisk |
| HDD | EDB, Basilisk |
| SSD | MCDB, Phoenix |

CPU Phoenix and NonPhoenix have physical DBType rows. CPU Basilisk is backed by
DAG/Hotspot actual data, while all four Basilisk forecast-serving views are
explicitly empty.

These are observed E1 values only. DB Type completeness and the final matrix
remain gated to E2/E3.

Evidence:
[`E1_3_observed_dbtype_evidence.csv`](evidence/E1/E1_3_observed_dbtype_evidence.csv).

### E1.4 - ROPS

| Object/role | Evidence |
|---|---|
| `forecast_substrateBE_rops` | 1,473,360 rows; 1,473,360 non-null forecasts |
| `SubstrateBE_M2CP_Rops_Smooth` | 7,339,928 rows; one write event, liveness uncalibrated |
| ROPS Demand | 217,170 rows |
| ROPS Forecast with Perturbation | 0 rows |
| Three ROPS limit views | 0 rows |
| ROPS Telemetry | 8,304,196 rows; 332 events through 2026-08-17; CURRENT |
| ROPS TimeSeries | 1,200,171 rows |

The ROPS forecast table is structurally analogous to CPU and IOPS and has
directed lineage into the currently empty serving view. No explicit registry
Metric/MetricName value exposes ROPS.

Final ROPS classification:

```text
SUPPORTED_ACTIVE_BASE_METRIC_NOT_EXPOSED_IN_DASHBOARD
```

Formal universe status: `SUPPORTED_ACTIVE_BASE_METRIC`.

Evidence:
[`E1_4_ROPS_analysis.csv`](evidence/E1/E1_4_ROPS_analysis.csv).

### Explicit Metric and MetricName vocabularies

Final structural result:

```text
Metric objects = 5
MetricName objects = 32
Total explicit sources = 37
Metric vs MetricName = PARTIAL_OVERLAP
```

The prior approximate 3/16 count was incomplete.

Three active explicit Metrics were discovered in
`SubstrateBE_ASCStamp_Forecast`:

| Raw Metric | Rows | Versions | Latest |
|---|---:|---:|---|
| `P95ItemsPerShard` | 34,127,248 | 35 | 2026-08-15 |
| `P95ShardCpuUtil` | 34,126,940 | 35 | 2026-08-15 |
| `P95ShardSizeInGb` | 34,126,860 | 35 | 2026-08-15 |

Active registry evidence also proves:

```text
MetricName=AD
Unit=Dit
Granularity=Forest
7,125,425 demand rows
7 publications
CurrentForecastPointer promoted 2026-07-29
```

`ASCStamp` is the producer/registry branch containing the three P95 Metrics,
not a base Metric itself. `MCDB_ForestSKU` and `MCDB_Region` are pipeline branch
identifiers.

Evidence:

- [`E1_2_metric_source_inventory.csv`](evidence/E1/E1_2_metric_source_inventory.csv)
- [`E1_2_raw_metric_values.csv`](evidence/E1/E1_2_raw_metric_values.csv)
- [`E1_2_raw_to_base_metric_mapping.csv`](evidence/E1/E1_2_raw_to_base_metric_mapping.csv)
- [`E1_2_metric_vs_metricname_comparison.csv`](evidence/E1/E1_2_metric_vs_metricname_comparison.csv)

### Evidence-supported base Metric universe

Ten active base Metric families are supported:

| Base Metric | E1 status | Dashboard9 |
|---|---|---|
| CPU | CONFIRMED_ACTIVE_BASE_METRIC | YES |
| HDD | CONFIRMED_ACTIVE_BASE_METRIC | YES |
| IOPS | CONFIRMED_ACTIVE_BASE_METRIC | YES |
| SSD | CONFIRMED_ACTIVE_BASE_METRIC | YES |
| Memory | CONFIRMED_ACTIVE_BASE_METRIC | YES |
| ROPS | SUPPORTED_ACTIVE_BASE_METRIC | NO |
| AD | CONFIRMED_ACTIVE_BASE_METRIC | NO |
| P95ItemsPerShard | CONFIRMED_ACTIVE_BASE_METRIC | NO |
| P95ShardCpuUtil | CONFIRMED_ACTIVE_BASE_METRIC | NO |
| P95ShardSizeInGb | CONFIRMED_ACTIVE_BASE_METRIC | NO |

Evidence:
[`E1_final_metric_universe.csv`](evidence/E1/E1_final_metric_universe.csv).

### Dashboard coverage gaps

Thirteen data-backed combinations/base Metrics are not reachable through the
observed dashboard nine:

1. CPU Phoenix
2. CPU Phoenix Failover
3. CPU NonPhoenix
4. CPU NonPhoenix Failover
5. CPU Basilisk
6. CPU Basilisk Failover
7. HDD - EDB Consumer
8. HDD - EDB Enterprise
9. ROPS
10. AD
11. P95ItemsPerShard
12. P95ShardCpuUtil
13. P95ShardSizeInGb

Evidence:
[`E1_final_dashboard_coverage_gap.csv`](evidence/E1/E1_final_dashboard_coverage_gap.csv).

### Spelling collisions

The five required collisions are preserved in
[`E1_spelling_collision_map.csv`](evidence/E1/E1_spelling_collision_map.csv).

`SSD - Phoenix` versus `SSD-PhoenixDB` is
`CONFIRMED_SAME_CONCEPT` because the DAG label is computed directly from
PhoenixDB measures.

```text
Divergent spellings can break exact-string joins, slicers, filtering and
coverage reconciliation.
```

No raw value was normalized in evidence.

### Counting contract for E2-E8

- DAG/Memory: `UpdateTime`
- CPU by-DB and ASCStamp: `ForecastVersion`
- CPU/IOPS base outputs: `forecastdate` is the producer marker; `DataDate`
  remains target
- HDD: `write_time` and `execution_time` are not automatically interchangeable
- AD: `ForecastRunId` + `PublishSeq` + `ValidFromUtc`
- ROPS forecast: `VERSION_UNRESOLVED`; telemetry UpdateTime proves only
  supporting currentness

Required later measures:

```text
RowsTotal
RowsLatestComparableVersion
DistinctForecastVersions
DistinctKeys
```

Evidence:
[`E1_counting_contract_E2_E8.csv`](evidence/E1/E1_counting_contract_E2_E8.csv).

### Open questions

- `OPEN_QUESTION_E2`: complete DB Type universe and cross-family comparability.
- `OPEN_QUESTION_FUTURE_EXPANSION`: owner Segment decision beyond the accepted
  partial conclusion.
- `OPEN_QUESTION_E3`: CPU Basilisk forecast semantics.
- `OPEN_QUESTION_E3` (LOW PRIORITY): optional reconciliation of the 43 duplicate
  Workload views. Not required; profiling them cannot change the established
  conclusion.
- `OPEN_QUESTION_E10`: spelling and Sue/Xinmei Excel reconciliation.

See [`E1_final_open_questions.csv`](evidence/E1/E1_final_open_questions.csv).

### Validation and analytical result

All analytical correctness checks and priorities 1-3 pass.

Evidence:

- [`E1_final_validation.csv`](evidence/E1/E1_final_validation.csv)
- [`E1_final_cross_validation.csv`](evidence/E1/E1_final_cross_validation.csv)

Two governance conditions were open at the end of analysis and are resolved by
owner decision in the closure section below:

```text
Stage query budget <=250: 292 executed -> WAIVED_BY_OWNER
Segment section complete: PARTIAL -> PARTIAL_ACCEPTED
```

E2 and E3 were not started.

## E1 Formal Closure - Owner Scope Decision

### Purpose of E1

Identify and evidence the Metric universe relevant to the current product.

### E1 purpose versus E1 scope

E1 discovered every evidence-supported active Metric family in
`TesseractEarthDW`. The owner then made an explicit product-scope decision
separating what exists in the warehouse from what the current MVP implements.
Both facts are preserved; neither replaces the other.

### 1. Final MVP base Metric universe

```text
CURRENT_MVP_BASE_METRIC_COUNT = 5

CURRENT_MVP_BASE_METRICS =
CPU
HDD
IOPS
SSD
Memory
```

| Base Metric | MVP status |
|---|---|
| CPU | IN_CURRENT_MVP |
| HDD | IN_CURRENT_MVP |
| IOPS | IN_CURRENT_MVP |
| SSD | IN_CURRENT_MVP |
| Memory | IN_CURRENT_MVP |

These five are the formal E1 output for the current Forecasting, Forecast Drift
and Grafana implementation scope.

### 2. Operational site labels

```text
CURRENT_MVP_OPERATIONAL_LABEL_COUNT = 9
```

| # | Operational label | Base Metric | Distinguishing semantics |
|---:|---|---|---|
| 1 | `HDD - Basilisk` | HDD | DB-Type-like: Basilisk |
| 2 | `HDD - EDB` | HDD | DB-Type-like: EDB |
| 3 | `CPU` | CPU | Base scenario |
| 4 | `CPU Failover` | CPU | Scenario = Failover |
| 5 | `IOPS` | IOPS | Base scenario |
| 6 | `IOPS Failover` | IOPS | Scenario = Failover |
| 7 | `SSD - Phoenix` | SSD | DB-Type-like: Phoenix |
| 8 | `SSD - MCDB` | SSD | DB-Type-like: MCDB |
| 9 | `Memory` | Memory | No DB-Type or Scenario split observed |

Critical reading rule:

```text
9 operational labels != 9 base Metrics
```

Established decomposition evidence:

```text
CPU Failover  = CPU  + Scenario Failover
IOPS Failover = IOPS + Scenario Failover
```

`HDD - Basilisk` / `HDD - EDB` and `SSD - Phoenix` / `SSD - MCDB` carry
DB-Type-like semantics that the operational catalog will consume directly. E1 is
not reopened to prove these semantics further.

### 3. Valid discoveries deferred from the current MVP

The following five families were discovered with evidence during E1. They are
**not** false positives and must not be deleted from the record.

| Family | E1 evidence status | Product scope | Discovery scope for E2-E10 |
|---|---|---|---|
| ROPS | SUPPORTED_ACTIVE_BASE_METRIC | DEFERRED_OUT_OF_CURRENT_MVP_PRODUCT_SCOPE | IN_DISCOVERY_SCOPE |
| AD | CONFIRMED_ACTIVE_BASE_METRIC | DEFERRED_OUT_OF_CURRENT_MVP_PRODUCT_SCOPE | IN_DISCOVERY_SCOPE |
| P95ItemsPerShard | CONFIRMED_ACTIVE_BASE_METRIC | DEFERRED_OUT_OF_CURRENT_MVP_PRODUCT_SCOPE | IN_DISCOVERY_SCOPE |
| P95ShardCpuUtil | CONFIRMED_ACTIVE_BASE_METRIC | DEFERRED_OUT_OF_CURRENT_MVP_PRODUCT_SCOPE | IN_DISCOVERY_SCOPE |
| P95ShardSizeInGb | CONFIRMED_ACTIVE_BASE_METRIC | DEFERRED_OUT_OF_CURRENT_MVP_PRODUCT_SCOPE | IN_DISCOVERY_SCOPE |

Reason for deferral: they are evidence-supported active or internal forecast
families discovered during E1, but they are not required for the current product
implementation scope.

Deferral is a **product** decision only. All five remain fully in scope for E2
through E10 axis discovery. Their DB Type, Granularity, Region and Key values
must be discovered like any other data-evidenced family.

### 4. CPU coverage-gap discoveries preserved

These six combinations remain recorded as coverage evidence. They are **not**
new base Metrics.

| Combination | Preserved finding |
|---|---|
| CPU Phoenix | Data-backed combination |
| CPU Phoenix Failover | Data-backed combination |
| CPU NonPhoenix | Data-backed combination |
| CPU NonPhoenix Failover | Data-backed combination |
| CPU Basilisk | Taxonomy/data-backed; current serving forecast view is explicitly `WHERE 1=0` |
| CPU Basilisk Failover | Taxonomy/data-backed; current serving forecast view is explicitly `WHERE 1=0` |

These findings remain important for Forecasting and Forecast Drift coverage
analysis.

### 5. Segment decision

```text
SEGMENT_STATUS = PARTIAL_ACCEPTED
SEGMENT_CONCEPT_CONFIRMED_BUT_NOT_PHYSICAL_COLUMN
```

The owner accepts the limitation. The 43 duplicate/multi-layer Workload views
were not profiled and will not be profiled, because the physical `Workload`
column carries `BE`, `Backend`, `Enterprise`, `EDU`, `SMC - Corporate` and
`SMC - SMB`, which is not the Consumer/Enterprise/Greenland concept. Consumer
and Enterprise are separate measure columns, not row values of a dimension, so
further view profiling cannot change the conclusion.

Consumer and Enterprise evidence remains documented. Greenland remains
supporting/unresolved evidence. This does not block closure and is carried
forward as `OPEN_QUESTION_FUTURE_EXPANSION`.

### 6. Query-budget waiver

```text
Reconstructed executions = 292
Later-established budget = 250
QUERY_BUDGET_OVERAGE = WAIVED_BY_OWNER
```

The cost-discipline addendum arrived after those queries had already executed.
The waiver applies only to E1. Future stages must obey their budget from the
beginning. No query was issued as part of this closure.

### 7. RM-E1-CLOSED roadmap marker

```text
RM-E1-CLOSED
Date: 2026-08-16
Status: CLOSED_BY_OWNER_SCOPE_DECISION
Base Metrics: 5
Operational Labels: 9
Deferred Active Families: 5
Segment: PARTIAL_ACCEPTED
Query Budget Overage: WAIVED_BY_OWNER
Additional SQL Queries During Closure: 0
```

This RM point is the durable baseline from which the next operational catalog
work begins. No future stage may silently change the five-Metric MVP scope
without explicit owner authorization.

### 8. Next work

#### Preliminary combination evidence, not the final catalog

The six preserved CPU coverage-gap combinations **will be included as rows** in
the Operational Master Table.

```text
9 observed site labels
+ 6 additional CPU combinations already discovered
= 15 preliminary rows

ARTIFACT_CLASS = E1_PRELIMINARY_COMBINATION_EVIDENCE
```

These 15 rows are **not** the final catalog and do **not** constrain E2-E10
discovery. They are what E1 happened to observe. E2 through E10 must still
discover every valid filter value and combination for the five approved Base
Metrics.

For the six additional CPU combinations:

```text
ReachableFromDashboard = NO
```

Their inclusion does **not** expand the Base Metric universe. They remain
combinations of the Base Metric CPU and are included because they are
operationally relevant to Forecasting and Forecast Drift coverage.

```text
CURRENT_MVP_BASE_METRIC_COUNT = 5    (product-scope annotation)
E1_PRELIMINARY_COMBINATION_ROWS = 15 (preliminary evidence, not a limit)
```

The preliminary rows do not overlap: `CPU` and `CPU Failover` are the dashboard-
reachable labels, while the six additions are DB-Type-qualified CPU
combinations.

| # | Preliminary row | Base Metric | ReachableFromDashboard |
|---:|---|---|---|
| 1 | `HDD - Basilisk` | HDD | YES |
| 2 | `HDD - EDB` | HDD | YES |
| 3 | `CPU` | CPU | YES |
| 4 | `CPU Failover` | CPU | YES |
| 5 | `IOPS` | IOPS | YES |
| 6 | `IOPS Failover` | IOPS | YES |
| 7 | `SSD - Phoenix` | SSD | YES |
| 8 | `SSD - MCDB` | SSD | YES |
| 9 | `Memory` | Memory | YES |
| 10 | `CPU Phoenix` | CPU | NO |
| 11 | `CPU Phoenix Failover` | CPU | NO |
| 12 | `CPU NonPhoenix` | CPU | NO |
| 13 | `CPU NonPhoenix Failover` | CPU | NO |
| 14 | `CPU Basilisk` | CPU | NO |
| 15 | `CPU Basilisk Failover` | CPU | NO |

Known caveat carried forward: the `CPU Basilisk` and `CPU Basilisk Failover`
serving forecast views are explicitly `WHERE 1=0`, so those two rows are
expected to resolve with an empty forecast branch. This is a recorded property,
not a defect to rediscover.

Authorization boundary:

```text
NO ADDITIONAL METRIC-FAMILY DISCOVERY IS AUTHORIZED.
DIMENSION/FILTER DISCOVERY FOR THE FIVE APPROVED METRICS
CONTINUES THROUGH E2-E10.
```

Evidence:
[`E1_master_table_scope.csv`](evidence/E1/E1_master_table_scope.csv).

#### Fields to resolve

```text
NEXT:
Discover the complete set of valid values and combinations for the five
approved Base Metrics across:

DB Type
Scenario
Granularity
Region
Key
Canonical Source
Version
```

The final table is expected to contain more than 15 rows. No new Metric family
will be introduced, and no universal `TesseractEarthDW` rescan will be reopened.

### 9. Closure validation

| Check | Result |
|---|---|
| No new SQL queries executed | PASS |
| Five MVP base Metrics documented | PASS |
| Nine operational labels documented | PASS |
| ROPS/AD/P95 preserved as deferred discoveries | PASS |
| Six CPU coverage-gap combinations preserved | PASS |
| Segment marked PARTIAL_ACCEPTED | PASS |
| Budget overage marked WAIVED_BY_OWNER | PASS |
| Master document updated | PASS |
| README updated | PASS |
| RM-E1-CLOSED created | PASS |
| E2 or other discovery stage not started | PASS |

Closure evidence:

- [`E1_closure_decision.csv`](evidence/E1/E1_closure_decision.csv)
- [`E1_mvp_metric_universe.csv`](evidence/E1/E1_mvp_metric_universe.csv)
- [`E1_mvp_operational_labels.csv`](evidence/E1/E1_mvp_operational_labels.csv)
- [`E1_deferred_families.csv`](evidence/E1/E1_deferred_families.csv)
- [`E1_closure_validation.csv`](evidence/E1/E1_closure_validation.csv)
- [`RM_E1_CLOSED.md`](RM_E1_CLOSED.md)

```text
E1_CLOSED_BY_OWNER_SCOPE_DECISION
RM_E1_CLOSED
READY_FOR_E2_DBTYPE_UNIVERSE
```


## E2 - DB Type Universe

### Purpose

Answer one question: what DB Type values actually exist for the five approved
Base Metrics?

E1 stayed closed. No Metric family was added. No object rescan or dependency
expansion was performed. The E1 boundary, column inventory and row counts were
read locally before any query was issued.

```text
SQL executions: 28 / 30
Timeout: 90 s
Fallbacks needed: 0
Failed queries: 1 (invalid column name, corrected on a different object)
```

Ledger: [`E2_query_ledger.csv`](evidence/E2/E2_query_ledger.csv).

### Canonical DB Type universe

```text
CANONICAL_DBTYPE_COUNT = 5

Phoenix
NonPhoenix
EDB
Basilisk
MCDB
```

| Canonical DB Type | Metric families | Strongest evidence |
|---|---|---|
| Phoenix | CPU, SSD | `DBType='Phoenix'`; `Resource='SSD-PhoenixDB'` |
| NonPhoenix | CPU | `DBType='NonPhoenix'` |
| EDB | HDD | `MetricName` prefix `HDD-EDB-*` |
| Basilisk | HDD, CPU | `MetricName='HDD-EDB-Basilisk'`; CPU label only |
| MCDB | SSD | `Resource='SSD-MCDB'` |

Full universe:
[`E2_DBType_Universe.csv`](evidence/E2/E2_DBType_Universe.csv).

### How DB Type is physically encoded

DB Type is not modelled the same way across metrics. This matters for every
later join.

| Base Metric | Encoding mechanism | Column |
|---|---|---|
| CPU | Dedicated physical dimension column | `DBType` |
| HDD | Embedded in the metric label | `MetricName` |
| SSD | Embedded in the resource label plus object naming | `Resource` |
| IOPS | None observed | - |
| Memory | None observed | - |

### Evidence by metric

#### CPU

```text
DBType = Phoenix     forest 23,318,632 | region 2,825,340
DBType = NonPhoenix  forest 20,937,897 | region 3,396,484
```

The DBType column contains exactly two values. Crossed with Scenario it forms a
complete 2x2:

```text
Phoenix    | Consumed  1,601,026
Phoenix    | Failover  1,224,314
NonPhoenix | Consumed  1,804,572
NonPhoenix | Failover  1,591,912
```

`CPU Basilisk` has **no** physical DBType row. It exists only as a DAG/Hotspot
label whose serving views are explicitly `WHERE 1=0`. Classification:
`LABEL_ONLY_DBTYPE_EVIDENCE`.

#### HDD

```text
MetricName = HDD-EDB-Consumer    forest 26,912,021 | region 5,167,235
MetricName = HDD-EDB-Enterprise  forest 26,759,853 | region 5,239,184
MetricName = HDD-EDB-Basilisk    forest    246,915 | region    74,162
```

This is the most consequential E2 finding. The site presents `HDD - EDB` and
`HDD - Basilisk` as peers, but physically **Basilisk is nested inside the EDB
forecast object**. Consumer and Enterprise are Segment, not DB Type, and remain
an E3 question.

Both `vw_SubstrateBE_Demand_HddBasilisk_Forest` and `_Region` return **0 rows**,
so the `HDD - Basilisk` site label has no populated serving view even though
321,077 physical Basilisk rows exist.

#### SSD

```text
Resource = SSD-MCDB       region    541,700 | forestSKU 1,234,534 | demandforecast 2,989,717
Resource = SSD-PhoenixDB  region    426,246 | forest    1,614,543
Resource = SSD-Phoenix    inorganic   591,384
Resource = SSD            region    533,141  (unqualified, coexists with SSD-MCDB)
```

#### IOPS and Memory

```text
IOPS:   DBTYPE_NOT_OBSERVED
Memory: DBTYPE_NOT_OBSERVED
```

No DB-type-like column exists in any in-scope IOPS or Memory object. IOPS
`MetricName` values are `IOPS-Consumed` and `IOPS-Failover`, which are Scenario,
not DB Type. The Memory label is unqualified.

No DB Type was invented to make the metrics structurally symmetrical.

Detail:
[`E2_DBType_ByMetric_Evidence.csv`](evidence/E2/E2_DBType_ByMetric_Evidence.csv)
and
[`E2_applicability_by_metric.csv`](evidence/E2/E2_applicability_by_metric.csv).

### Candidates ruled out

Several columns look like DB Type and are not. Recording them prevents the same
false lead being re-investigated later.

| Candidate | Observed values | Verdict |
|---|---|---|
| `DagType` | NULL in 100% of rows in all four DemandForecast objects | Not a DB Type source |
| `type` | `actual`, `ARIMA`, `ExponentialSmoothing`, `FixedGrowth1%..5%` and ensembles | Forecasting model |
| `Type` | `Organic` | Demand nature |
| `ValueType` | `Forecast-Mean` | Value role |
| `data_type` | `Consumer`, `Enterprise` | Segment, carried to E3 |
| `ResourceType` / `ResouceType` | `HDD`, `SSD`, `CPU`, `IOPS` | Metric name |
| `HddDatabaseType` | `Cold`, `Default` | Storage tier, different concept |

`ResouceType` is a misspelled column name in the CPU and IOPS accuracy views;
the HDD and SSD views spell it `ResourceType`.

Evidence:
[`E2_negative_findings.csv`](evidence/E2/E2_negative_findings.csv).

### Aliases and spelling variants

Eight alias pairs are recorded verbatim without normalization, including the
newly discovered third SSD Phoenix spelling.

```text
SSD - Phoenix   vs SSD-PhoenixDB     CONFIRMED_SAME_CONCEPT
SSD-PhoenixDB   vs SSD-Phoenix       SUPPORTED_SAME_CONCEPT   (new in E2)
SSD - MCDB      vs SSD-MCDB          CONFIRMED_SAME_CONCEPT
HDD - EDB       vs HDD-EDB           SUPPORTED_SAME_CONCEPT
HDD - Basilisk  vs HDD-EDB-Basilisk  SUPPORTED_SAME_CONCEPT
CPU Phoenix     vs CPU-Phoenix       SUPPORTED_SAME_CONCEPT
CPU NonPhoenix  vs CPU-NonPhoenix    SUPPORTED_SAME_CONCEPT
ResourceType    vs ResouceType       CONFIRMED_SAME_CONCEPT   (column name)
```

Evidence:
[`E2_alias_collision_map.csv`](evidence/E2/E2_alias_collision_map.csv).

### Direct owner answers

**A. Canonical DB Type values supported:** 5.

**B. Every canonical DB Type:** Phoenix, NonPhoenix, EDB, Basilisk, MCDB.

**C. Raw aliases and spelling variants, listed separately:**
`Phoenix`, `NonPhoenix`, `CPU Phoenix`, `CPU-Phoenix`, `CPU NonPhoenix`,
`CPU-NonPhoenix`, `CPU Basilisk`, `HDD-EDB-Consumer`, `HDD-EDB-Enterprise`,
`HDD-EDB-Basilisk`, `HDD - EDB`, `HDD-EDB`, `HDD - Basilisk`, `SSD-MCDB`,
`SSD - MCDB`, `SSD-PhoenixDB`, `SSD-Phoenix`, `SSD - Phoenix`.

**D. Observed with CPU:** Phoenix and NonPhoenix physically; Basilisk label-only.

**E. Observed with HDD:** EDB and Basilisk, both physical, with Basilisk nested
inside EDB.

**F. Observed with SSD:** MCDB and Phoenix.

**G. Does IOPS have DB Type?** No. `DBTYPE_NOT_OBSERVED`.

**H. Does Memory have DB Type?** No. `DBTYPE_NOT_OBSERVED`.

**I. DB Types not previously visible in the nine site labels?** Yes:

1. `NonPhoenix` - a physical CPU DB Type with 24.3M rows, absent from the site.
2. `HDD-EDB-Basilisk` - proves Basilisk is physically a child of EDB, not a peer.
3. `SSD-Phoenix` - a third spelling not previously mapped.
4. The unqualified `SSD` Resource value coexisting with `SSD-MCDB` inside the
   same object, which remains unresolved.

Answers:
[`E2_owner_answers.csv`](evidence/E2/E2_owner_answers.csv).

### Open questions carried to E3

- `OPEN_QUESTION_E3`: is the unqualified `SSD` Resource value a total, a
  default DB Type, or an unlabelled slice?
- `OPEN_QUESTION_E3`: is CPU `Phoenix` the same engine concept as SSD
  `PhoenixDB`? Currently SUPPORTED, not CONFIRMED.
- `OPEN_QUESTION_E3`: should `NonPhoenix` be treated as a DB Type or as the
  complement of Phoenix?
- `OPEN_QUESTION_E3`: HDD Basilisk and Memory serving views return 0 rows while
  data exists upstream.
- `OPEN_QUESTION_E3`: Consumer and Enterprise remain Segment, not DB Type.

### Validation

All thirteen checks pass, including 28/30 queries, no rescan, no dependency
expansion, and explicit IOPS and Memory answers.

Evidence: [`E2_validation.csv`](evidence/E2/E2_validation.csv).

### RM-E2-CLOSED

```text
RM-E2-CLOSED
Date: 2026-08-16
Canonical DB Type count: 5
Canonical values: Phoenix, NonPhoenix, EDB, Basilisk, MCDB
Raw aliases recorded: 18
Applicable metrics: CPU, HDD, SSD
Not observed: IOPS, Memory
Query budget used: 28 / 30
Open questions: 5 (all E3)
Next stage: E3 Metric x DB Type
```

RM-E1-CLOSED is unchanged.

```text
E2_COMPLETE_AWAITING_AUTHORIZATION
```


## E3 - Metric x DB Type

### Purpose

For each metric, which DB Types does it actually have, and which does it not?

E3 organizes evidence E2 already produced and resolves what E2 left open. It is
not a discovery stage. No boundary work, no new objects, no sub-stage.

```text
SQL executions: 4 / 30
Counts reused from E1/E2 rather than recomputed
```

### The matrix

Routing states are kept separate from the five canonical DB Types. `NOT_FILTERED`
and `NOT_APPLICABLE` are structural states, not DB Type values.

| Base Metric | Phoenix | NonPhoenix | EDB | Basilisk | MCDB | Routing state |
|---|---|---|---|---|---|---|
| CPU | PHYSICAL_CONFIRMED | PHYSICAL_CONFIRMED | NOT_OBSERVED | LABEL_ONLY | NOT_OBSERVED | NOT_FILTERED |
| HDD | NOT_OBSERVED | NOT_OBSERVED | PHYSICAL_CONFIRMED | PHYSICAL_CONFIRMED | NOT_OBSERVED | NOT_FILTERED |
| SSD | PHYSICAL_CONFIRMED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | PHYSICAL_CONFIRMED | NOT_FILTERED |
| IOPS | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_APPLICABLE |
| Memory | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_OBSERVED | NOT_APPLICABLE |

39 fully classified cells with row counts, encoding and reason:
[`E3_metric_dbtype_matrix.csv`](evidence/E3/E3_metric_dbtype_matrix.csv).

### Which metrics have an evidenced DB Type axis

| Base Metric | Axis | Encoding | Confirmed DB Types |
|---|---|---|---|
| CPU | YES | Physical `DBType` column | Phoenix, NonPhoenix |
| HDD | YES | Embedded in `MetricName` | EDB, Basilisk |
| SSD | YES | Embedded in `Resource` and object naming | MCDB, Phoenix |
| IOPS | NO | - | - |
| Memory | NO | - | - |

The scope statement matters:

```text
IOPS   NOT_OBSERVED in evidenced scope, independently corroborated as N/A by the Excel
Memory NOT_OBSERVED in evidenced scope, with no external corroboration
```

Neither is a claim of universal non-existence. Nothing outside the evidenced
boundary was tested.

Detail:
[`E3_applicability_by_metric.csv`](evidence/E3/E3_applicability_by_metric.csv).

### The five E2 questions, resolved

**2.1 Is `Total` a stored value or an absence of filter?**
`SEPARATE_OBJECT`. `vw_SubstrateBE_CPU_Total_Forecast_Region` reads
`forecast_substrateBE_cpu_region`, an object with **no** `DBType` column, using no
DB Type predicate. The `DBType` column itself contains only `Phoenix` and
`NonPhoenix`, so `Total` is never stored anywhere.

**2.2 Is Basilisk a peer of EDB, or a child?**
`CHILD`. The only physical HDD Basilisk rows are `MetricName='HDD-EDB-Basilisk'`
inside the EDB forecast object. The correct HDD tree is:

```text
HDD
└── EDB                     (the only physical HDD DB Type)
    ├── Consumer            (Segment)
    ├── Enterprise          (Segment)
    └── Basilisk            (DB-Type-like sub-qualifier)
```

The site presents `HDD - EDB` and `HDD - Basilisk` as peers. The physical
encoding does not support that. Note also that the `MetricName` suffix slot
carries Segment and DB Type values interchangeably.

**2.3 The unqualified `SSD` value.**
`UNQUALIFIED_LEGACY_SERIES`, not a total.

```text
Resource='SSD'       533,141 rows | 32 keys | 21 forecast versions | from 2022-03-31
Resource='SSD-MCDB'  541,700 rows | 41 keys | 10 forecast versions | from 2023-10-31
```

A total cannot have fewer keys than its parts. In the matrix it occupies the
`NOT_FILTERED` routing state, not a sixth DB Type.

**2.4 Is CPU `Phoenix` the same concept as SSD `PhoenixDB`?**
`UNRESOLVED`. Deliberately not upgraded. They share an engine name and nothing
else that was found: CPU Phoenix is a `DBType` column value measured in cores,
while SSD PhoenixDB is a `Resource` label measured in TB produced by separate
objects. No shared column, object or join key ties them.

**2.5 Is `NonPhoenix` a DB Type or the complement of Phoenix?**
Both, precisely: a **stored value that functions as a partition**. `DBType` is
single valued with exactly two values and no NULL, so every row is either
Phoenix or NonPhoenix, with no overlap and no third value.

Evidence:
[`E3_e2_question_resolutions.csv`](evidence/E3/E3_e2_question_resolutions.csv).

### The two extra axes - classified, not modelled

| Axis | Physical column | Observed values | Metrics | Relation to DB Type |
|---|---|---|---|---|
| Segment | Partially: `data_type`, `MetricName` suffix, separate measure columns | `Consumer`, `Enterprise` | HDD | SEPARATE_AXIS |
| Organic/Inorganic | Partially: `Type` plus object naming | `Organic`, `Organic_adjust`, `BESTLA` | CPU, SSD, HDD | SEPARATE_AXIS |

Both are **separate axes**. Two overloading problems are recorded:

1. The `MetricName` suffix slot carries Segment values (`Consumer`, `Enterprise`)
   and a DB-Type-like value (`Basilisk`) in the same position.
2. The Excel column labelled "Scenario" mixes Segment values with the real
   Scenario values `Consumed` and `Failover`.

A third naming inconsistency: `forecast_substrateBE_inorganic_ssd` carries
`Type='BESTLA'`, not `Inorganic`.

These are reported only. Whether the master model grows beyond
`Metric -> DB Type -> Granularity -> Region -> Key` is the owner's decision.

Evidence:
[`E3_extra_axes_evidence.csv`](evidence/E3/E3_extra_axes_evidence.csv).

### Sue/Xinmei Excel reconciliation

| Excel line | Verdict |
|---|---|
| HDD -> EDB | CONFIRMED (Excel omits Basilisk) |
| CPU -> Total (phx and nonphx) | PARTIALLY_CONFIRMED (real concept, separate object, not a stored value) |
| CPU -> Phoenix | CONFIRMED |
| CPU -> NonPhoenix | CONFIRMED |
| IOPS -> N/A | CONFIRMED |
| SSD -> MCDB(Total) | PARTIALLY_CONFIRMED (no `Total` Type value exists) |
| SSD -> PHX(Total) | PARTIALLY_CONFIRMED (no `Total` Type value exists) |
| SSD -> MCDB(Organic) | CONFIRMED |
| SSD -> PHX(Organic) | CONFIRMED |
| SSD rows marked "Updated in Earth? = no" | REFUTED: the objects are present and populated |
| Excel "Scenario" column holding Consumer/Enterprise | REFUTED: those are Segment |

Where the Excel and the data disagree, **the data is right** on three points: the
SSD objects do exist in Earth, `Total` is not a stored DB Type, and
Consumer/Enterprise are not Scenario. The Excel is right that IOPS has no DB
Type. The Excel is incomplete on HDD, which also has Basilisk.

Evidence:
[`E3_excel_reconciliation.csv`](evidence/E3/E3_excel_reconciliation.csv).

### Open questions

Six questions are carried forward without investigation, including whether the
unqualified SSD series is numerically a total, whether CPU `Total` equals
Phoenix plus NonPhoenix, and why the HDD Basilisk and Memory demand views are
`WHERE 1=0` placeholders.

See [`E3_open_questions.csv`](evidence/E3/E3_open_questions.csv).

### Validation

All twelve checks pass, including 4/30 queries, no sub-stage, no boundary work,
reuse of E1/E2 counts, and no blank cells.

Evidence: [`E3_validation.csv`](evidence/E3/E3_validation.csv).

### RM-E3-CLOSED

```text
RM-E3-CLOSED
Date: 2026-08-16
Matrix cells classified: 39
Metrics with an evidenced DB Type axis: 3 (CPU, HDD, SSD)
Metrics without: 2 (IOPS, Memory)
Canonical DB Types: 5 (unchanged)
Routing states: NOT_FILTERED, NOT_APPLICABLE
Extra axes reported: 2 (Segment, Organic/Inorganic)
Query budget used: 4 / 30
Open questions: 6
Next stage: E4 Granularity
```

RM-E1-CLOSED and RM-E2-CLOSED are unchanged.

```text
E3_COMPLETE_AWAITING_AUTHORIZATION
```


## E4 - Granularity Universe

### Purpose

What Granularity concepts actually exist for the five approved Base Metrics?

E1, E2 and E3 stayed closed. No Metric, DB Type or applicability work was
performed. No rescan, no dependency expansion, no sub-stage.

```text
SQL executions: 9 / 20
```

Ledger: [`E4_query_ledger.csv`](evidence/E4/E4_query_ledger.csv).

### Canonical Granularity universe

```text
CANONICAL_GRANULARITY_COUNT = 3

Forest
Forest_SKU
Region
```

All three are stored values of a physical `Granularity` column, paired with
`GranularityValue`, on the `SubstrateBE_DemandForecast_*` family.

| Canonical | Raw spellings | Value shape | Metrics |
|---|---|---|---|
| Forest | `Forest`, `*_Forest` token | bare forest alias, e.g. `GBRP302` | HDD, SSD |
| Forest_SKU | `Forest_SKU`, `ForestSKU` token | forest + SKU generation, e.g. `APCPRD02-HP Gen8` | CPU, IOPS, SSD |
| Region | `Region`, `*_Region` token | region + stripe, e.g. `CAN-Go Local` | CPU, HDD, IOPS, SSD |

Universe:
[`E4_granularity_universe.csv`](evidence/E4/E4_granularity_universe.csv).

### The object names contradict the stored values

This is the most important E4 finding, and it is exactly why object-name
evidence is never upgraded to physical-column evidence.

| Object | Name implies | `Granularity` actually stores |
|---|---|---|
| `SubstrateBE_DemandForecast_CPU_Forest` | Forest | **Forest_SKU** |
| `SubstrateBE_DemandForecast_IOPS_Forest` | Forest | **Forest_SKU** |
| `SubstrateBE_DemandForecast_Ssd_MCDB_ForestSKU` | ForestSKU | **Forest** |

Anyone joining or filtering on the object name alone will select the wrong
grain. The `_Perturbed` variants were checked and agree with their parents.

### Forest to Region relationship

```text
FOREST_ROLLS_UP_TO_REGION
```

From `vw_SubstrateBE_Forests_V2`:

```text
rows    = 173
forests = 173
regions = 35
stripes = 6
forests mapping to more than one region = 0
```

A clean rollup with no overlap. Region-level values can be derived by
aggregating forest-level values.

Note that the stored `Region` granularity value is a **composite** of region and
stripe, such as `CAN-Go Local`, where stripes include `Go Local`, `Multitenant`
and `Gallatin`. Region keys are therefore not pure geography, which matters for
E8.

Hierarchy:
[`E4_granularity_hierarchy.csv`](evidence/E4/E4_granularity_hierarchy.csv).

### ForestSKU

```text
FORESTSKU_DISTINCT_GRANULARITY
```

`Forest_SKU` is a stored value of the physical `Granularity` column, not merely
a naming convention, and it carries 51,194,194 CPU rows and 32,620,690 IOPS
rows. Its values decompose as forest + SKU generation, so it is strictly finer
than `Forest`. It is the finest published forecast grain.

Separately, `SKU` also appears as an independent column in other objects
(`Forest_SKU` in 14 approved objects, `SKU` in 25, `Sku_CommonName` in the Memory
raw view), so:

```text
AxisName = SKU
Status   = EXTRA_AXIS_DETECTED
```

SKU is **not** modelled into the master tree in E4.

### DAG

```text
DAG_IS_SEPARATE_AXIS
```

DAG was **observed inside approved scope**, so this is not a scope-induced false
negative. `vw_SubstrateBE_MemoryRawData` is a Memory object and carries a
physical `Dagname` column with values such as `NAMPR07DG525`, `APCPR04DG388` and
`APCPR02DG461`, alongside `Forest` and `Sku_CommonName`.

DAG also appears in:

- `vw_DAG_Metrics` and `vw_COPSMultitenant_Extend` (shared actuals)
- `vw_SubstrateBE_ROPS_Limits`, `_by_Dag` and `_Telemetry` (deferred ROPS branch,
  inspected only to classify DAG and not reopened)

The decisive evidence is negative: the `Granularity` column vocabulary is
exactly `Forest`, `Forest_SKU` and `Region`. **`Dag` is never a stored
Granularity value.** DAG is a real fleet level finer than Forest, used in the
actuals and telemetry layer, but nothing is published at DAG grain as a forecast
Granularity.

#### Role of `vw_DAG_Metrics`

It is a **DAG-grain actuals object**, not a granularity definition. It has a
physical `DagName` column with `Forest` and `Region` as attributes, roughly 190
measure columns, and the `MetricName` / `MetricType` / `MetricValue` triple that
supplies dashboard vocabulary for CPU, HDD, SSD and Memory. It has **no**
`Granularity` column. The `DAG` in its name is object naming plus the grain of
its rows; it does not make DAG a forecast Granularity.

### Granularity by approved Metric - observation only

| Metric | Forest | Forest_SKU | Region | DAG |
|---|---|---|---|---|
| CPU | object name only | PHYSICAL | PHYSICAL | actuals only |
| HDD | PHYSICAL | not observed | PHYSICAL | actuals only |
| IOPS | object name only | PHYSICAL | PHYSICAL | not observed |
| SSD | PHYSICAL | object name and Key | PHYSICAL | actuals only |
| Memory | object name only | not observed | object name only | PHYSICAL |

This is observation, **not** applicability. The
`Metric x DB Type x Granularity` matrix belongs to E5.

Evidence:
[`E4_granularity_by_metric_evidence.csv`](evidence/E4/E4_granularity_by_metric_evidence.csv).

### Extra axes detected, not modelled

| Axis | Status | Relation to Granularity |
|---|---|---|
| SKU | EXTRA_AXIS_DETECTED | Qualifier: refines Forest into Forest_SKU |
| Stripe | EXTRA_AXIS_DETECTED | Qualifier: embedded inside Region values |
| DAG | SEPARATE_AXIS | Actuals and telemetry level, not a forecast grain |
| Environment | OBSERVED_NOT_CLASSIFIED | Unresolved, carried to E5 |

Evidence:
[`E4_compound_axis_evidence.csv`](evidence/E4/E4_compound_axis_evidence.csv).

### Routing states

Kept separate from the canonical universe, exactly as E3 did for DB Type.

```text
GRANULARITY_NOT_APPLICABLE : Memory
GRANULARITY_NOT_FILTERED   : none found in approved scope
```

No Memory object carries a `Granularity` column, and its two demand views are
`WHERE 1=0` placeholders. The absence of any `NOT_FILTERED` state is a negative
finding rather than an omission: every approved demand forecast object is
grain-specific and stores exactly one Granularity value.

Evidence:
[`E4_routing_states.csv`](evidence/E4/E4_routing_states.csv).

### Candidates searched and not found

`Stamp`, `Geo`, `Site` and `Cluster` were searched inside the validated boundary
and local metadata. `Geo`, `Site` and `Cluster` have no columns or objects at
all. `Stamp` appears only inside measure names such as
`DagTenantSearchStampShardMailboxCount` and in the deferred `ASCStamp` branch, so
it is `NOT_A_GRANULARITY` in approved scope.

### Direct owner answers

**A. Canonical Granularity concepts:** 3.

**B. Every canonical value:** `Forest`, `Forest_SKU`, `Region`.

**C. Is Forest a Granularity?** Yes, `GRANULARITY_CONFIRMED`.

**D. Is Region a Granularity?** Yes, `GRANULARITY_CONFIRMED`, with a composite
region+stripe value shape.

**E. What exactly is ForestSKU?** `FORESTSKU_DISTINCT_GRANULARITY`.

**F. Is DAG a Granularity?** `DAG_IS_SEPARATE_AXIS`.

**G. Any Granularity beyond Forest / Forest_SKU / Region / DAG?** No.

**H. Separate SKU or other axis?** Yes: SKU and Stripe are
`EXTRA_AXIS_DETECTED`; Environment is observed but unresolved.

**I. Granularity per approved Metric:** see the table above, observation only.

**J. Forest to Region:** `FOREST_ROLLS_UP_TO_REGION`.

**K. Routing states:** `GRANULARITY_NOT_APPLICABLE` for Memory; no
`GRANULARITY_NOT_FILTERED` found. Neither counts toward the canonical total.

Answers:
[`E4_owner_answers.csv`](evidence/E4/E4_owner_answers.csv).

### Open questions

Five questions carried forward without investigation, including why the object
names contradict the stored grain, whether Environment is an axis, and whether
Region should be decomposed into Region and Stripe.

See [`E4_open_questions.csv`](evidence/E4/E4_open_questions.csv).

### Validation

All 23 checks pass.

Evidence: [`E4_validation.csv`](evidence/E4/E4_validation.csv).

### RM-E4-CLOSED

```text
RM-E4-CLOSED
Date: 2026-08-16
Canonical Granularity count: 3
Canonical values: Forest, Forest_SKU, Region
Raw aliases/tokens: Forest, Forest_SKU, ForestSKU, *_Forest, *_Region, *_ForestSKU
ForestSKU classification: FORESTSKU_DISTINCT_GRANULARITY
DAG classification: DAG_IS_SEPARATE_AXIS
DAG scope caveat: observed inside approved scope in vw_SubstrateBE_MemoryRawData, so absence is not scope-induced
vw_DAG_Metrics role: DAG-grain actuals with no Granularity column
Forest vs Region: FOREST_ROLLS_UP_TO_REGION (173 forests, 35 regions, 0 multi-region forests)
Routing states: GRANULARITY_NOT_APPLICABLE (Memory); GRANULARITY_NOT_FILTERED none found
Extra axes detected: SKU, Stripe, DAG, Environment (unresolved)
Query budget used: 9 / 20
Open questions: 5
Next stage: E5 Metric x DB Type x Granularity
```

RM-E1-CLOSED, RM-E2-CLOSED and RM-E3-CLOSED are unchanged.

```text
E4_COMPLETE_AWAITING_AUTHORIZATION
```


## E5 - Metric x DB Type x Granularity

### Purpose

For every valid Metric x DB Type branch established by E3, which of the three
canonical Granularity values established by E4 actually apply?

E1, E2, E3 and E4 stayed closed. No new Metric, DB Type or Granularity was
introduced. No rescan, no dependency expansion, no sub-stage.

```text
SQL_EXECUTIONS_USED = 14 / 30
HARD_CAP_RESPECTED  = YES
OWNER_WAIVER_USED   = NO
```

One connection attempt was rejected by the server firewall before the VPN was
restored. It executed no SQL and therefore consumed no budget; it is logged in
the ledger as `BLOCKED_FIREWALL`.

Ledger: [`E5_query_ledger.csv`](evidence/E5/E5_query_ledger.csv).

### The structural problem E5 had to solve first

Local metadata showed that **no DB-Type-carrying object has a `Granularity`
column**. The physical `Granularity` column exists only on the
`SubstrateBE_DemandForecast_*` family, which is not the family that carries
`DBType` or the SSD `Resource` labels.

Since object names were barred as decisive evidence by E4, grain for those
branches had to be established from the actual `Key` / `MyKey` value structure.
That is what most of the eleven queries did.

```text
CELLS_CLASSIFIED_FROM_PHYSICAL_GRANULARITY = 14
CELLS_CLASSIFIED_FROM_INFERRED_COLUMNS     = 20
CELLS_CLASSIFIED_FROM_OBJECT_NAME          = 0
```

### The matrix

| Metric | DB Type / Route | Forest | Forest_SKU | Region | Serving caveat |
|---|---|---|---|---|---|
| CPU | Phoenix | YES | NO | YES | |
| CPU | NonPhoenix | YES | NO | YES | |
| CPU | Basilisk | LABEL_ONLY | LABEL_ONLY | LABEL_ONLY | serving views `WHERE 1=0` |
| CPU | NOT_FILTERED / Total | NO | YES | YES | |
| HDD | EDB | YES | NO | YES | |
| HDD | Basilisk | SERVING_EMPTY | NO | SERVING_EMPTY | physically confirmed, views empty |
| HDD | NOT_FILTERED | YES | NO | YES | |
| SSD | MCDB | YES | YES | YES | |
| SSD | Phoenix | YES | NO | YES | |
| SSD | NOT_FILTERED / unqualified | NO | NO | YES | |
| IOPS | NOT_APPLICABLE | NO | YES | YES | |
| Memory | NOT_APPLICABLE | N/A | N/A | N/A | both demand views `WHERE 1=0` |

34 classified cells, 20 `PHYSICAL_CONFIRMED` or
`PHYSICAL_CONFIRMED_SERVING_EMPTY`, no blanks:
[`E5_metric_dbtype_granularity_matrix.csv`](evidence/E5/E5_metric_dbtype_granularity_matrix.csv).

### The finding that matters most

**Changing DB Type silently changes the available grain for CPU.**

```text
CPU Phoenix / NonPhoenix -> Forest + Region
CPU Total                -> Forest_SKU + Region
```

The by-DB objects store bare forest aliases such as `NAMP134` and `CHEP278`.
A distinct-value probe returned 159 distinct keys with **zero** containing a SKU
suffix, and a `LIKE '%Gen%'` probe on the region object returned nothing. The
Total route, by contrast, stores `Granularity = 'Forest_SKU'` with values such
as `NAMP131-WCS Gen6`.

So CPU Total is not a superset of the DB-Type branches at the same grain. They
are different grains entirely, and no aggregation reconciles them directly.

### CPU

| Route | Forest | Forest_SKU | Region |
|---|---|---|---|
| Phoenix | 23,318,632 | - | 2,825,340 |
| NonPhoenix | 20,937,897 | - | 3,396,484 |
| Total | - | 51,194,194 | 8,508,120 |
| Basilisk | LABEL_ONLY | LABEL_ONLY | LABEL_ONLY |

`Total` remains `SEPARATE_OBJECT`. It is **not** `DBType IS NULL`, because
`forecast_substrateBE_cpu_region` has no `DBType` column at all.

### HDD

The physical `Granularity` column settles this directly:

```text
HDD-EDB-Consumer   | Forest 26,912,021   | Region 5,167,235
HDD-EDB-Enterprise | Forest 26,759,853   | Region 5,239,184
HDD-EDB-Basilisk   | Forest    246,915   | Region    74,162
```

EDB and Basilisk have identical grain coverage. The difference is **serving, not
physics**: 321,077 Basilisk rows exist, yet
`vw_SubstrateBE_Demand_HddBasilisk_Forest` and `_Region` both return zero rows.
Those cells are therefore `PHYSICAL_CONFIRMED_SERVING_EMPTY`, not
`PHYSICAL_CONFIRMED`.

### SSD

SSD MCDB is the **only branch in the entire catalog with all three canonical
grains**:

```text
SSD-MCDB       Forest 2,989,717 | Forest_SKU 30,966,833 | Region 537,480
SSD-PhoenixDB  Forest 1,614,543 |            -          | Region 426,246
SSD (legacy)          -         |            -          | Region 580,213 + 533,141
```

Grain came from Key structure:
`NAM-Multitenant-NAMPRD08-WCS Gen7` carries a SKU suffix and is Forest_SKU,
while `NAM-Multitenant-NAMPRD03` stops at the forest and is Forest.

A second naming contradiction surfaced: `SubstrateBE_SsdForecastForestSKU` reads
like a generic SSD series, but every row carries `Resource = 'SSD-MCDB'`.

### IOPS and Memory

IOPS has **no DB Type axis but a real Granularity axis** — `Forest_SKU`
(32,620,690) and `Region` (6,451,852). Its forest-level object stores
`Forest_SKU`, so bare `Forest` is not observed. No fake DB Type value was
created.

Memory keeps `GRANULARITY_NOT_APPLICABLE` on both axes and is represented by a
single structural row rather than three manufactured empty cells.

### UI / UX filter contract

| Metric | DB Type filter | Visible DB Type values | Granularity filter | Visible Granularity values |
|---|---|---|---|---|
| CPU | SHOW | Phoenix, NonPhoenix, Total (route) | SHOW | Forest, Region (Forest_SKU on Total only) |
| HDD | SHOW | EDB, Basilisk, All (route) | SHOW | Forest, Region |
| SSD | SHOW | MCDB, Phoenix, SSD (route) | SHOW | Forest, Forest_SKU, Region |
| IOPS | DO_NOT_SHOW | - | SHOW | Forest_SKU, Region |
| Memory | DO_NOT_SHOW | - | DO_NOT_SHOW | - |

Contract:
[`E5_ui_filter_applicability.csv`](evidence/E5/E5_ui_filter_applicability.csv).

### Filter value routing contract

| Metric | Filter | Visible value | Routing type | Source / column | Predicate |
|---|---|---|---|---|---|
| CPU | DB Type | Phoenix | PREDICATE_ON_COLUMN | `forecast_substrateBE_cpu_byDB_*` / `DBType` | `DBType = 'Phoenix'` |
| CPU | DB Type | NonPhoenix | PREDICATE_ON_COLUMN | `forecast_substrateBE_cpu_byDB_*` / `DBType` | `DBType = 'NonPhoenix'` |
| CPU | DB Type | Total | SEPARATE_OBJECT | `forecast_substrateBE_cpu_region` | no DB Type predicate |
| CPU | DB Type | Basilisk | NOT_ROUTABLE_YET | serving views are `WHERE 1=0` | - |
| HDD | DB Type | EDB | NESTED_IN_LABEL | `SubstrateBE_DemandForecast_HDD_EDB_*` / `MetricName` | `MetricName IN ('HDD-EDB-Consumer','HDD-EDB-Enterprise')` |
| HDD | DB Type | Basilisk | NESTED_IN_LABEL | same / `MetricName` | `MetricName = 'HDD-EDB-Basilisk'` |
| SSD | DB Type | MCDB | RESOURCE_LABEL | MCDB objects / `Resource` | `Resource = 'SSD-MCDB'` |
| SSD | DB Type | Phoenix | RESOURCE_LABEL | PhoenixDB objects / `Resource` | `Resource = 'SSD-PhoenixDB'` |
| SSD | DB Type | SSD (unqualified) | RESOURCE_LABEL | `*_ForecastRegion` / `Resource` | `Resource = 'SSD'` |

```text
ROUTABLE_VISIBLE_FILTER_VALUES     = 13
NOT_ROUTABLE_VISIBLE_FILTER_VALUES = 1   (CPU Basilisk)
```

CPU Basilisk was deliberately left `NOT_ROUTABLE_YET` rather than given an
invented predicate.

One route conflict is recorded rather than resolved: the `HDD - EDB` site view
reads the **unqualified** `forecast_substrateBE_hdd_region`, not the
MetricName-qualified objects. Both routes are documented.

Full contract:
[`E5_filter_value_routing.csv`](evidence/E5/E5_filter_value_routing.csv).

### Granularity profiles

```text
Region only        : SSD unqualified
Forest + Region    : CPU Phoenix, CPU NonPhoenix, HDD EDB, HDD Basilisk, HDD unfiltered, SSD Phoenix
Forest_SKU + Region: CPU Total, IOPS
All three          : SSD MCDB
Forest only        : none
Forest_SKU only    : none
```

### Naming contradictions

Five recorded, two newly found in E5:

- `SubstrateBE_SsdForecastForestSKU` is entirely `SSD-MCDB`, not a generic SSD series.
- `forecast_substrateBE_cpu_byDB_forest` is genuinely Forest grain, which
  contradicts the similarly named `SubstrateBE_DemandForecast_CPU_Forest` that
  stores Forest_SKU.

Evidence:
[`E5_naming_contradictions.csv`](evidence/E5/E5_naming_contradictions.csv)
and [`E5_serving_gap_evidence.csv`](evidence/E5/E5_serving_gap_evidence.csv).

### Upstream contradiction status

```text
NO_UPSTREAM_UNIVERSE_CONTRADICTION
```

No new physical DB Type and no new physical Granularity appeared. The canonical
universes remain 5 and 3.

### Validation

All 36 checks pass, including
`CELLS_CLASSIFIED_FROM_OBJECT_NAME = 0`, 14/30 SQL executions, and no
sub-stage.

Evidence: [`E5_validation.csv`](evidence/E5/E5_validation.csv).

### E5 addendum - conditional UI navigation contract

The UI must not assume a fixed axis sequence. Each Metric derives its next
applicable axis from the taxonomy evidence, and any `NOT_APPLICABLE` axis is
skipped automatically rather than rendered as an empty control.

Three further queries were executed to populate `AllowedNextValues` honestly,
bringing the stage to 14/30. This resolved the allowed values for
already-confirmed branches only; it is **not** Scenario-universe discovery.

#### The Scenario axis is not uniform

| Metric | Scenario column | Observed values | Real Scenario axis |
|---|---|---|---|
| CPU | YES | `Consumed`, `Failover` | YES |
| IOPS | YES | `Consumed`, `Failover` | YES |
| HDD | YES | `Consumer`, `Enterprise`, `Basilisk` | **NO** |
| SSD | YES | NULL or empty only | **NO** |
| Memory | NO | - | NO |

Two findings matter here.

**HDD overloads its `Scenario` column.** It holds two Segment values and one DB
Type value, so HDD has no Consumed/Failover axis at all. The
`Scenario = 'Basilisk'` count is 74,162, which matches `HDD-EDB-Basilisk` at
region grain exactly, so this column is also a **second route** to HDD Basilisk.

**SSD has the column but never populates it.**
`SubstrateBE_Ssd_MCDB_ForecastRegion` splits 309,213 NULL and 223,928 empty, so
there is no scenario vocabulary to offer.

Evidence:
[`E5_scenario_axis_evidence.csv`](evidence/E5/E5_scenario_axis_evidence.csv).

#### Navigation behavior

```text
SHOW_NEXT_AXIS         14
SKIP_AXIS_AND_CONTINUE  7
TERMINAL                1
UNRESOLVED             11
```

| Metric | Axis chain |
|---|---|
| CPU | Metric -> DBType -> Scenario -> Granularity -> Region (E7) |
| HDD | Metric -> DBType -> ~~Scenario~~ skipped -> Granularity -> Region (E7) |
| SSD | Metric -> DBType -> ~~Scenario~~ skipped -> Granularity -> Region (E7) |
| IOPS | Metric -> ~~DBType~~ skipped -> Scenario -> Granularity -> Region (E7) |
| Memory | Metric -> all axes NOT_APPLICABLE -> UNRESOLVED_LATER_STAGE |

Worked examples from the contract:

```text
Metric = CPU
  NextApplicableAxis = DBType
  AllowedNextValues  = Total | Phoenix | NonPhoenix

CPU + Phoenix
  NextApplicableAxis = Scenario
  AllowedNextValues  = Consumed | Failover

CPU + Phoenix + Consumed
  NextApplicableAxis = Granularity
  AllowedNextValues  = Forest | Region

CPU + Total + Consumed
  NextApplicableAxis = Granularity
  AllowedNextValues  = Forest_SKU | Region     <- different grain set

Metric = IOPS
  DBType = NOT_APPLICABLE, skipped
  NextApplicableAxis = Scenario
  AllowedNextValues  = Consumed | Failover

Metric = HDD + EDB
  Scenario = skipped, the column holds Segment and DB Type values
  NextApplicableAxis = Granularity
  AllowedNextValues  = Forest | Region

Metric = Memory
  NextApplicableAxis = UNRESOLVED_LATER_STAGE
  render no control at all
```

`CPU + Basilisk` is the single `TERMINAL` row: it must not be offered, because no
physical row exists and every serving view is `WHERE 1=0`.

Every `SKIP_AXIS_AND_CONTINUE` row carries a `SkipReason`, and no row has a blank
behavior or evidence status. Nothing downstream of Granularity was invented: all
eleven `UNRESOLVED` rows point at E6.

Contract:
[`E5_ui_navigation_contract.csv`](evidence/E5/E5_ui_navigation_contract.csv).

This contract is declarative. No UI or production code was created or modified.

### RM-E5-CLOSED

```text
RM-E5-CLOSED
Date: 2026-08-17
E3 branches evaluated: 12 of 12
Matrix cells classified: 34
Physically confirmed combinations: 20
CPU: Phoenix and NonPhoenix = Forest + Region; Total = Forest_SKU + Region; Basilisk = LABEL_ONLY
HDD: EDB = Forest + Region; Basilisk = Forest + Region physically but serving empty
SSD: MCDB = all three grains; Phoenix = Forest + Region; unqualified = Region only
IOPS: no DB Type axis; Forest_SKU + Region
Memory: NOT_APPLICABLE on both axes
CELLS_CLASSIFIED_FROM_PHYSICAL_GRANULARITY = 14
CELLS_CLASSIFIED_FROM_INFERRED_COLUMNS = 20
CELLS_CLASSIFIED_FROM_OBJECT_NAME = 0
ROUTABLE_VISIBLE_FILTER_VALUES = 13
NOT_ROUTABLE_VISIBLE_FILTER_VALUES = 1
Serving gaps: HDD Basilisk (both grains), CPU Basilisk, Memory
Naming contradictions: 5 (2 new in E5)
Upstream contradiction: NO_UPSTREAM_UNIVERSE_CONTRADICTION
SQL_EXECUTIONS_USED = 14 / 30
HARD_CAP_RESPECTED = YES
OWNER_WAIVER_USED = NO
UI navigation contract: 33 rows (14 show, 7 skip, 1 terminal, 11 unresolved)
Scenario axis real for CPU and IOPS only; HDD column overloaded, SSD column unpopulated
Open questions: 5
Next stage: E6 Scenario / Segment / Organic-Inorganic (roadmap extended to E0-E11)
```

RM-E1-CLOSED, RM-E2-CLOSED, RM-E3-CLOSED and RM-E4-CLOSED are unchanged.

```text
E5_COMPLETE_AWAITING_AUTHORIZATION
```


## E6 - Scenario / Segment / Organic-Inorganic Applicability

### Roadmap extension

Scenario, Segment and Organic/Inorganic needed a real closure stage before
Region, so the roadmap is extended from E0-E10 to **E0-E11**:

```text
E1  Metric
E2  DB Type Universe
E3  Metric x DB Type
E4  Granularity Universe
E5  Metric x DB Type x Granularity
E6  Scenario / Segment / Organic-Inorganic Applicability   <- this stage
E7  Region Universe
E8  x Region
E9  Key
E10 Source Table
E11 Final Reconciliation
```

The master filename stays `AEGIS_Master_Catalog_Discovery_E0_E10.md`
deliberately, because existing documentation links depend on it. Prior internal
references to "E6 = Region Universe" have been corrected to E7.

### Purpose and cost

For each valid E5 branch, which of Scenario, Segment and Organic/Inorganic apply,
which values exist, and how should navigation route through them?

```text
SQL_EXECUTIONS_USED = 8 / 20   (4 initial + 3 correction + 1 final reconciliation)
HARD_CAP_RESPECTED  = YES
OWNER_WAIVER_USED   = NO
```

Only four queries were needed initially because E1 had already profiled 377 raw
Scenario rows and E5 had established the Scenario baseline. A later review
identified two closure blockers, resolved with three further queries: a
key-population proof for `Organic_adjust` and a Segment reconciliation for the
HDD inorganic route.

```text
CELLS_CLASSIFIED_FROM_OBJECT_NAME = 0
```

### Scenario

The canonical value set is small and does not belong to every metric:

```text
Consumed | Failover
```

| Metric | Real Scenario axis | Values |
|---|---|---|
| CPU | YES | Consumed, Failover on all three routable DB Types |
| IOPS | YES | Consumed 3,225,926 and Failover 3,225,926 |
| HDD | NO | the column holds Segment and DB Type values |
| SSD | NO | the column is present but only NULL or empty |
| Memory | NO | no Scenario column at all |

**CPU coverage does not differ by DB Type.** Phoenix carries 1,601,026 Consumed
and 1,224,314 Failover, NonPhoenix 1,804,572 and 1,591,912, Total 4,254,060 and
4,254,060.

SSD does have a rich demand-planning vocabulary — `High Volume`, `Low Volume`,
attachment-offloading variants and `BESTLA` suffixes — but it lives in
non-serving objects such as `CPG_SSD_Demand_Forecast_Scenarios`. It is a
different concept from the Consumed/Failover capacity scenario and is outside
the E5 branch roster.

Evidence:
[`E6_scenario_by_branch.csv`](evidence/E6/E6_scenario_by_branch.csv).

### Segment

```text
Consumer | Enterprise
```

Segment exists **only in HDD**. No CPU, IOPS, SSD or Memory object carries a
Segment-bearing column, and no in-scope object has a literal `Segment` column at
all.

HDD encodes the same value three different ways:

```text
forecast_substrateBE_hdd                  data_type
forecast_substrateBE_hdd_region           Scenario
SubstrateBE_DemandForecast_HDD_EDB_*      MetricName suffix
```

#### Does Segment cross HDD Basilisk? No.

This was the decisive E6 question, and the answer is arithmetic:

```text
Consumer    26,915,733
Enterprise  26,759,854
Basilisk       246,915
            ----------
total       53,922,502   = the exact row count of forecast_substrateBE_hdd
```

The three values are **mutually exclusive and exhaustive within one slot**. A DB
Type is sitting in the same column position as two Segment values. Therefore
`HDD-EDB-Basilisk-Consumer` and `HDD-EDB-Basilisk-Enterprise` do not exist and
were not invented.

Selecting Basilisk removes the Segment axis entirely. That is a
`DATA_REQUIRED` nesting constraint, not a UI preference.

`Greenland` is **not** a Segment value: it appears only as measure column names
such as `GreenlandTotal` and `greenland_forecast`, never as a row value in scope.

Evidence:
[`E6_segment_by_branch.csv`](evidence/E6/E6_segment_by_branch.csv).

### Organic / Inorganic

Raw values found:

```text
Organic
Organic_adjust
Organic (Without SubstrateBlobShard)
Inorganics
BESTLA
```

Canonical set:

```text
Organic | Inorganic
```

| Raw value | Classification | Canonical | Why |
|---|---|---|---|
| `Organic` | CANONICAL_AXIS_VALUE | Organic | Stored across CPU, HDD, IOPS and SSD |
| `Organic_adjust` | **PROCESSING_STATE** | Organic | Proven by key-set identity: `EXCEPT` in both directions returns **0** one-sided keys for CPU and for IOPS |
| `Organic (Without SubstrateBlobShard)` | ALIAS_OR_VARIANT | Organic | 145,757 HDD rows; a scoped restatement |
| `Inorganics` | CANONICAL_AXIS_VALUE | Inorganic | 352,139 at region and 1,446,739 at forest, both `Resource='HDD'` |
| `BESTLA` | ALIAS_OR_VARIANT | Inorganic | 591,384 rows occupying the inorganic `Type` slot for SSD Phoenix |
| `Inorganic` | **NOT_AXIS_VALUE** | - | The singular spelling is never stored; only `Inorganics` is |

Two findings are worth stating plainly.

**Inorganic does exist physically**, contradicting the earlier assumption that it
lived only in object naming. The stored spelling is `Inorganics`, plural.

**`Organic_adjust` is not a selectable demand nature.** This was initially argued
from equal row counts, which is not sufficient. A key-set comparison now proves
it:

```text
CPU_ORGANIC_ONLY_KEYS         = 0
CPU_ORGANIC_ADJUST_ONLY_KEYS  = 0
IOPS_ORGANIC_ONLY_KEYS        = 0
IOPS_ORGANIC_ADJUST_ONLY_KEYS = 0
SAME_KEY_POPULATION           = YES for both metrics
```

Compared on the dimensional projection only, excluding the `Type` discriminator
and the value measures. Offering `Organic_adjust` beside `Organic` in a filter
would double-count the same population.

Applicability:

| Branch | Axis |
|---|---|
| HDD EDB, HDD All | Organic and Inorganic |
| SSD Phoenix | Organic and Inorganic (BESTLA) |
| CPU all routes, IOPS, SSD MCDB, SSD legacy | Organic only, so no choice to offer |
| HDD Basilisk, Memory | none |

#### HDD Segment x Organic/Inorganic is asymmetric

The two axes do **not** form a Cartesian product:

| Segment | Organic | Inorganic |
|---|---|---|
| Consumer | YES (5,170,217) | **NO** |
| Enterprise | YES (5,240,675) | **NO** |

The HDD `Scenario` column is overloaded a **third** way. On the organic route it
holds Segment and DB Type values; on the inorganic route it holds demand
initiative names:

```text
Go Big With Memory Shard Efficiency: Scenario B   229,816 region | 565,656 forest
Go Big With Memory Shard Efficiency                89,700 region | 774,540 forest
GoBig Base                                         15,456 region |  52,416 forest
GoBig High                                         15,456 region |  52,416 forest
TWN Migration                                       1,711 region |   1,711 forest
```

Neither `Consumer` nor `Enterprise` appears anywhere on the inorganic route, and
the inorganic objects carry `Resource='HDD'` with **no DB Type split** either.

#### The inorganic route has no DB Type either

A final reconciliation tested whether `HDD -> EDB -> Inorganic` is a real path.
It is not. None of the three HDD DB Type encodings exists on the inorganic
objects:

```text
MetricName   absent
data_type    absent
DBType       absent
Resource     = 'HDD' only
Fleet=[BareMetal] Workload=[BE] Unit=[TB]   single constant combination
             across all 352,139 region and 1,446,739 forest rows
```

```text
HDD_INORGANIC_DBTYPE_APPLICABILITY = NOT_APPLICABLE
```

Consequently the HDD hierarchy is forced by the data, not chosen by preference:

```text
Organic/Inorganic MUST_FOLLOW_METRIC        (DATA_REQUIRED)
DBType            MUST_FOLLOW_ORGANIC_AXIS  (DATA_REQUIRED, BRANCH_CONDITIONAL)
Segment           MUST_FOLLOW_DBTYPE        (organic branch only)

Organic   -> DB Type shown, then Segment on EDB and All
Inorganic -> DB Type skipped, Segment skipped
```

`HDD -> EDB -> Inorganic` and `HDD -> Basilisk -> Inorganic` are therefore
**not offered**, because they do not physically exist.

These initiative values are recorded but **not modelled** as a new axis:
[`E6_inorganic_initiative_values.csv`](evidence/E6/E6_inorganic_initiative_values.csv).

Matrix:
[`E6_hdd_segment_organic_matrix.csv`](evidence/E6/E6_hdd_segment_organic_matrix.csv).
Correction evidence:
[`E6_closure_correction_evidence.csv`](evidence/E6/E6_closure_correction_evidence.csv).

Evidence:
[`E6_organic_inorganic_by_branch.csv`](evidence/E6/E6_organic_inorganic_by_branch.csv)
and
[`E6_axis_value_classification.csv`](evidence/E6/E6_axis_value_classification.csv).

### Applicability matrix

49 fully classified cells, every one with a class and a reason, 48 from a
physical column and one from validated upstream evidence:
[`E6_axis_applicability_matrix.csv`](evidence/E6/E6_axis_applicability_matrix.csv).

### Nesting: data versus UI policy

| Constraint | Source |
|---|---|
| Organic/Inorganic MUST_FOLLOW_METRIC for HDD | DATA_REQUIRED: the inorganic route carries neither DB Type nor Segment |
| DBType MUST_FOLLOW_ORGANIC_AXIS for HDD | DATA_REQUIRED: DB Type is encoded only on the organic objects |
| Scenario MUST_FOLLOW_DBTYPE for CPU | DATA_REQUIRED: the column lives inside the by-DB object |
| Scenario MUST_FOLLOW_METRIC for IOPS | DATA_REQUIRED: there is no DB Type axis |
| Organic/Inorganic MUST_FOLLOW_DBTYPE for HDD and SSD Phoenix | DATA_REQUIRED: inorganic demand is served by separate objects |
| Granularity placed last | OWNER_DEFINED_UI_POLICY |
| Single-value axes skipped | OWNER_DEFINED_UI_POLICY |

```text
DATA_REQUIRED            17 nodes
OWNER_DEFINED_UI_POLICY  14 nodes
UNRESOLVED               10 nodes
```

Evidence:
[`E6_axis_nesting_constraints.csv`](evidence/E6/E6_axis_nesting_constraints.csv).

### Conditional navigation contract

The E5 baseline of 33 rows was read and **extended**, not rebuilt:

```text
                          E5 baseline   E6 contract
SHOW_NEXT_AXIS                14            23
SKIP_AXIS_AND_CONTINUE         7             6
TERMINAL                       1             1
UNRESOLVED_LATER_STAGE        11            11
                          -----------   -----------
                              33            41

Counts derived from the final CSV after the HDD subtree was restructured. The
invalid EDB-Inorganic and All-Inorganic paths were removed and replaced by a
single `HDD > Inorganic` node that skips both DB Type and Segment.
```

No row lacks a behavior or an evidence status, and every skip carries a reason.

Contract:
[`E6_ui_navigation_contract.csv`](evidence/E6/E6_ui_navigation_contract.csv).

### Owner-facing cascade

```text
CPU
└─ DB Type
   ├─ Phoenix
   │  └─ Scenario [Consumed | Failover]
   │     └─ Granularity [Forest | Region]
   │        └─ Region ... UNRESOLVED_LATER_STAGE (E7)
   ├─ NonPhoenix
   │  └─ Scenario [Consumed | Failover]
   │     └─ Granularity [Forest | Region]
   ├─ Total
   │  └─ Scenario [Consumed | Failover]
   │     └─ Granularity [Forest_SKU | Region]      <- different grain set
   └─ Basilisk .......... TERMINAL, do not offer

HDD                                          <- RESTRUCTURED
├─ Scenario ............ SKIPPED (the HDD Scenario column never holds Consumed/Failover)
└─ Organic/Inorganic                          <- FIRST axis after Metric
   ├─ Organic
   │  └─ DB Type
   │     ├─ EDB
   │     │  └─ Segment [Consumer | Enterprise]
   │     │     └─ Granularity [Forest | Region]
   │     ├─ All  (routing state, no DB Type predicate)
   │     │  └─ Segment [Consumer | Enterprise]
   │     │     └─ Granularity [Forest | Region]
   │     └─ Basilisk
   │        ├─ Segment ... SKIPPED (Basilisk occupies the Segment slot)
   │        └─ Granularity [Forest | Region]   serving views empty
   └─ Inorganic
      ├─ DB Type ........ SKIPPED (no DB Type encoding exists on this route)
      ├─ Segment ........ SKIPPED (slot holds initiative names)
      └─ Granularity [Forest | Region]

SSD
└─ DB Type
   ├─ MCDB
   │  ├─ Scenario ....... SKIPPED (NULL or empty)
   │  ├─ Segment ........ SKIPPED (does not exist)
   │  ├─ Organic/Inorg .. SKIPPED (Organic only)
   │  └─ Granularity [Forest | Forest_SKU | Region]
   ├─ Phoenix
   │  ├─ Scenario ....... SKIPPED
   │  ├─ Segment ........ SKIPPED
   │  └─ Organic/Inorganic
   │     ├─ Organic              -> Granularity [Forest | Region]
   │     └─ Inorganic (BESTLA)   -> Granularity [Forest]      <- CORRECTED BY E8
   └─ SSD (legacy)
      └─ Granularity [Region]

IOPS
├─ DB Type ............. SKIPPED (no DB Type axis)
├─ Segment ............. SKIPPED (does not exist)
└─ Scenario [Consumed | Failover]
   └─ Granularity [Forest_SKU | Region]

Memory
└─ every axis NOT_APPLICABLE -> render no control at all
```

### Filter value routing

16 routing rows, every visible value carrying a status. Fifteen are `CONFIRMED`,
one is `SUPPORTED` (SSD inorganic maps through `BESTLA` by slot position rather
than a shared spelling), and one carried-forward value stays `UNRESOLVED`
(CPU Basilisk).

Evidence:
[`E6_filter_value_routing.csv`](evidence/E6/E6_filter_value_routing.csv).

### Upstream contradiction status

```text
NO_UPSTREAM_UNIVERSE_CONTRADICTION
```

### Validation

All 55 checks pass, including 8/20 SQL executions, master filename unchanged, and
no sub-stage.

Evidence: [`E6_validation.csv`](evidence/E6/E6_validation.csv).

### E6_POSTCLOSE_CORRECTION_FROM_E8

E8 found physical evidence that corrects one E6 branch conclusion. RM-E6-CLOSED
stands; this note preserves auditability rather than pretending E6 was never
closed.

| Field | Value |
|---|---|
| FindingStage | E8 |
| AffectedStage | E6 |
| AffectedBranch | `SSD \| Phoenix \| Inorganic` |
| OldClassification | Granularity `Forest \| Region` |
| CorrectedClassification | Granularity `Forest` only |
| EvidenceObject | `forecast_substrateBE_inorganic_ssd` |
| EvidenceFinding | 133 bare forest aliases, zero Region-Environment composite tokens |
| CorrectionType | BRANCH_APPLICABILITY_CORRECTION |
| SQLUsedForCorrection | 0 |

E6 had inherited Region applicability from the organic PhoenixDB objects. The
inorganic object is forest grain.

```text
E4_GRANULARITY_UNIVERSE_UNCHANGED = YES
E6_BRANCH_APPLICABILITY_CORRECTED = YES
```

The canonical Granularity universe is still `Forest`, `Forest_SKU`, `Region`.
Only this branch's applicability changed.

Trace:
[`E8_upstream_reconciliation.csv`](evidence/E8/E8_upstream_reconciliation.csv).

### RM-E6-CLOSED

```text
RM-E6-CLOSED
Date: 2026-08-17
Roadmap extended: E0-E10 -> E0-E11 (master filename deliberately unchanged)
Scenario canonical values: Consumed | Failover
Scenario applies to: CPU (all routable DB Types), IOPS
Scenario does NOT apply to: HDD, SSD, Memory
Segment canonical values: Consumer | Enterprise
Segment applies to: HDD EDB and HDD All, ORGANIC BRANCH ONLY
Segment does NOT cross HDD Basilisk (three values sum exactly to the object total)
Organic/Inorganic raw values: Organic, Organic_adjust, Organic (Without SubstrateBlobShard), Inorganics, BESTLA
Organic/Inorganic canonical values: Organic | Inorganic
Organic_adjust = PROCESSING_STATE, proven by key-set identity (0 one-sided keys for CPU and IOPS)
Inorganic exists physically, stored as Inorganics
BESTLA = inorganic variant for SSD Phoenix
Applicability matrix cells: 51
Data-required nesting constraints: 17 nodes
Owner-defined UI policy: 14 nodes
Navigation contract: 41 rows (23 show, 6 skip, 1 terminal, 11 unresolved) extended from the E5 baseline of 33
HDD hierarchy: Organic/Inorganic precedes DB Type; Inorganic carries neither DB Type nor Segment
HDD_INORGANIC_DBTYPE_APPLICABILITY = NOT_APPLICABLE
Closure correction: 3 blockers resolved (Organic_adjust key proof, HDD Segment asymmetry, HDD Inorganic DB Type)
CELLS_CLASSIFIED_FROM_OBJECT_NAME = 0
Upstream contradiction: NO_UPSTREAM_UNIVERSE_CONTRADICTION
SQL_EXECUTIONS_USED = 8 / 20 (4 initial + 3 correction + 1 final reconciliation)
HARD_CAP_RESPECTED = YES
OWNER_WAIVER_USED = NO
Open questions: 6
Next stage: E7 Region Universe
```

RM-E1-CLOSED through RM-E5-CLOSED are unchanged.

```text
E6_COMPLETE_AWAITING_AUTHORIZATION
```


## E7 - Region Universe

### Purpose and cost

What is the complete canonical Region universe, how are Regions physically
represented, and do reference tokens match what serving objects actually store?

```text
SQL_EXECUTIONS_USED  = 5 / 12
HARD_CAP_RESPECTED   = YES
SOFT_STOP_TRIGGERED  = NO
OWNER_WAIVER_USED    = NO
```

E4 had proved the counts 173 forests / 35 regions / 6 stripes but never captured
the content. E7 captured it, and in doing so corrected an E4 supporting note.

Ledger: [`E7_query_ledger.csv`](evidence/E7/E7_query_ledger.csv).

### Terminology correction: the embedded token is Environment, not Stripe

E4 recorded that the token embedded in Region values was Stripe, naming
`Go Local`, `Multitenant` and `Gallatin`. The reference dimension disproves it:

```text
Stripe column      = '' , Stripe1, Stripe2, Stripe3, Stripe4, Stripe5
Environment column = BlackForest, Dedicated, GCC Low, Gallatin, Go Local,
                     ITAR DoD, ITAR GCCH, MSIT, Multitenant, SDF, TDF
```

The two are different reference columns with **disjoint value sets**. The token
embedded in every serving Region value comes from `Environment`.

```text
E4_SUPPORTING_NOTE_CORRECTED
NO_E4_GRANULARITY_CONTRADICTION
```

The canonical Granularity universe stays `Forest`, `Forest_SKU`, `Region`. Only
this supporting note changed. Full terminology map:
[`E7_terminology_correction.csv`](evidence/E7/E7_terminology_correction.csv).

### The decomposition rule

```text
ServingRegionValue = UPPER(Region) + '-' + Environment
```

Every one of the 71 serving values is a composite. **None is a bare region code.**

```text
CANONICAL_REGION_COUNT                = 35
PHYSICALLY_ROUTABLE_REGION_COUNT      = 33
NOT_ROUTABLE_YET_COUNT                = 2      (MGMT, SAU)
ENVIRONMENT_COUNT                     = 11
REFERENCE_STRIPE_COUNT                = 6
REGION_ENVIRONMENT_COMBINATION_COUNT  = 73
RAW_SERVING_REGION_VALUES             = 71
```

`REGION_ENVIRONMENT_COMBINATION_COUNT` supersedes the earlier
`REGION_STRIPE_COMBINATION_COUNT` label. The value is unchanged; only the name
was wrong.

The two reference attributes, kept separate:

```text
ENVIRONMENTS     = BlackForest, Dedicated, GCC Low, Gallatin, Go Local,
                   ITAR DoD, ITAR GCCH, MSIT, Multitenant, SDF, TDF
REFERENCE_STRIPE = <blank>, Stripe1, Stripe2, Stripe3, Stripe4, Stripe5
```

### Complete canonical Region universe

| Canonical Region | Environment(s) | Raw physical value(s) | Forests | Routing shape | Status |
|---|---|---|---|---:|---|
| `APC` | DEDICATED, Dedicated, MSIT, Multitenant | `APC-DEDICATED`<br>`APC-Dedicated`<br>`APC-MSIT`<br>`APC-Multitenant` | 7 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `ARE` | GO LOCAL, Go Local | `ARE-GO LOCAL`<br>`ARE-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `AUS` | Go Local | `AUS-Go Local` | 3 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `AUT` | Go Local | `AUT-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `BRA` | Go Local | `BRA-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `CAN` | DEDICATED, Dedicated, Go Local | `CAN-DEDICATED`<br>`CAN-Dedicated`<br>`CAN-Go Local` | 3 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `CHE` | GO LOCAL, Go Local | `CHE-GO LOCAL`<br>`CHE-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `CHL` | Go Local | `CHL-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `CHN` | Gallatin | `CHN-Gallatin` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `DEU` | BlackForest, Go Local | `DEU-BlackForest`<br>`DEU-Go Local` | 2 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `DNK` | GO LOCAL, Go Local | `DNK-GO LOCAL`<br>`DNK-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `ESP` | GO LOCAL, Go Local | `ESP-GO LOCAL`<br>`ESP-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `EUR` | DEDICATED, Dedicated, Go Local, MSIT, Multitenant | `EUR-DEDICATED`<br>`EUR-Dedicated`<br>`EUR-Go Local`<br>`EUR-MSIT`<br>`EUR-Multitenant` | 35 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `FRA` | Go Local | `FRA-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `GBR` | DEDICATED, Dedicated, Go Local | `GBR-DEDICATED`<br>`GBR-Dedicated`<br>`GBR-Go Local` | 4 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `IDN` | GO LOCAL, Go Local | `IDN-GO LOCAL`<br>`IDN-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `IND` | Go Local | `IND-Go Local` | 2 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `ISR` | GO LOCAL, Go Local | `ISR-GO LOCAL`<br>`ISR-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `ITA` | Go Local | `ITA-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `JPN` | Go Local | `JPN-Go Local` | 3 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `KOR` | Go Local | `KOR-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `LAM` | MULTITENANT, Multitenant | `LAM-MULTITENANT`<br>`LAM-Multitenant` | 3 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `MEX` | GO LOCAL, Go Local | `MEX-GO LOCAL`<br>`MEX-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `MGMT` | _reference only_ | _none in any serving object_ | 5 | - | **NOT_ROUTABLE_YET** |
| `MYS` | Go Local | `MYS-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `NAM` | Dedicated, GCC LOW, GCC Low, GCC-LOW, GCC-Low, GO LOCAL, Government, ITAR, ITAR DOD, ITAR DoD, ITAR GCCH, MSIT, Multitenant, SDF, TDF | `NAM-Dedicated`<br>`NAM-GCC LOW`<br>`NAM-GCC Low`<br>`NAM-GCC-LOW`<br>`NAM-GCC-Low`<br>`NAM-GO LOCAL`<br>`NAM-Government`<br>`NAM-ITAR`<br>`NAM-ITAR DOD`<br>`NAM-ITAR DoD`<br>`NAM-ITAR GCCH`<br>`NAM-MSIT`<br>`NAM-Multitenant`<br>`NAM-SDF`<br>`NAM-TDF` | 82 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `NOR` | Go Local | `NOR-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `NZL` | Go Local | `NZL-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `POL` | GO LOCAL, Go Local | `POL-GO LOCAL`<br>`POL-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `QAT` | GO LOCAL, Go Local | `QAT-GO LOCAL`<br>`QAT-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `SAU` | _reference only_ | _none in any serving object_ | 1 | - | **NOT_ROUTABLE_YET** |
| `SGP` | Go Local | `SGP-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `SWE` | GO LOCAL, Go Local | `SWE-GO LOCAL`<br>`SWE-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `TWN` | Go Local | `TWN-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |
| `ZAF` | GO LOCAL, Go Local | `ZAF-GO LOCAL`<br>`ZAF-Go Local` | 1 | REGION_PLUS_STRIPE | PHYSICAL_CONFIRMED |

Universe: [`E7_region_universe.csv`](evidence/E7/E7_region_universe.csv).
Mapping: [`E7_region_stripe_mapping.csv`](evidence/E7/E7_region_stripe_mapping.csv).

### Reference vs serving reconciliation

Verdicts are issued **per source object**, because a family may have several
Region-grain lineages.

| Family | Verdict | Per-object detail |
|---|---|---|
| CPU | `VOCABULARY_VARIES_BY_SOURCE_OBJECT` | `forecast_substrateBE_cpu_region` = VOCABULARY_DIFFERS; `forecast_substrateBE_cpu_byDB_region` = VOCABULARY_IDENTICAL |
| HDD | `VOCABULARY_DIFFERS` | `forecast_substrateBE_hdd_region` = VOCABULARY_DIFFERS |
| SSD | `VOCABULARY_VARIES_BY_SOURCE_OBJECT` | `SubstrateBE_SsdForecastRegion` = VOCABULARY_DIFFERS; `SubstrateBE_Ssd_MCDB_ForecastRegion` = VOCABULARY_DIFFERS; `SubstrateBE_Ssd_PhoenixDB_ForecastRegion` = VOCABULARY_IDENTICAL |
| IOPS | `VOCABULARY_DIFFERS` | `forecast_substrateBE_iops_region` = VOCABULARY_DIFFERS |
| Memory | excluded | E5 and E6 established there is no Region-grain serving route |

```text
REGION_REFERENCE_SERVING_RECONCILIATION = VOCABULARY_DIFFERS
```

#### Every mismatch, verbatim

**19 pairs differ only by case.** HDD is the outlier: it stores 21 uppercase
variants where CPU, IOPS and SSD store title case.

```text
APC-DEDICATED     vs APC-Dedicated
ARE-GO LOCAL      vs ARE-Go Local
CAN-DEDICATED     vs CAN-Dedicated
CHE-GO LOCAL      vs CHE-Go Local
DNK-GO LOCAL      vs DNK-Go Local
ESP-GO LOCAL      vs ESP-Go Local
EUR-DEDICATED     vs EUR-Dedicated
GBR-DEDICATED     vs GBR-Dedicated
IDN-GO LOCAL      vs IDN-Go Local
ISR-GO LOCAL      vs ISR-Go Local
LAM-MULTITENANT   vs LAM-Multitenant
MEX-GO LOCAL      vs MEX-Go Local
NAM-GCC LOW       vs NAM-GCC Low
NAM-GCC-LOW       vs NAM-GCC-Low
NAM-ITAR DOD      vs NAM-ITAR DoD
POL-GO LOCAL      vs POL-Go Local
QAT-GO LOCAL      vs QAT-Go Local
SWE-GO LOCAL      vs SWE-Go Local
ZAF-GO LOCAL      vs ZAF-Go Local
```

A **separator** difference also exists: `NAM-GCC Low` versus `NAM-GCC-Low`.

Six serving values have no reference pair:

```text
EUR-GO LOCAL      NAM-GCC-LOW       NAM-GCC-Low
NAM-GO LOCAL      NAM-Government    NAM-ITAR
```

Two reference regions have **no serving token at all**:

```text
MGMT   (1 forest)   -> NOT_ROUTABLE_YET
SAU    (1 forest)   -> NOT_ROUTABLE_YET
```

Nothing was normalised. Every variant is preserved verbatim in
[`E7_region_aliases.csv`](evidence/E7/E7_region_aliases.csv) and
[`E7_region_vocabulary_reconciliation.csv`](evidence/E7/E7_region_vocabulary_reconciliation.csv).

### Routing contract

```text
CanonicalRegion != PhysicalRoutingValue
```

A UI may display `NAM` with Environment `GCC Low`, but no query can filter on
either alone. The physical predicate must be the full composite token, and the
correct casing depends on which object is being read:

```text
DISPLAY            NAM + GCC Low
PHYSICAL ROUTING   NAM-GCC Low | NAM-GCC LOW | NAM-GCC-Low
                   depending on the source object
```

`CanonicalRegion + Environment` therefore defines the **logical** decomposition,
but it cannot be reconstructed into one universally valid serving token. No
normalized token is declared universally correct.

`PhysicalRoutingValue` is always taken from the serving object, never from the
reference dimension. `MGMT` and `SAU` are marked `NOT_ROUTABLE_YET` rather than
presented as selectable.

Contract:
[`E7_region_routing_contract.csv`](evidence/E7/E7_region_routing_contract.csv).

### Region-like false positives

| Candidate | Why it is not a Region |
|---|---|
| `Stripe` | Internal partition attribute `<blank>`, `Stripe1`..`Stripe5`. It is **not** the token embedded in Region values |
| `CentralAdminRegion` | Administrative attribute with the same cardinality as Region |
| `Forest` | A finer canonical Granularity already closed in E4 |
| `DAG` | Closed in E4 as a separate actuals-layer axis |
| `Geo`, `Site`, `Cluster` | Do not exist in scope |

Evidence:
[`E7_region_false_positives.csv`](evidence/E7/E7_region_false_positives.csv).

### UI implication, declarative only

When `Granularity = Region`, the Region selector becomes available:

```text
Granularity = Region
  -> CanonicalRegion
     -> Environment context
        -> exact PhysicalRoutingValue
```

E7 supplies the canonical universe of 35 regions; **E8 will restrict it per
branch**. Do not assume every region appears for every branch, and never build a
predicate from a canonical code alone.

Environment is classified as:

```text
Environment = PHYSICAL_ROUTING_DIMENSION_CONFIRMED
UI_FILTER_STATUS = NOT_DECIDED
```

E7 does **not** promote Environment to a standalone visible filter. That is an
owner or later-stage design decision.

### Validation

All 64 checks pass, including 5/12 SQL executions, no branch crossing, and no
silent normalization.

Evidence: [`E7_validation.csv`](evidence/E7/E7_validation.csv).

### RM-E7-CLOSED

```text
RM-E7-CLOSED
Date: 2026-08-17
CANONICAL_REGION_COUNT = 35
Canonical Regions: APC, ARE, AUS, AUT, BRA, CAN, CHE, CHL, CHN, DEU, DNK, ESP, EUR, FRA, GBR, IDN, IND, ISR, ITA, JPN, KOR, LAM, MEX, MGMT, MYS, NAM, NOR, NZL, POL, QAT, SAU, SGP, SWE, TWN, ZAF
PHYSICALLY_ROUTABLE_REGION_COUNT = 33
NOT_ROUTABLE_YET = MGMT, SAU
ENVIRONMENT_COUNT = 11
ENVIRONMENTS = BlackForest, Dedicated, GCC Low, Gallatin, Go Local, ITAR DoD, ITAR GCCH, MSIT, Multitenant, SDF, TDF
REFERENCE_STRIPE_COUNT = 6
REFERENCE_STRIPE_VALUES = <blank>, Stripe1, Stripe2, Stripe3, Stripe4, Stripe5
REGION_ENVIRONMENT_COMBINATION_COUNT = 73
DECOMPOSITION_RULE = UPPER(Region) + '-' + Environment
RAW_SERVING_REGION_VALUES = 71
Environment != Stripe
PhysicalRoutingValue is source-object-specific
Alias groups (case variants): 19
Unmapped values: 6
CPU_REGION_VOCABULARY = VOCABULARY_VARIES_BY_SOURCE_OBJECT
HDD_REGION_VOCABULARY = VOCABULARY_DIFFERS
SSD_REGION_VOCABULARY = VOCABULARY_VARIES_BY_SOURCE_OBJECT
IOPS_REGION_VOCABULARY = VOCABULARY_DIFFERS
REGION_REFERENCE_SERVING_RECONCILIATION = VOCABULARY_DIFFERS
CanonicalRegion alone is NOT a safe physical predicate
E4_SUPPORTING_NOTE_CORRECTED
NO_E4_GRANULARITY_CONTRADICTION
NO_UPSTREAM_UNIVERSE_CONTRADICTION
SQL_EXECUTIONS_USED = 5 / 12
HARD_CAP_RESPECTED = YES
SOFT_STOP_TRIGGERED = NO
OWNER_WAIVER_USED = NO
Open questions: 6
Next stage: E8 Branch x Region
```

RM-E1-CLOSED through RM-E6-CLOSED are unchanged.

```text
E7_COMPLETE_AWAITING_AUTHORIZATION
```


## E8 - Branch x Region

### Purpose and cost

For every Region-capable branch, which canonical Regions physically exist and
what exact serving tokens represent them?

```text
SQL_EXECUTIONS_USED  = 7 / 10
HARD_CAP_RESPECTED   = YES
SOFT_STOP_TRIGGERED  = YES (query 7 was closure-critical only)
OWNER_WAIVER_USED    = NO
```

The roster was frozen locally from the E5 and E6 contracts **before any SQL**,
producing 18 Region-capable paths, exactly matching the provisional expectation.
Seven queries then covered all 18 branches by grouping on source object rather
than querying per branch, and two SSD objects were reused from E7 with zero SQL
because E2 had already proved them 1:1.

Ledger: [`E8_query_ledger.csv`](evidence/E8/E8_query_ledger.csv).

### Branch roster

```text
DERIVED_REGION_PATHS_FROM_PRE_E8_CONTRACT = 18
REGION_CAPABLE_BRANCH_COUNT               = 17
ROUTABLE_BRANCH_COUNT                     = 16
SERVING_EMPTY_BRANCH_COUNT                = 1
UNRESOLVED_BRANCH_COUNT                   = 0
```

The 17 Region-capable branches are **16 routable plus 1 serving-empty**. Being
Region-capable means physical Region evidence exists; being routable means the
product can actually serve it.

One path was reclassified on E8 evidence:
`SSD|Phoenix|Inorganic|Region` has **no Region-grain serving route**.
`forecast_substrateBE_inorganic_ssd` stores 133 bare forest aliases such as
`GBRP302` and `NAMPRD12`, with no Region-Environment composite. E6 had inherited
the grain set from the organic PhoenixDB objects; the inorganic object is forest
grain only.

```text
REGION_NOT_APPLICABLE_BRANCHES = 3
  SSD|Phoenix|Inorganic   (corrected by E8: Forest grain only)
  CPU|Basilisk            (LABEL_ONLY)
  Memory                  (no Granularity axis)
```

`SSD | Phoenix | Inorganic` is therefore **not** merely reduced Region coverage.
Its valid path is:

```text
SSD -> Phoenix -> Inorganic -> Forest        VALID
SSD -> Phoenix -> Inorganic -> Region        INVALID
```

This is an upstream **branch-applicability correction**, recorded as
`E6_POSTCLOSE_CORRECTION_FROM_E8`. The canonical Granularity universe is
unchanged.

### Complete branch table

| Branch | Regions | Environments | Physical tokens | Missing vs global 33 | Serving status | Sibling relation | Status |
|---|---:|---:|---:|---|---|---|---|
| `CPU|Basilisk|Region` | - | - | - | - | LABEL_ONLY | n/a | NOT_APPLICABLE |
| `CPU|NonPhoenix|Consumed|Region` | 32 | 10 | 44 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `CPU|NonPhoenix|Failover|Region` | 32 | 10 | 44 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `CPU|Phoenix|Consumed|Region` | 32 | 10 | 44 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `CPU|Phoenix|Failover|Region` | 32 | 10 | 44 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `CPU|Total|Consumed|Region` | 32 | 12 | 46 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `CPU|Total|Failover|Region` | 32 | 12 | 46 | DNK | ROUTABLE | identical across all 6 CPU branches | PHYSICAL_CONFIRMED |
| `HDD|Inorganic|Region` | 33 | 10 | 46 | — | ROUTABLE | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `HDD|Organic|All|Consumer|Region` | 33 | 16 | 52 | — | ROUTABLE | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `HDD|Organic|All|Enterprise|Region` | 33 | 19 | 74 | — | ROUTABLE | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `HDD|Organic|Basilisk|Region` | 33 | 10 | 46 | — | SERVING_EMPTY | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `HDD|Organic|EDB|Consumer|Region` | 33 | 15 | 52 | — | ROUTABLE | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `HDD|Organic|EDB|Enterprise|Region` | 33 | 17 | 52 | — | ROUTABLE | identical across all HDD branches | PHYSICAL_CONFIRMED |
| `IOPS|Consumed|Region` | 33 | 11 | 46 | — | ROUTABLE | identical Consumed vs Failover | PHYSICAL_CONFIRMED |
| `IOPS|Failover|Region` | 33 | 11 | 46 | — | ROUTABLE | identical Consumed vs Failover | PHYSICAL_CONFIRMED |
| `Memory|Region` | - | - | - | - | NOT_APPLICABLE | n/a | NOT_APPLICABLE |
| `SSD|Legacy|Organic|Region` | 24 | 8 | 32 | AUT|CHL|CHN|DNK|ESP|IDN|MYS|NZL|TWN | ROUTABLE | differs by branch | PHYSICAL_CONFIRMED |
| `SSD|MCDB|Organic|Region` | 25 | 12 | 41 | AUT|CHL|CHN|DNK|IDN|MYS|NZL|TWN | ROUTABLE | differs by branch | PHYSICAL_CONFIRMED |
| `SSD|Phoenix|Inorganic|Region` | 0 | 0 | 133 | APC|ARE|AUS|AUT|BRA|CAN|CHE|CHL|CHN|DEU|DNK|ESP|EUR|FRA|GBR|IDN|IND|ISR|ITA|JPN|KOR|LAM|MEX|MYS|NAM|NOR|NZL|POL|QAT|SGP|SWE|TWN|ZAF | ROUTABLE | differs by branch | PHYSICAL_CONFIRMED |
| `SSD|Phoenix|Organic|Region` | 25 | 7 | 35 | AUT|CHL|CHN|DNK|IDN|MYS|NZL|TWN | ROUTABLE | differs by branch | PHYSICAL_CONFIRMED |

Full matrix, 790 rows with every Region and every token per branch:
[`E8_branch_region_matrix.csv`](evidence/E8/E8_branch_region_matrix.csv).

### Region coverage is not uniform

```text
HDD  (6 branches)  33 regions   complete global routable coverage
IOPS (2 branches)  33 regions   complete global routable coverage
CPU  (6 branches)  32 regions   missing MEX
SSD  MCDB          25 regions
SSD  Phoenix       25 regions
SSD  Legacy        24 regions
```

Two consistent gaps stand out. **Every CPU branch is missing exactly one region**,
and **SSD coverage is materially narrower** than CPU, HDD and IOPS. Both are
recorded as open questions rather than explained away.

### Sibling comparison, computed locally with zero extra SQL

Nine of ten sibling pairs are **IDENTICAL**:

```text
CPU Phoenix        Consumed vs Failover    IDENTICAL
CPU NonPhoenix     Consumed vs Failover    IDENTICAL
CPU Total          Consumed vs Failover    IDENTICAL
IOPS               Consumed vs Failover    IDENTICAL
HDD Organic EDB    Consumer vs Enterprise  IDENTICAL
HDD Organic All    Consumer vs Enterprise  IDENTICAL
HDD Consumer       EDB vs All              IDENTICAL
CPU Consumed       Phoenix vs NonPhoenix   IDENTICAL
CPU Consumed       by-DB vs Total          IDENTICAL
SSD Phoenix        Organic vs Inorganic    NOT_COMPARABLE
```

The SSD Phoenix pair is a **GRANULARITY_APPLICABILITY_DIFFERENCE**, not reduced
Region coverage: Organic has a Region-grain route and Inorganic has Forest grain
only.

So the answer to the practical questions is clean:

- **Scenario does not change CPU region coverage** for Phoenix, NonPhoenix or Total.
- **Scenario does not change IOPS region coverage.**
- **Segment does not change HDD region coverage.**
- SSD Phoenix Organic versus Inorganic is not comparable, because Inorganic has
  no Region-grain route at all.

Evidence:
[`E8_sibling_region_set_comparison.csv`](evidence/E8/E8_sibling_region_set_comparison.csv).

### The routing problem gets worse, not better

```text
MULTI_TOKEN_REGION_CAPABLE_BRANCH_COUNT = 17
MULTI_TOKEN_ROUTABLE_BRANCH_COUNT       = 16
```

**Every Region-capable branch** has at least one canonical Region that resolves
to **multiple physical tokens**. E7 found 19 casing-variant groups; E8 found
**61 further token variants** absent from E7, including a third casing
convention inside the HDD organic column:

```text
che-Go Local      beside   GBR-Go Local        (same column, same object)
apc-Dedicated     beside   APC-DEDICATED
nam-ITAR GCCH     beside   NAM-ITAR GCCH
```

27 lowercase and 33 uppercase region prefixes coexist in the HDD organic
lineage. Nothing was normalised.

```text
CanonicalRegion alone cannot be converted to one universal physical token.
CONFIRMED from branch evidence, not only from E7.
```

Tokens: [`E8_branch_region_physical_tokens.csv`](evidence/E8/E8_branch_region_physical_tokens.csv).
Anomalies: [`E8_region_coverage_anomalies.csv`](evidence/E8/E8_region_coverage_anomalies.csv).

### MGMT and SAU

```text
MGMT: NOT routable on any branch
SAU:  NOT routable on any branch
```

E7's `NOT_ROUTABLE_YET` classification is confirmed, not overturned.

### Serving-empty branch

`HDD|Organic|Basilisk|Region` has 33 canonical Regions with physical evidence,
but its demand views are `WHERE 1=0`.

```text
PHYSICAL_REGION_DATA_EXISTS = YES
SERVING_REGION_DATA_EXISTS  = NO
UI_REGION_ROUTING           = NOT_AVAILABLE
```

Its Regions must not be exposed.

### UI consequence, declarative only

The Region selector must be restricted to the **branch-specific** set, never the
global 35. A CPU branch offers 32 regions; an SSD Legacy branch offers 24.
Selection must route using the exact serving token for that branch and object.
Environment remains `PHYSICAL_ROUTING_DIMENSION_CONFIRMED` with
`UI_FILTER_STATUS = NOT_DECIDED`.

### Validation

All 52 checks pass, including 7/10 SQL executions, no Key discovery, no Source
Table selection, and no silent normalization.

Evidence: [`E8_validation.csv`](evidence/E8/E8_validation.csv).

### RM-E8-CLOSED

```text
RM-E8-CLOSED
Date: 2026-08-17
DERIVED_REGION_PATHS_FROM_PRE_E8_CONTRACT = 18
REGION_CAPABLE_BRANCH_COUNT = 17
ROUTABLE_BRANCH_COUNT = 16
SERVING_EMPTY_BRANCH_COUNT = 1
UNRESOLVED_BRANCH_COUNT = 0
REGION_NOT_APPLICABLE_BRANCHES = SSD|Phoenix|Inorganic, CPU|Basilisk, Memory
Branches with all 33 globally routable regions: 8 (all HDD branches and both IOPS branches)
Reduced coverage: CPU 32 regions on all six branches; SSD MCDB 25; SSD Phoenix 25; SSD Legacy 24
SERVING_EMPTY: HDD|Organic|Basilisk|Region
REGION_NOT_APPLICABLE_CORRECTION = SSD|Phoenix|Inorganic
SSD_PHOENIX_INORGANIC_GRANULARITY = Forest only
MGMT: not routable on any branch
SAU: not routable on any branch
Sibling comparison: 9 of 10 pairs IDENTICAL; SSD Phoenix Organic vs Inorganic NOT_COMPARABLE
CPU Scenario does not change region coverage
IOPS Scenario does not change region coverage
HDD Segment does not change region coverage
MULTI_TOKEN_REGION_CAPABLE_BRANCH_COUNT = 17
MULTI_TOKEN_ROUTABLE_BRANCH_COUNT = 16
New physical token variants absent from E7: 61
Regions outside the canonical 35: 0
NO_UPSTREAM_CANONICAL_UNIVERSE_CONTRADICTION
E4_GRANULARITY_UNIVERSE_UNCHANGED
E6_BRANCH_APPLICABILITY_CORRECTED
SQL_EXECUTIONS_USED = 7 / 10
ADDITIONAL_SQL_FOR_RECONCILIATION = 0
HARD_CAP_RESPECTED = YES
SOFT_STOP_TRIGGERED = YES
OWNER_WAIVER_USED = NO
Open questions: 5
Next stage: E9 Key
```

RM-E1-CLOSED through RM-E7-CLOSED are unchanged.

```text
E8_COMPLETE_AWAITING_AUTHORIZATION
```


## E9 - Key Semantics

### Purpose and cost

What does "Key" logically mean on each branch, and does a selectable Key axis
actually exist there?

```text
SQL_EXECUTIONS_USED  = 3 / 10
HARD_CAP_RESPECTED   = YES
SOFT_STOP_TRIGGERED  = NO
OWNER_WAIVER_USED    = NO
```

The candidate roster was frozen locally first: 26 rows, of which **10 needed no
SQL at all** because E7 and E8 had already enumerated their columns as Region
tokens. One 173-row query on the forest dimension then resolved almost everything
else locally.

Ledger: [`E9_query_ledger.csv`](evidence/E9/E9_query_ledger.csv).

### The headline answer

```text
NO_GLOBAL_KEY_UNIVERSE
```

**There is no independent logical Key axis on any branch.** Every physical column
named `Key` or `MyKey` holds a dimension that is already modelled.

| Granularity | What `Key` / `MyKey` actually contains | Semantic role |
|---|---|---|
| Region | `NAM-Multitenant`, `CAN-Go Local` | REGION_ROUTING_TOKEN |
| Forest | `NAMPRD07`, `NAMP134`, `GBRP302` | FOREST_IDENTIFIER |
| Forest_SKU (CPU, IOPS) | `NAMP131-WCS Gen6` | FOREST_SKU_COMPOSITE |
| Forest_SKU (SSD) | `NAM-Multitenant-NAMPRD08-WCS Gen7` | COMPOSITE_ROUTING_TOKEN |

Nine Region-grain source families were classified `REGION_ROUTING_TOKEN`. Naming
a column `Key` proved nothing.

Classification:
[`E9_key_semantic_classification.csv`](evidence/E9/E9_key_semantic_classification.csv).

### NAMPRD07

```text
NAMPRD07 = FOREST_IDENTIFIER
```

It is alias `namprd07` in `vw_SubstrateBE_Forests_V2`, mapping to Region `NAM`
and Environment `Multitenant`. It is **not** an arbitrary key.

This matters for the UI: showing `Region = NAM` and `Key = NAMPRD07` as
independent selections would present the same hierarchy twice, because the forest
already determines its region.

Note the casing pattern repeats from E7: all 173 reference aliases are stored
**lowercase**, while every serving object stores **uppercase**.

### LVNE and LVWE

```text
LVNE and LVWE are NOT Key values
```

They appear only as **object-name tokens** on two forecast-accuracy objects,
`forecast_substrateBE_ssd_phx_lvne_metrics` and `..._lvwe_metrics`. They are
never a column name and never a value anywhere in the evidence base.

Each object's `Key` column holds **60 Forest aliases**, and the two sets are
**identical**. They were preserved as distinct objects and were not merged,
averaged or collapsed. Their business meaning stays an open question.

### Composite decomposition

```text
NAMP131-WCS Gen6                    = Forest + SKU
APCPRD02-HP Gen8                    = Forest + SKU
NAM-Multitenant-NAMPRD03            = Region + Environment + Forest
NAM-Multitenant-NAMPRD08-WCS Gen7   = Region + Environment + Forest + SKU
```

The SSD four-part composite packs four already-modelled dimensions into one
column. It must **not** be exposed as one opaque Key, because doing so would hide
the SKU dimension behind string parsing.

### SKU

```text
SKU_PHYSICAL_DIMENSION = CONFIRMED
KEY_DEPENDS_ON_SKU     = YES, at Forest_SKU granularity for CPU, IOPS and SSD
UI_FILTER_STATUS       = NOT_DECIDED
```

SKU is necessary to uniquely identify a Forest_SKU selection, so it was not
hidden inside a normalised Key. It was also not promoted to a visible axis.

### Applicability by branch

| Grain | Branches | Applicability |
|---|---:|---|
| Region | 10 | INHERENT_IN_GRANULARITY |
| Forest | 5 | INHERENT_IN_GRANULARITY |
| Forest_SKU | 4 | COMPOSITE_WITH_OTHER_AXIS |
| HDD Basilisk | 1 | SERVING_EMPTY |
| CPU Basilisk, Memory | 2 | NOT_APPLICABLE |

Matrix:
[`E9_key_applicability_matrix.csv`](evidence/E9/E9_key_applicability_matrix.csv).

### Parent relationships

```text
Key spans multiple Regions?      NO   173 forests -> 35 regions, zero multi-region forests
Region contains multiple Keys?   YES  MANY_KEYS_PER_REGION at Forest and Forest_SKU grain
```

Reused from E4 and E7 rather than rediscovered.

### Navigation consequence, declarative only

```text
Granularity = Region      -> Key SKIPPED: the physical key is the Region already chosen
Granularity = Forest      -> Key SKIPPED as an independent axis: the Forest alias IS the value
Granularity = Forest_SKU  -> a SKU choice completes the identifier;
                             the composite must not be exposed as one opaque Key
```

**No Key dropdown is added to any branch.** Building one would have manufactured a
filter over data that is really Region, Forest, or Forest plus SKU.

### Validation

All 33 checks pass, including 3/10 SQL executions, no brute-force scan on any
object above 50M rows, and no silent normalization.

Evidence: [`E9_validation.csv`](evidence/E9/E9_validation.csv).

### RM-E9-CLOSED

```text
RM-E9-CLOSED
Date: 2026-08-17
Universal logical Key axis: NONE. NO_GLOBAL_KEY_UNIVERSE
Semantic classes found: REGION_ROUTING_TOKEN, FOREST_IDENTIFIER,
                        FOREST_SKU_COMPOSITE, COMPOSITE_ROUTING_TOKEN
Key/MyKey columns that are actually Region: 9 source families
Key/MyKey columns that are actually Forest: 7 columns
Forest semantics: the Forest alias is the granularity value, not a separate Key
Forest_SKU semantics: Forest + SKU for CPU and IOPS; Region + Environment + Forest + SKU for SSD
NAMPRD07 = FOREST_IDENTIFIER, alias namprd07 -> Region NAM, Environment Multitenant
LVNE / LVWE = object-name tokens on two accuracy objects; Key columns hold 60 identical Forest aliases
SKU_PHYSICAL_DIMENSION = CONFIRMED; UI_FILTER_STATUS = NOT_DECIDED
Independent logical Key branches: 0
Key parent cardinality: MANY_KEYS_PER_REGION; no key spans multiple regions
Reference vs serving: forest aliases lowercase in reference, uppercase in serving
REFERENCE_ONLY_KEYS = 0; SERVING_ONLY_KEYS = 0 for forest aliases
New canonical taxonomy axis discovered: NONE
NO_UPSTREAM_CANONICAL_UNIVERSE_CONTRADICTION
SQL_EXECUTIONS_USED = 3 / 10
HARD_CAP_RESPECTED = YES
SOFT_STOP_TRIGGERED = NO
OWNER_WAIVER_USED = NO
Open questions: 5
Next stage: E10 Source Table
```

RM-E1-CLOSED through RM-E8-CLOSED are unchanged.

```text
E9_COMPLETE_AWAITING_AUTHORIZATION
```


## PRE_E10_CONSOLIDATED_TAXONOMY_GENERATED

Consolidation of E1 through E9 into a single owner-facing view, ahead of E10.

```text
ADDITIONAL_SQL = 0
E10_STARTED    = NO
```

No closed conclusion from E1 to E9 was altered.

| Artifact | Content |
|---|---|
| [`AEGIS_Complete_Taxonomy_E1_E9.md`](AEGIS_Complete_Taxonomy_E1_E9.md) | Complete 14-section view |
| [`AEGIS_Complete_Taxonomy_E1_E9.csv`](AEGIS_Complete_Taxonomy_E1_E9.csv) | Canonical long-form view, 1,116 rows |
| [`AEGIS_Complete_Taxonomy_E1_E9_Gaps.csv`](evidence/E9/AEGIS_Complete_Taxonomy_E1_E9_Gaps.csv) | 20 explicit gaps |

Headline result:

```text
PHYSICAL_CONFIRMED                    877
REFERENCE_MAPPED                      173
SERVING_EMPTY                          46
STRUCTURALLY_VALID_NOT_MATERIALIZED    18
```

Region grain is fully enumerated. Forest grain is **materialized on only one branch out of
seventeen**: `SSD|Phoenix|Inorganic` with 133 forests. Scenario x Forest remains `STRUCTURAL_ONLY`
and was not inferred from equal Region coverage.

> **PRE-COMPLETION HISTORICAL STATE.** The counters above describe the state before the PRE-E10
> pair-coverage completion pass. See `PRE_E10_PAIR_COVERAGE_COMPLETE` below for the current state:
> 19 of 19 Forest-capable branches materialized and 7,501 consolidated rows.

```text
PRE_E10_TAXONOMY_CONSOLIDATION_COMPLETE_WITH_GAPS_AWAITING_AUTHORIZATION
```

---

## PRE_E10_PAIR_COVERAGE_COMPLETE

**Status: `PRE_E10_FINAL_DOCUMENTATION_RECONCILIATION_COMPLETE_AWAITING_AUTHORIZATION`**

Pair-coverage completion plus final documentation reconciliation. Not E10, not E9.1, not a new
stage. E1 through E9 remain CLOSED. No canonical source table was selected.

### Final counters

| Counter | Value |
|---|---|
| `ORIGINAL_GAPS` | 20 |
| `RESOLVED_GAPS` | 20 |
| `REMAINING_GAPS` | 0 |
| `FOREST_CAPABLE_SERVING_BRANCHES` | 19 |
| `FOREST_BRANCHES_FULLY_MATERIALIZED` | 19 |
| `SCENARIO_BRANCHES` | 8 |
| `SCENARIO_BRANCHES_FULLY_MATERIALIZED` | 8 |
| `REFERENCE_FOREST_COUNT` | 173 |
| `SERVING_FOREST_UNIQUE_COUNT` | 164 |
| `SERVING_FOREST_OUTSIDE_REFERENCE_COUNT` | 4 |
| `GLOBAL_OBSERVED_SKU_COUNT` | 9 |
| `GLOBAL_UNIQUE_OBSERVED_FOREST_SKU_COMBINATIONS` | 714 |
| `GLOBAL_UNIQUE_FOREST_SKU_GRAIN_ROUTING_TOKENS` | 873 |
| `TOTAL_CONSOLIDATED_ROWS` | 7,501 |
| `SQL_EXECUTIONS_USED` | 8 |
| `ADDITIONAL_SQL_FOR_FINAL_RECONCILIATION` | 0 |
| `OVER_50M_EXCEPTION_COUNT` | 3 |
| `SQL_FAILURES` | 0 |
| `SQL_FALLBACKS` | 0 |
| `TRUNCATED_VOCABULARIES` | 0 |
| `NAMPRD07_SERVING_BRANCH_COUNT` | 19 |
| `PAIR_COVERAGE_STATUS` | FULLY_MATERIALIZED |

### >50M controlled exceptions

- `SubstrateBE_DemandForecast_CPU_Forest` - 51,194,194 rows, MetricName, GranularityValue, 7.9s, 1428 returned, complete vocabulary YES, fallback NO
- `SubstrateBE_DemandForecast_HDD_EDB_Forest` - 53,918,789 rows, MetricName, GranularityValue, 10.8s, 791 returned, complete vocabulary YES, fallback NO
- `forecast_substrateBE_hdd` - 53,922,502 rows, data_type, forest_name, 2.8s, 791 returned, complete vocabulary YES, fallback NO

### Findings preserved

1. **Scenario does not discriminate membership.** Consumed and Failover are identical across all
   four scenario-bearing families, in Forest, SKU and Forest_SKU combinations.
2. **In HDD neither segment nor route changes coverage.** Consumer, Enterprise, the EDB route and
   the All route share the same 162 Forests.
3. **The staging object was not representative.** Query P08 against the real serving object
   prevented declaring a partial coverage complete.
4. **Physical token shapes are positional and proven** by separator counting.
5. **4 serving Forests outside the reference
   universe**, classified `SERVING_FOREST_OUTSIDE_REFERENCE`, not added to the
   173.
6. **Basilisk exposes 155 physical Forests but stays
   `SERVING_EMPTY`** and is not exposed as routable.
7. **Eighth occurrence of the casing pattern** in the HDD discriminators.
8. **SSD MCDB Forest (154) is a strict subset of its Forest_SKU
   (162)**, so identical Region sets do not imply identical Forest
   sets.
9. **SSD Phoenix Organic = 144**, **Inorganic =
   133**, separate physical branches; Inorganic keeps Region
   `NOT_APPLICABLE`.

### Documentation correction applied

The global Forest x SKU count had been documented as a single ambiguous number. It is now split
into `GLOBAL_UNIQUE_OBSERVED_FOREST_SKU_COMBINATIONS` = 714 and
`GLOBAL_UNIQUE_FOREST_SKU_GRAIN_ROUTING_TOKENS` = 873, the difference being the 159
`SSD|MCDB|Organic|Forest_SKU` tokens with no SKU component. The >50M exception count was also
corrected to 3, along with the SKU axis status and the Section 3
trees.

---

## RM-E10-CLOSED - CANONICAL SERVING SOURCE CONTRACT

**Status: `E10_COMPLETE_AWAITING_AUTHORIZATION`**

E10 answered, for every final taxonomy route, which physical object serves the forecast and which
columns are required to read it correctly.

### Counters

| Counter | Value |
|---|---|
| `E10_TOTAL_ROUTES` | 38 |
| `ROUTABLE_SOURCE_ROUTES` | 34 |
| `SELECTED_SOURCE_ROUTES` | 34 |
| `AMBIGUOUS_SOURCE_ROUTES` | 0 |
| `UNIQUE_SELECTED_SOURCE_OBJECTS` | 20 |
| `SERVING_EMPTY_ROUTES` | 2 |
| `LABEL_ONLY_OR_NOT_APPLICABLE_ROUTES` | 2 |
| `FORECAST_VALUE_RESOLVED_ROUTES` | 34 |
| `TARGET_PERIOD_RESOLVED_ROUTES` | 34 |
| `FORECAST_CYCLE_RESOLVED_ROUTES` | 30 |
| `ACCURACY_READY_ROUTES` | 30 |
| `DRIFT_READY_ROUTES` | 29 |
| `SQL_EXECUTIONS_USED` | 5 / 8 |
| `HARD_CAP_RESPECTED` | YES |
| `E1_E9_CHANGED` | NO |

### The three schema families

The E1 column inventory revealed that the 20 serving objects belong to three families, and the
forecast contract changes with the family:

| Family | Value | Target period | Forecast cycle | Objects |
|---|---|---|---|---|
| A | `Value` | `Datetime` / `DateTime` | `ForecastVersion` | 14 |
| B | `Value` | `DataDate` | `ForecastRunId` | 5 |
| C | `forecast_mean` | `target_date` | `write_time` | 1 |

In family A, `ValueType` turned out to be the constant `Forecast-Mean` (E10Q2), so no extra
predicate is needed to separate forecast from actual.

### Critical finding: four routes cannot support drift

`ForecastRunId` **is not always a forecast cycle**. E10Q5 proved that in two objects the number of
distinct values equals the row count exactly:

```text
SubstrateBE_DemandForecast_CPU_Forest    COUNT(*) = 51,194,194 = COUNT(DISTINCT ForecastRunId)
SubstrateBE_DemandForecast_IOPS_Forest   COUNT(*) = 32,620,690 = COUNT(DISTINCT ForecastRunId)
```

There it is a **per-row identifier**, not a run. Those objects expose no other vintage dimension,
so the following four routes are `ForecastCycleSemantic = NOT_PRESENT` and **cannot support
drift**:

- `CPU|Total|Consumed|Forest_SKU`
- `CPU|Total|Failover|Forest_SKU`
- `IOPS|Consumed|Forest_SKU`
- `IOPS|Failover|Forest_SKU`

In the other three family-B objects the same field is a genuine run: 560 in
`SubstrateBE_DemandForecast_HDD_EDB_Forest`, 50 in `..._HDD_EDB_Region`, 14 in
`..._Ssd_MCDB_ForestSKU`.

### Second finding: one route has a single current snapshot

`forecast_substrateBE_inorganic_ssd` has a single `ForecastVersion` (2024-07-23), so
`SSD|Phoenix|Inorganic|Forest` is `SINGLE_CURRENT_SNAPSHOT`: usable for accuracy against a known
vintage, but not for drift.

### Third finding: the HDD family-C cycle

`forecast_substrateBE_hdd` exposes two plausible datetime columns. E10Q4 measured
`execution_time` at 30,998 distinct values, `write_time` at 606 and `target_date` at 4,260.
`write_time` was selected because its cardinality matches the order of the 560 `ForecastRunId`
values on the sibling EDB route, while `execution_time` is far too granular for a publication
cycle. Confidence **MEDIUM**; `execution_time` is retained as a documented alternative.

### Selection decisions preserved

- `forecast_substrateBE_hdd_staging` **rejected** on both HDD All Forest routes, applying the
  PRE-E10 lesson: staging lacks the discriminator case variants present in production.
- `SubstrateBE_DemandForecast_Ssd_MCDB_ForestSKU` serves **Forest** grain and
  `SubstrateBE_Ssd_MCDB_ForecastForestSKU` serves **Forest_SKU** grain, despite what their names
  suggest. Content was honoured over naming.
- `HDD|Organic|Basilisk` on both grains: `SERVING_EMPTY_NO_ROUTABLE_SOURCE`.
- `CPU|Basilisk|Region`: `NOT_APPLICABLE_LABEL_ONLY`. `Memory|Region`: `NOT_APPLICABLE`.
- `SSD|Phoenix|Inorganic` remains Forest-grain only, Region `NOT_APPLICABLE`.

---

## E11_ELIGIBILITY_PROFILING_COMPLETE

**Status: `E11_ELIGIBILITY_PROFILING_COMPLETE_AWAITING_OWNER_POLICY`**

Analytical eligibility profiling. E1 through E10 remain CLOSED and unchanged. No final manifest
and no production artifacts were created.

| Counter | Value |
|---|---:|
| `TOTAL_LOGICAL_LEAF_CASES` | 6,383 |
| `ACTUALS_SOURCE_RESOLVED_LEAVES` | 5,887 |
| `LEAVES_WITH_ACTUAL_DATA` | 5,438 |
| `NO_DATA_LEAVES` | 449 |
| `ACTUALS_SOURCE_UNRESOLVED_LEAVES` | 496 |
| `HISTORY_GE30` | 5,432 |
| `HISTORY_GE60` | 5,428 |
| `HISTORY_GE90` | 5,420 |
| `HISTORY_GE120` | 5,415 |
| `HISTORY_GE150` | 5,406 |
| `PROVISIONAL_RECENT_LEAVES` | 4,681 |
| `PROVISIONAL_STALE_LEAVES` | 757 |
| `HISTORY_GE90_AND_PROVISIONAL_RECENT` | 4,681 |
| `SQL_EXECUTIONS_USED` | 6 / 16 |
| `FINAL_HISTORY_THRESHOLD_SELECTED` | NO |
| `FINAL_RECENCY_POLICY_SELECTED` | NO |
| `FINAL_ANALYTICAL_MANIFEST_CREATED` | NO |
| `PRODUCTION_ARTIFACTS_CREATED` | NO |

### Actuals source

`SubstrateBE_M2CP_Demand_History`, 1.18M rows, period column `datadate`, **DAILY** measured
cadence (2,600 periods between 2019-07-01 and 2026-08-16). It is distinct from the 20 E10
forecast sources: the actuals and forecast contracts are independent.

`ObservationCount` = COUNT(DISTINCT datadate) with the measure NOT NULL. Never COUNT(*), never
forecast horizon, never number of vintages.

### Findings

1. **The history threshold barely discriminates.** Between 30 and 150 observations only
   26 leaves are lost. With a daily cadence and 2,600 periods, almost every leaf
   with data has years of history.
2. **The real constraint is recency**, not history: 4,681 fresh against 5,420 with
   sufficient history.
3. **The reduction concentrates in Forest_SKU**, caused by freshness rather than history: 2,964 of
   3,587 reach >=90 observations but only 2,322 are fresh.
4. **The actuals SKU vocabulary differs from the taxonomy**, but the `Full_SKU` column of the same
   table carries the canonical vocabulary. The crosswalk was read from the data, not invented. It
   is many-to-one, so counting was grouped at the source.
5. **Inorganic branches have no observed actuals** and are `ACTUALS_SOURCE_UNRESOLVED`, which is
   not the same as `NO_DATA`.
6. **Basilisk has physical actuals series** but keeps `LABEL_ONLY` and `SERVING_EMPTY` per the
   mandate.

---

## E11_PRE_DELIVERY_PACKAGE

**Status: `E11_PRE_DELIVERY_PACKAGE_COMPLETE_AWAITING_OWNER_REVIEW`**

Conversion of the E0-E11 discovery into a delivery package. No additional SQL. E1-E10 unchanged.

| Counter | Value |
|---|---|
| `INITIAL_DELIVERY_CASE_COUNT` | **130** |
| `INITIAL_ROUTE_ARTIFACT_COUNT` | **29** |
| `INITIAL_DELIVERY_HISTORY_GATE` | 150 |
| `INITIAL_DELIVERY_FRESHNESS_GATE` | ACTIVE_ROUTE_AND_RECENT_LEAF |
| `FINAL_HISTORY_THRESHOLD_SELECTED` | NO |
| `FINAL_RECENCY_POLICY_SELECTED` | NO |
| `CPU_PHOENIX_NONPHOENIX_ACTUALS_STATUS` | DERIVABLE_ACTUALS_SPLIT_CONFIRMED |
| `INITIAL_DELIVERY_METRICS` | CPU,HDD,IOPS,SSD |
| `SSD_PHOENIX_INCLUDED` | YES |
| `MEMORY_ANALYTICS_INCLUDED` | NO |
| `DYNAMIC_UI_MANIFEST_CREATED` | YES |
| `HTML_MOCKUP_CREATED` | YES |
| `FULL_STATUS_REPORT_CREATED` | YES |
| `PRODUCTION_RESULTS_CREATED` | NO |
| `PRODUCTION_GRAFANA_DEPLOYED` | NO |
| `SQL_EXECUTIONS_USED` | 0 |
| `DOCUMENT_LANGUAGE` | ENGLISH |

### E11 semantic counter correction

| Counter | Value |
|---|---:|
| `ACTUALS_SOURCE_RESOLVED` | 5,887 |
| `LEAVES_WITH_ACTUAL_DATA` | 5,438 |
| `NO_DATA` | 449 |
| `ACTUALS_SOURCE_UNRESOLVED` | 496 |

`NO_DATA` and `ACTUALS_SOURCE_UNRESOLVED` must not be summed as "no data".

### Blocking checks

**A. CPU Phoenix / NonPhoenix** = `DERIVABLE_ACTUALS_SPLIT_CONFIRMED`.
Physically distinct columns exist (`GCycles_consumed_SSD` 851 obs against `GCycles_consumed_HDD`
563), but the correspondence to Phoenix/NonPhoenix is derived from the storage tier rather than
labelled. The routes are preserved and navigable, but are not marked
`ANALYTICS_DELIVERY_READY`.

**B. Per-route freshness.** 31 active routes, 2 inactive. `SSD|Legacy|Organic` publishes daily
(implied cadence 1.06) but stopped on 2026-07-01: it is a **discontinued** route, not a
slow-cadence one. Excluded from the cohort.

### Artifacts

`evidence/E11/E11_initial_delivery_cohort.csv`,
`E11_initial_delivery_route_summary.csv`,
`E11_dynamic_ui_route_manifest.csv` / `.json`,
`E11_route_freshness_sanity_check.csv`,
`E11_current_dashboard_vs_discovered_scope.csv` / `.md`,
`E11_owner_eligibility_summary.md`,
`AEGIS_Full_Status_Pre_Delivery.md`,
`AEGIS_Dynamic_Taxonomy_Dashboard_Mockup.html`.

All owner-facing deliverables are written in English.

Next: **IMPLEMENT THE 29 ROUTE ARTIFACTS AND WIRE THE DYNAMIC TAXONOMY INTO AEGIS/GRAFANA.**

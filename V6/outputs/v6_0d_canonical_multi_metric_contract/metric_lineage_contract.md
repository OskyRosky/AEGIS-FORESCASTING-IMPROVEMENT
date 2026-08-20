# V6.0D — Metric Lineage and Governance Contract

Defines how a value travels from a physical source to the screen, and what must be
provable at each hop.

---

## 1. The lineage chain

```
SQL source object
      |  (Track B, gated)
      v
Local extract file            data/raw/<file>.csv
      |  registry resolution
      v
Resolved registry entry       metric_registry_resolved.csv
      |  adapter normalisation
      v
Canonical normalized rows     official_metrics_normalized.csv
      |  isolated aggregation
      v
Ranking rows                  official_metric_rankings.csv
      |  option projection
      v
Filter options                metric_filter_options.csv
      |  read-only consumption
      v
Shiny dashboard
```

## 2. Traceability rules

| Rule | Statement | Enforced by |
| --- | --- | --- |
| L1 | Every row in `official_metrics_normalized.csv` carries `source_object` and `source_file` | T02 |
| L2 | Every `source_file` appears in `metric_source_lineage.csv` with `rows_in`, `rows_out` and input `sha256` | T15 |
| L3 | Every ranking row is reproducible from the normalized rows matching its identity tuple | T10 |
| L4 | Every ranking row declares `source_object_count`; a value above one is illegal unless the registry allows merging | T07 |
| L5 | Every Shiny filter option originates in `metric_filter_options.csv` | T13 |
| L6 | Every displayed capability originates in `metric_computability_status.csv` | T12 |
| L7 | Every row declares `contract_version` | T17 |

## 3. Governance invariants preserved

| Invariant | Statement |
| --- | --- |
| G1 | Shiny stays read-only. It renders governed artifacts and never computes a business metric. |
| G2 | No business measure is recalculated anywhere downstream of the source. Measures are copied verbatim. |
| G3 | The champion decision, the 15-model scope and the 30/60/180 horizons are untouched by this work. |
| G4 | No SQL runs in Track A. The builder consumes local extracts only. |
| G5 | `data/raw` is never mounted into the container and never published in an artifact. |
| G6 | No artifact contains a server name, connection string, credential or token. |
| G7 | Legacy artifacts are superseded, never edited, moved or deleted. |
| G8 | An unavailable metric is reported with a status and a reason, never as zero and never as an empty chart. |

## 4. Evidence discipline

Every classification carries `evidence_level`:

| Level | Meaning | Example from the current snapshot |
| --- | --- | --- |
| `VERIFIED_LOCAL` | Measured directly from local files | SSD-Phoenix keys are a strict subset of the forest namespace |
| `VERIFIED_IN_DOCUMENT` | Confirmed in closed prior-stage evidence | The HDD source retains 48 forecast versions |
| `INFERENCE` | Reasoned but unconfirmed | SSD-MCDB may use a SKU grain below forest |
| `STAKEHOLDER_STATEMENT` | Asserted verbally and not verified | The CPU table names and the GCycles unit |

An `INFERENCE` or a `STAKEHOLDER_STATEMENT` may be displayed, but never styled or
worded as a verified fact.

## 5. What the dashboard is forbidden from doing

- Recomputing MAPE, SMAPE, RMSE, MAE, Bias or Accuracy.
- Summing or averaging raw values across `metric_id`.
- Pooling two `db_type` values into one series.
- Comparing a region key against a forest key.
- Inferring a scenario that the source does not contain.
- Rendering a chart whose enabling capability flag is false.

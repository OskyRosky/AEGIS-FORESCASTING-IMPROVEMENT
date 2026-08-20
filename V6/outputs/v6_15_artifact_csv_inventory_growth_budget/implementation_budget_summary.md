# V6.15 Implementation Budget Summary

## 1. What exists now

The pre-V6.15 inventory contains:

| Measure | Exact count |
|---|---:|
| Relevant files | 2,195 |
| CSV files | 1,465 |
| Total size | 1,882.215 MB |
| CSV size | 1,828.207 MB |
| Present registered Shiny inputs | 41 |
| Current registered Shiny CSV inputs | 39 |
| Evidence-only files | 1,878 |
| Contract/spec-only files | 261 |
| Productive runtime inputs | 47 |

Location totals:

| Location | Files | CSV | Size MB | Current Shiny feeds |
|---|---:|---:|---:|---:|
| `V6/outputs/` | 2,164 | 1,436 | 1,718.405 | 22 |
| `V6/data/processed/` | 24 | 24 | 137.980 | 19 |
| `V6/data/storage/` | 6 | 5 | 25.820 | 0 |
| `scenario_resolver.R` | 1 | 0 | 0.011 | 0 |

The active Viewer remains the verified legacy artifact:

- HDD - EDB / Enterprise / Region only.
- 39 of 45 governed keys in that combination.
- 204,300 rows.
- 15 models, not 16.
- 12 rolling origins and 30 horizons.

## 2. Verified product scope

The first-release contract contains 16 exposed combinations:

- Six HDD combinations with actuals: Viewer and Forecast eligible.
- Two SSD-Phoenix combinations without actuals: Forecast eligible only.
- Four CPU combinations without actuals: Forecast eligible only, not extracted.
- Four IOPS combinations without actuals: Forecast eligible only, not extracted.

Current Phase-1 local coverage:

- Six HDD combinations: actual and forecast data present.
- Two SSD-Phoenix combinations: forecast data present.
- CPU and IOPS: no current local extraction.

The final HDD Viewer universe contains 596 key-combinations. The legacy
backtest covers 39, so 557 require model generation if all six combinations are
approved.

## 3. Verified model universe

The exact intersection of the legacy artifact and the v2 model contract is 15:

- Four growth baselines.
- Five statistical models.
- Three machine-learning models.
- Three lightweight-neural models displayed as Deep Learning.

There is no verified sixteenth model. A future stage must not add one without a
new product and model-governance decision.

## 4. Growth budget

Storage estimates use observed local rates:

- Legacy Viewer CSV: 51,467,614 bytes / 204,300 rows =
  251.9218 bytes per row.
- R7 DuckDB: 27,013,120 bytes / 2,033,970 source rows =
  13.2810 bytes per row.

The full-scope footprint retains separate non-neural and neural raw CSVs, writes
the final record CSV, and adds a proportional DuckDB table. It therefore
budgets 1,090.77 MB, not merely the final CSV size.

| Scope | New rows | New CSV files | Estimated artifacts | Storage added |
|---|---:|---:|---:|---:|
| Five-case pilot | 24,750 | 1 | 5 | 5.95 MB |
| Formal Boon/NAMPRD07 slice | 782,100 | 3 | 8 | 385.71 MB |
| All six HDD, 12 non-neural | 1,769,400 | 1 | 5 | 425.10 MB |
| All six HDD, 3 neural | 442,350 | 1 | 5 | 106.28 MB |
| All six HDD, all 15 | 2,211,750 | 3 | 8 | 1,090.77 MB |
| SSD-Phoenix Forecast reuse | 651,480 existing | 0 | 3 planning/validation | 0 MB |

The five-case pilot is a budget construct: five representative Enterprise
Forest key-combinations, 11 origins, 15 models, and 30 horizons. V6.15 does not
choose or run those keys.

## 5. Proposed prerequisites for later versions

These are planning gates, not authorization:

### Before V6.16

- Review and approve this inventory boundary and classification.
- Resolve whether the execution scope is five-case pilot, formal Boon slice, or
  all six HDD combinations.
- Close the existing decisions on model phasing, neural timing, origin cadence,
  Basilisk short history, six missing Region keys, champion scope, and lineage.

### Before V6.17

- Approve a frozen run manifest.
- Name exact pilot keys if a five-case pilot is chosen.
- Record input paths, checksums, expected units, row budget, phase caps, and
  stop conditions.
- Provide explicit authorization to run models.

### Before V6.18

- Complete and validate authorized raw outputs.
- Reconcile actuals and extraction lineage.
- Confirm all approved models are present with no fabricated or padded rows.
- Keep final assembly separate from model execution.

No later version should modify Shiny until a complete, validated record artifact
and read-only storage table exist.

## 6. Risks and assumptions

| Risk or assumption | Effect |
|---|---|
| Five-case pilot keys are not selected | Row/storage budget is valid for five EDB Forest keys, but execution inputs remain undefined |
| Basilisk has about five months of history | Its origin count is five and must not be padded to EDB length |
| Legacy 39 keys are backfilled | They are not included in the 557-key generation estimate |
| CSV size scales linearly | Real text width may change by key and model output |
| DuckDB size scales linearly | Compression may differ for the v2 table |
| Raw phase outputs are retained | Full project-growth estimate is deliberately conservative |
| SSD-Phoenix data already exists | Forecast implementation should add no new extracted rows |
| CPU and IOPS are contracted but absent locally | They cannot feed Forecast until separately approved extraction exists |

## 7. Recommendation

Do not start implementation from V6.15. First approve the scope and frozen
manifest for the next planning gate. If a pilot is desired, define the exact
five key-combinations and expected lineage before any model command.

V6.16 remains blocked until explicit authorization.

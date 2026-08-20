# V6.19 Cohort Source-of-Truth Gate

## Final status

`V6_19_COHORT_SOURCE_OF_TRUTH_GATE_BLOCKED_E11_SOURCE_MISSING`

This gate is documentation and reconciliation only. No artifact generation, model
execution, forecast/backtest regeneration, SQL, or Tesseract extraction occurred.

## E11 source status

The required files were not found:

- `evidence/E11/E11_initial_delivery_cohort.csv`
- `evidence/E11/E11_initial_delivery_route_summary.csv`

`AEGIS_series_universe.csv` was also not found. Searches covered the primary repository,
the parent Forecast Generation project folder, sibling worktrees, the nearby Tesseract
project, E11-named directories/files, and Git history.

Two surviving documents state that E11 froze 130 cases across 29 route artifacts:

- CPU: 48
- HDD: 32
- IOPS: 20
- SSD: 30

They do not enumerate the exact route/entity cases. Therefore the exact 130-case cohort
is not available and must not be reconstructed from prose.

## SSD-Phoenix reconciliation

Current prepared V6.17/V6.18 scope:

- Low Volume No Efficiency / Forest: 148 keys
- Low Volume With Efficiency / Forest: 152 keys
- union: 152 keys
- the 148-key set is contained in the 152-key set
- With-Efficiency-only keys: `CHNPR01`, `NAMP156`, `NAMP242`, `NAMP243`
- both variants are forecast-only

Discovery documentation:

- SSD / Phoenix / Organic / Forest: 144 keys
- SSD / Phoenix / Inorganic / Forest: 133 keys
- SSD / Phoenix / Organic / Region: 25 Regions
- Inorganic actuals source: unresolved

No governed crosswalk maps Organic/Inorganic to either Low Volume variant. The exact
144-key discovery membership is unavailable because the series-universe source is
missing. The SSD-Phoenix mismatch remains a `BLOCKING_DECISION`; neither 144 nor 152 is
selected for future generation.

## Recommended generation scope

Option A, the original 130-case cohort, remains the recommended continuity path only
after its source is recovered or reproducibly regenerated. No generation option is
currently authorized.

The current V6.17/V6.18 scope is measurable but is not a substitute for E11: it contains
896 Forecast cases, 596 Viewer-eligible cases and eight operational routes, while omitting
CPU/IOPS and preserving unresolved legacy SSD-Phoenix variants.

## Exact next step

Oscar must choose one:

1. provide the original E11 cohort and route-summary CSVs; or
2. explicitly authorize a read-only governed E11 discovery rerun that recreates the
   two missing files and the key-level series universe; or
3. define an owner-approved custom cohort and acknowledge that it is not the original
   E11 cohort.

After source recovery, rerun V6.19, populate the exact cohort manifest, reconcile
SSD-Phoenix key membership and obtain explicit scope approval.

## Files created

- `v6_19_file_search_inventory.csv`
- `v6_19_e11_file_status.csv`
- `v6_19_initial_delivery_cohort_manifest.csv`
- `v6_19_route_summary_reconciliation.csv`
- `v6_19_ssd_phoenix_reconciliation.csv`
- `v6_19_generation_scope_options.csv`
- `v6_19_final_generation_manifest.csv`
- `v6_19_blockers_and_decisions.csv`
- `v6_19_validation.csv`
- `v6_19_closure_summary.md`

The initial-delivery and final-generation manifests intentionally contain headers and
zero data rows.

## Files not touched

- V6.18 Shiny UI and server code
- V6.17/V6.18 productive CSV and Parquet artifacts
- model code, model outputs and forecast/backtest artifacts
- V1-V5
- Docker, Azure and Grafana
- Assistant/LLM
- Tesseract sources and SQL

## Governance validation

- Source search was read-only.
- Existing evidence was summarized without moving or overwriting it.
- No 130-case manifest was fabricated.
- No SSD-Phoenix mapping or key count was selected without evidence.
- No generation manifest was populated while blocked.

## V6.20 gate

V6.20 cannot start. The missing E11 source, SSD-Phoenix crosswalk and owner generation
scope decision block artifact generation.

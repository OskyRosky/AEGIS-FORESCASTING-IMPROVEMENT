# R8-FIX-2B Recommended Execution Plan

## Stage boundary

This is a compute-budget estimate only. It does not authorize or execute
R8-FIX-3.

No backtest, model fit, Tesseract extraction, Shiny change, SQL write, Docker
action, or Azure action was performed in R8-FIX-2B.

## 1. Measured reference

The legacy artifact
`V6/data/processed/forecast_viewer_model_outputs.csv` was measured directly:

| Measure | Observed |
|---|---:|
| Series | 39 |
| Distinct rolling-origin dates | 12 |
| Series-origin units | 454 |
| Horizons | 30 |
| Models | 15 |
| Rows | 204,300 |

The identity `454 series-origin units x 15 models x 30 horizons = 204,300
rows` reconciles exactly.

Historical runtime evidence:

- V3.3B-2 live-fit the exact 12 non-neural Viewer models over 454
  series-origin units in 10.87 minutes.
- V3.2D measured the three neural models over the same 454-unit scope:
  FNAR-V2 195.6613 seconds, NLIN-DLIN_FIXED 0.9863 seconds, and SMLP-TCN
  29.196 seconds, totaling 3.764 minutes.
- The reconstructed 15-model reference is therefore 14.634 minutes.

This is not a direct timing of one monolithic legacy-artifact build. It combines
two compatible historical measurements and should be treated as a planning
baseline.

## 2. Scaling method

The estimate scales linearly by series-origin units:

`projected minutes = reference minutes x projected series-origin units / 454`

R8-FIX-0 estimated the missing all-six-HDD scope at:

- 557 new key-combinations.
- 4,915 series-origin units.
- 73,725 model fits across 15 models.
- 2,211,750 new forecast rows across 30 horizons.

The six HDD combinations use 11 monthly origins for EDB and 5 for Basilisk.
The 204,300 verified legacy rows are backfilled rather than rerun.

## 3. Important interpretation of the Boon slice

The formal R8-FIX-0 Boon option is `HDD - EDB / Enterprise / Region + Forest`:

- Top up six uncovered Region keys.
- Generate all 152 Forest keys.
- 1,738 new series-origin units.
- 782,100 new rows for all 15 models.
- Base model time: 56.02 minutes.

NAMPRD07 is a Forest key. It does not exist at Region grain, where keys are
region names. A NAMPRD07-only pilot is therefore a one-key Enterprise/Forest
smoke test, not the complete formal Boon slice.

## 4. Base estimates

| Scope | 12 non-neural | 3 neural | Full 15 |
|---|---:|---:|---:|
| All six HDD combinations | 117.68 min | 40.75 min | 158.43 min |
| Formal Boon slice | 41.61 min | 14.41 min | 56.02 min |
| NAMPRD07 Enterprise/Forest pilot | 0.26 min | 0.09 min | 0.35 min |

The NAMPRD07 scaled compute time is much smaller than process startup,
serialization, and validation overhead. Its execution budget should still be
30 minutes.

## 5. Uncertainty and contingency

The base estimate has medium confidence at scope level and lower confidence at
individual non-neural model level:

- The exact 12-model aggregate is measured, but seven fast models and five
  challenger models were timed as groups.
- Neural models have isolated measurements.
- Forest series may differ in length and behavior from the legacy Region
  series.
- Historical improved LightGBM and XGBoost candidates took 462.9279 and
  1339.3481 seconds respectively over the legacy scope. They are not the exact
  Viewer model implementations, so they are excluded from the base estimate,
  but they justify retaining an overnight contingency.
- Linear scaling does not model startup, checkpoint, I/O, failure recovery, or
  validation.

For that reason:

- Base all-six full run: 2.64 hours of model work.
- Recommended authorized window: 4 hours.
- Conservative unattended window: 8 hours.

## 6. Recommended phased R8-FIX-3 plan

If R8-FIX-3 is later explicitly authorized:

### Gate 0 - 30-minute pilot

Run all 15 models only for `HDD - EDB / Enterprise / Forest / NAMPRD07`.

Stop if:

- Any model fails.
- Row grain or horizon reconciliation fails.
- Actual lineage fails.
- The measured family runtime materially exceeds the projection.

### Phase A - Three-hour cap

Run the 12 non-neural models for all six HDD combinations.

- Base estimate: 117.68 minutes.
- Budget: 180 minutes.
- Validate all raw outputs before proceeding.

### Phase B - One-hour cap

Run FNAR-V2, NLIN-DLIN_FIXED, and SMLP-TCN for all six HDD combinations.

- Base estimate: 40.75 minutes.
- Budget: 60 minutes.
- Stop on the first systemic validation failure.

### After execution

Do not assemble or wire the artifact during R8-FIX-3. Final CSV and DuckDB
assembly remain R8-FIX-4, and Shiny remains unchanged until R8-FIX-5.

## 7. Recommendation

Approve a four-hour, two-phase execution window only after the R8-FIX-2 open
decisions and run manifest are closed:

1. 30-minute NAMPRD07 smoke gate.
2. Up to three hours for all-six 12-model execution and validation.
3. Up to one hour for all-six neural execution and validation.

The phase caps are operational ceilings, not targets. Checkpoint completed raw
outputs and stop rather than silently substituting, padding, or fabricating
missing results.

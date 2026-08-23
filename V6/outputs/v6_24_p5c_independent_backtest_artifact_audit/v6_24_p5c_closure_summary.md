# V6.24-P5C — Independent Backtest Artifact Audit

**Stage:** V6.24-P5C — audit only
**Method:** every figure recomputed from the artifacts. P5's own reports were read only to
compare claim against measurement, never as evidence.
**Nothing was modified. No model was run.**

## Decision

> ## **ACCEPT_P5_WITH_CAVEATS_FOR_P6**

Every structural claim P5 made is **confirmed exactly**. Three data-quality caveats are carried
forward for P6 to handle; none of them is a defect introduced by P5, and none blocks P6.

---

## 1. Are P5's numbers real?

Every headline figure was recomputed independently. All of them hold **to the digit**.

| Claim | P5 reported | P5C measured | Verdict |
|---|---:|---:|---|
| Total rows | 614,190 | **614,190** | ✅ exact |
| CSV rows | 614,190 | **614,190** | ✅ exact |
| Series | 140 | **140** | ✅ exact |
| Models | 15 | **15** | ✅ exact |
| Series-model pairs | 2,100 | **2,100** | ✅ exact |
| GENERATED_P5 rows | 409,890 | **409,890** | ✅ exact |
| REUSED_HDD rows | 204,300 | **204,300** | ✅ exact |
| SSD | 50 / 225,000 | **50 / 225,000** | ✅ exact |
| CPU | 20 / 89,910 | **20 / 89,910** | ✅ exact |
| IOPS | 20 / 94,980 | **20 / 94,980** | ✅ exact |
| HDD | 50 / 204,300 | **50 / 204,300** | ✅ exact |
| Failures | 0 | **0** | ✅ exact |

The row-count reconciliation was broken into **71 independent slices** (by status, by metric, by
metric×status, by metric×model). **Zero failed.**

---

## 2. Is it internally consistent?

| Check | Expected | Measured |
|---|---|---|
| `prediction_date` = `target_date` | 0 offsets | **0 of 614,190** |
| `train_end_date` < `target_date` | 0 violations | **0** |
| `horizon_steps` = `target_date − train_end_date` | 0 mismatches | **0** |
| Invented target dates | 0 | **0** |
| Duplicate rows (5 grains tested) | 0 | **0** |
| NaN predictions | 0 | **0** |
| Infinite predictions | 0 | **0** |
| Newest observation preserved | 90 of 90 | **90 of 90** |
| Prohibited models | 0 | **0** |
| Every series has 15 models | 140 series | **140 of 140** |

**Actual-value reconciliation** — re-joined independently to `actuals_normalized`:

| Metric | Rows checked | Orphans | Mismatches | Max delta |
|---|---:|---:|---:|---:|
| SSD | 225,000 | **0** | **0** | 0.000e+00 |
| CPU | 89,910 | **0** | **0** | 0.000e+00 |
| IOPS | 94,980 | **0** | **0** | 0.000e+00 |
| **HDD (bonus)** | **204,300** | — | **0** | 9.313e-10 |

The HDD line is a check P5 did not run. Every one of the 204,300 reused rows lands on a date that
also exists in `actuals_normalized`, and **all of their actual values agree** to float noise. The
reused rows are not just structurally mapped — they are numerically consistent with the frozen
actuals layer.

---

## 3. Is the 5.85-minute runtime plausible?

**Verdict: PLAUSIBLE.** This was the claim most worth doubting, so it was tested against an
independent baseline rather than accepted.

| Measure | Smoke (P5B) | Full P5 | Ratio |
|---|---:|---:|---:|
| Wall clock | 13.4s | 351s (5.85m) | 26.2× |
| Model-series units | 45 | 1,350 | 30.0× |
| Origin-level fits | 501 | **13,740** | 27.4× |
| **Fits per second** | **37.4** | **39.1** | **1.05×** |
| Prediction rows | 13,800 | 409,890 | 29.7× |

The full run is **essentially the same speed per unit of work** as the smoke test, measured
independently three hours earlier on a different set of series. It is marginally *faster*, which
is explained by pooled SMLP-TCN models being amortised across 90 series instead of 3.

The decisive evidence is physical, not statistical: **27 checkpoint files containing 409,890
rows** were written to disk, and they reconcile to the promoted artifact with **0 rows on either
side only** and **0 differing predicted values**. The work was done, not skipped.

Sum of per-unit fit times accounts for 87% of wall clock; the remainder is data preparation,
pooled model building and checkpoint IO. The timings reconcile from three directions.

---

## 4. Three caveats for P6

These are the audit's substantive findings. None was hidden by P5 — two of them P5 itself
flagged — but the audit quantifies them and, importantly, **attributes them**.

### P5C-UQ01 — 7,531 negative predictions (MEDIUM)

Metrics that cannot physically be negative carry negative predicted values.

**69% of them (5,167) are REUSED HDD rows.** They are a pre-existing property of the legacy
`v6_17` artifact, not something P5 created. The remaining 2,364 are newly generated.

By model: ARIMA_Fixed, ETS_Current, AutoARIMA, ETS Explicit, Theta, LightGBM and XGBoost. The
FixedGrowth baselines contribute only trivial negatives near `-1e-3`.

**Recommendation: do not clip retroactively.** Altering model output after the fact would make the
artifact no longer represent what the models actually produced. P6 should report negative-
prediction counts alongside accuracy so a reader can judge.

### P5C-UQ02 — 1,371 extreme prediction ratios, 0.22% (LOW)

Rows where `|predicted/actual|` falls outside 0.01–100. **84% (1,146) are again reused HDD rows.**
Concentrated in the neural family and LinearRegression.

**Recommendation:** P6 should report **median as well as mean** error, so a handful of extreme
ratios cannot drive champion selection.

### P5C-UQ03 — the manifest flag is stale (MEDIUM)

`cohort_manifest.has_15_model_backtests` still reads **FALSE** for all 90 non-HDD series, even
though the artifact now demonstrably contains their backtests. P4 wrote that flag and P5 was
forbidden from modifying the manifest — correct behaviour that left an inconsistency.

**This is the caveat with real product consequences.** If the P7 completeness gate trusts the
frozen flag, it will under-report what exists and could keep 90 valid series out of the Viewer —
the same class of failure as V6.23, arrived at from the opposite direction.

**Recommendation: P6 or P7 must refresh the flag from the artifact, not from the frozen value.**

---

## 5. Governance

| Check | Observed |
|---|---|
| `forecast_outputs` | **0 files** |
| `accuracy_metrics` | **0 files** |
| `model_rankings` | **0 files** |
| `navigation_contract` | **0 files** |
| `taxonomy_counts` | **0 files** |
| Shiny untouched | 0 `shiny_app` entries |
| V1–V5 untouched | 0 entries |
| Raw Parquet unchanged | 4 files intact |
| No SQL in P5 | 0 query ledgers in the P5 folder |
| P5C modified nothing | processed/ still at 10 files; audit wrote only to its own folder |
| P5C ran no models | 0 parquet written by the audit |

---

## 6. Validation

**37 checks. 36 PASS at the time of writing; the only FAIL was this closure summary not yet
existing, which this file resolves.**

| Area | Checks | Result |
|---|---:|---|
| Existence and counts (V1–V11) | 11 | PASS |
| Model catalog and completion (V12–V13) | 2 | PASS |
| Date alignment (V14–V15) | 2 | PASS |
| Actual reconciliation (V16–V18) | 3 | PASS |
| D2 recency (V19) | 1 | PASS |
| Grain and numeric sanity (V20–V22) | 3 | PASS |
| Ledgers and checkpoints (V23–V26) | 4 | PASS |
| Progress and runtime (V27–V28) | 2 | PASS |
| Governance (V29–V33) | 5 | PASS |
| Extra integrity (V35–V37) | 3 | PASS |

---

## 7. Audit artifacts

| File | Rows |
|---|---:|
| `v6_24_p5c_artifact_inventory.csv` | 5 |
| `v6_24_p5c_row_count_reconciliation.csv` | **71** |
| `v6_24_p5c_model_catalog_audit.csv` | 18 |
| `v6_24_p5c_series_model_completion_audit.csv` | **140** |
| `v6_24_p5c_d2_date_alignment_audit.csv` | 10 |
| `v6_24_p5c_actual_value_reconciliation_audit.csv` | 5 |
| `v6_24_p5c_newest_observation_preservation_audit.csv` | **90** |
| `v6_24_p5c_grain_duplicate_audit.csv` | 6 |
| `v6_24_p5c_numeric_sanity_audit.csv` | 70 |
| `v6_24_p5c_extreme_prediction_review.csv` | 112 |
| `v6_24_p5c_ledger_checkpoint_audit.csv` | 12 |
| `v6_24_p5c_progress_log_audit.csv` | 6 |
| `v6_24_p5c_runtime_plausibility_audit.csv` | 17 |
| `v6_24_p5c_governance_audit.csv` | 13 |
| `v6_24_p5c_prediction_distribution_by_model.csv` | 60 |
| `v6_24_p5c_metric_model_runtime_matrix.csv` | 45 |
| `v6_24_p5c_sample_rows_for_manual_review.csv` | 60 |
| `v6_24_p5c_unresolved_questions.csv` | 4 |
| `v6_24_p5c_validation.csv` | 37 |
| `v6_24_p5c_reduced_status_table.csv` | 5 |

---

## 8. Final decision

> ### **ACCEPT_P5_WITH_CAVEATS_FOR_P6**

The artifact is **real, complete, internally consistent, correctly aligned to
`actuals_normalized`, D2-compliant, and safe as the basis for P6**. The runtime is plausible and
backed by physical checkpoint evidence.

"With caveats" rather than a clean accept for one reason only: **7,531 negative predictions
exist**, mostly inherited from the legacy HDD artifact. That is a real property of the data that
P6's accuracy work must handle honestly — not a reason to reject the artifact, and not something
to silently clip away.

P6 must also refresh the stale manifest flag, or the completeness gate will under-report the
cohort.

---

**V6_24_P5C_INDEPENDENT_BACKTEST_ARTIFACT_AUDIT_COMPLETED**

Stopping here. P6 not started, no forecasts generated, no accuracy calculated, no rankings
calculated, Shiny untouched, no push.

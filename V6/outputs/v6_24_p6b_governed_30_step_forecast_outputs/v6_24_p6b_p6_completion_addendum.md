# V6.24-P6 — Completion Addendum

**This addendum closes V6.24-P6.**

P6 originally delivered two of its three artifacts and blocked the third. P6B resolved
the block. As of this addendum, **P6 is complete for all three artifacts under the
governed 30-step MVP horizon.**

---

## 1. P6 artifact status — final

| Artifact | Location | Rows | Delivered by | Status |
|---|---|---|---|---|
| `accuracy_metrics` | `processed/v6_24_mvp_cohort/` | 2,100 | P6 | **COMPLETE** |
| `model_rankings` | `processed/v6_24_mvp_cohort/` | 2,100 | P6 | **COMPLETE** (see §4) |
| `forecast_outputs` | `processed/v6_24_mvp_cohort/` | 63,000 | **P6B** | **COMPLETE** |

## 2. How the block was resolved

P6 blocked `forecast_outputs` with the token
`V6_24_P6_BLOCKED_FORECAST_HORIZON_UNRESOLVED` because three mutually incompatible
horizon semantics existed and no evidence supported choosing between them.

The owner resolved it by **accepting the only empirically verified option**:

| Semantics | Value | Disposition |
|---|---|---|
| Prompt default assumption | 1,440 days | Rejected — unattainable by any governed model |
| Legacy HDD forward artifact | 732 daily steps, 30 ungoverned model names | Rejected — zero overlap with the governed 15 |
| **Proven model capability** | **30 daily steps** | **ACCEPTED** as `GOVERNED_30_STEP_DAILY_FORECAST` |

The evidence behind the accepted option is `v6_24_p6_forecast_horizon_probe.csv`: all
15 governed models were fitted on a real cohort series and every one emitted exactly 30
steps. The distinct set of emitted step counts across all 15 models is `[30]`.

This is a deliberate scope decision, not a workaround. A longer horizon remains
available later, but only as a **modelling capability change** — for the neural models,
`HORIZON_DAYS` is the output dimension of the trained network, not a parameter.

## 3. What P6B did and did not touch

P6B generated forward forecasts only. It did **not** re-run HDD backtests, did not
recalculate accuracy, and did not recalculate rankings. All 12 frozen P4/P5/P6 artifacts
were verified unmodified by mtime and size comparison before and after the run.

## 4. Caveat carried forward — `model_rankings` is complete but has a known defect

`model_rankings` is present and structurally valid: 2,100 rows, ranks 1–15 within every
series, exactly one champion per series.

However, P6B discovered that **16 of the 140 champions were selected incorrectly**. P6's
ranking fallback tiers `wape` → `smape` → `mae` as an ordered preference, so a model
with a computable `smape` outranks one that falls through to `mae` even when the latter
is strictly more accurate. In 15 cases this crowned `FNAR-V2` (mae 0.082–0.119) over
models with mae of exactly 0.000.

The defect is bounded to series where `wape` is not computable. The other **124 series
are verified correct**.

`model_rankings` is therefore marked **COMPLETE WITH A KNOWN DEFECT**, and a **P6C**
correction stage is recommended before P7 surfaces champions in the Viewer. Evidence:
`v6_24_p6b_p6_ranking_defect_finding.csv`.

## 5. Cohort caveat carried forward

**15 of the 140 MVP series contain only zeros.** Their forecasts are correctly ~0 and
their backtests are valid, but ranking and percentage-error metrics are structurally
meaningless for them. P7 should mark them `ZERO_SIGNAL`.

## 6. Aggregation rule carried forward from P6

Accuracy must be aggregated by **median, never by mean**. 11 of 2,100 series-model pairs
have `wape > 100` (max `1.25e23`), which pushes the HDD mean `wape` to ~2.4e20 while its
median is 0.0506.

## 7. Gate to P7

P7 (`navigation_contract`, `taxonomy_counts`) may start once the owner resolves:

- **Q1** — whether to run P6C to correct the 16 misranked champions *(recommended)*.
- **Q2** — how to treat the 15 zero-signal series in the Viewer cohort.

P7 must continue to derive readiness from `model_backtests_15_models`, never from
`cohort_manifest.has_15_model_backtests`, which remains stale `FALSE` for 90 series.

---

**V6_24_P6_COMPLETE_UNDER_GOVERNED_30_STEP_HORIZON**

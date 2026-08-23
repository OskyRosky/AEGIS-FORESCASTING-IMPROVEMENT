# V6.24-P6B — Governed 30-Step Forecast Outputs — Closure Summary

**Status: COMPLETE. Validation 40 PASS / 0 FAIL.**

`forecast_outputs` is generated and promoted. **P6 is now complete for all three of
its artifacts — `accuracy_metrics`, `model_rankings` and `forecast_outputs` — under
the governed 30-step MVP horizon.**

---

## 1. What was generated

| | |
|---|---|
| Rows | **63,000** (140 series × 15 models × 30 steps) |
| Series-model pairs | 2,100, every one emitting exactly 30 steps |
| Model failures | **0** of 2,100 |
| Runtime | **1.05 minutes** |
| Promoted to | `V6/data/processed/v6_24_mvp_cohort/forecast_outputs.parquet` / `.csv` |

Promotion was gated on 15 conditions checked **before** writing anything. Checkpoints
were written per metric (HDD 22,500 / SSD 22,500 / CPU 9,000 / IOPS 9,000) and
reconcile exactly to the final artifact.

## 2. The horizon that was accepted, and what it means

`forecast_type = GOVERNED_30_STEP_DAILY_FORECAST`, with
`forecast_date = train_end_date + forecast_step days` for `forecast_step` 1..30,
verified on all 63,000 rows.

`train_end_date` is **each series' own last observed date**, not a common calendar
origin. This means the forecast windows genuinely differ across metrics:

| Metric | train_end_date | forecast window |
|---|---|---|
| CPU, IOPS | 2023-07-20 | 2023-07-21 → 2023-08-19 |
| HDD | 2026-04-26 → 2026-07-19 | varies per series |
| SSD | 2026-08-22 | 2026-08-23 → 2026-09-21 |

Forcing a shared origin would have meant discarding real history or inventing it.
This is recorded as open question Q6 for the Viewer's x-axis design.

## 3. Fidelity with P5

The model execution path was **copied verbatim** from `p5_full_run.py` — same wrappers,
same `RANDOM_SEED = 42`, same pooled-global-model approach for SMLP-TCN. Forecasts and
backtests are therefore produced by identical code, which is what makes
Viewer = Forecast parity meaningful.

One consequence must be disclosed rather than hidden: `FNAR-V2` and `SMLP-TCN` apply an
internal `clip(0, ∞)` as part of their inverse `log1p` transform. That clip is **model
behaviour inherited from P5**, already baked into the backtest artifact — it is not P6B
clipping. P6B added no post-hoc clipping of its own. The practical effect is that those
two models can never emit a negative forecast, which a reader comparing models should
know. Recorded as Q5.

## 4. Negative and extreme forecasts — reported, not clipped

| | count | share |
|---|---|---|
| Negative forecasts | 573 | 0.91% |
| Extreme forecasts | 84 | 0.13% |
| Extreme ratio not computable | 8,550 | 13.57% |

Negatives concentrate in `LinearRegression` (96), `LightGBM` (90), `ETS_Current` (86),
`ARIMA_Fixed` (79) and `AutoARIMA` (67). The 8,550 not-computable rows are the
mechanical consequence of the finding in section 5: when the last observed actual is
zero, the ratio test has no denominator.

## 5. Finding — 15 MVP series carry no signal at all

**15 of the 140 MVP series (10.7%) have `actual_value = 0` for every single
observation.** All 15 are HDD, spanning both Basilisk and EDB Consumer lineages. Their
52,650 backtest rows sum to an absolute actual value of exactly **0.0**.

The forecasts for these series are correct — essentially zero, with only 540 of 6,750
rows nonzero and a maximum absolute value of 0.84. Nothing was faked.

But a "champion model" for an all-zero series is not a meaningful product statement, and
`wape` is structurally undefined for them. P7 should mark these series `ZERO_SIGNAL` and
suppress ranking display. Recorded as Q2.

## 6. Finding — P6 crowned the wrong champion for 16 of 140 series

While computing the extreme-ratio anchor, P6B surfaced a **defect in the P6 ranking
logic that P6 itself did not catch.**

P6 ranked models by `wape`, falling back to `smape`, then to `mae`. The fallback was
implemented as an ordered tier, so **a model with a computable `smape` (tier 1) always
outranked a model that fell through to `mae` (tier 2) — regardless of which was actually
more accurate.** The tier order encodes *metric availability*, not accuracy.

The consequence, measured:

- In **15 series**, `FNAR-V2` was crowned with `mae` between 0.082 and 0.119, beating
  `ARIMA_Fixed` and 12 other models that had `mae` of **exactly 0.000**.
- In the 16th series (`SSD__Phoenix__Forest__GBRP267`), `ARIMA_Fixed` (mae 0.091) was
  crowned over `NLIN-DLIN_FIXED` (mae 0.001).
- Every one of `FNAR-V2`'s 15 championships in P6 is one of these degenerate series —
  the two sets are **exactly equal**. The P6 closure's reading that FNAR-V2 shows "HDD
  affinity" was wrong; it was an artifact of this defect.

The defect is **bounded**: it can only affect series where `wape` is not computable for
any model. The other **124 series are verified correct** — the crowned champion is the
lowest-`wape` model in 124 of 124 cases.

P6B is explicitly forbidden from recalculating rankings, so **nothing was changed**. The
full per-series evidence is in `v6_24_p6b_p6_ranking_defect_finding.csv`, and a small
**P6C** correction stage is recommended before P7. Recorded as Q1.

## 7. Governance

Shiny, V1–V5 and the raw Parquet layer were verified clean via `git status` — not
asserted. All 12 frozen P4/P5/P6 artifacts were verified unmodified by mtime and size
comparison taken before and after the run. No SQL, no new extraction, no re-run of HDD
backtests, no recalculation of accuracy or rankings, no `navigation_contract`, no
`taxonomy_counts`, no staging, no push.

## 8. Recommended next step

**Run P6C before P7**, scoped narrowly to correcting the ranking tie order and marking
zero-signal series. P7 builds the navigation contract and will surface champions
directly in the Viewer; shipping it on top of 16 known-wrong champions would put the
defect in front of users.

---

**V6_24_P6B_GOVERNED_30_STEP_FORECAST_OUTPUTS_COMPLETED**

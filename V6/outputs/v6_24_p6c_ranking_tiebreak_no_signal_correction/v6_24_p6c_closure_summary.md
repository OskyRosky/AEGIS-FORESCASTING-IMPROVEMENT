# V6.24-P6C — Ranking Tie-Break / No-Signal Series Correction — Closure Summary

**Status: COMPLETE. Validation 38 PASS / 0 FAIL.**

**Verdict: `READY_FOR_P7_WITH_CAVEATS`.**

The canonical `model_rankings` has been recomputed under `P6C_RANKING_POLICY_V2`.
**16 of 140 champions were corrected.** No other processed artifact changed.

---

## 1. The defect, and the fix

P6 ranked models by `wape`, falling back to `smape`, then `mae`. The fallback was
resolved **per model**, as an ordered tier. That meant a model whose `smape` happened
to be computable (tier 1) automatically outranked models that fell through to `mae`
(tier 2) — **even when those models were strictly more accurate.** The tier order
encoded *metric availability*, not accuracy.

`P6C_RANKING_POLICY_V2` fixes this with three rules:

- **R01 — the metric sequence is resolved once per series, never per model.** This is
  the actual fix.
- **R02 — a metric may only be used if it is computable for all 15 models.** Comparing
  a computed value against a missing one is not a comparison.
- **R03 — a constant metric cannot be the primary metric.** A metric identical across
  all 15 models carries no ranking information; labelling it "primary" would
  misrepresent how the champion was chosen.

The deterministic tie-break (`ETS Explicit` first … `FNAR-V2` last) is applied **only
after every numeric metric has tied**, so it can never override measured accuracy.

## 2. The 15 vs 16 ambiguity — resolved from artifacts

Both numbers were right. They count different populations:

| Population | Definition | Derived from | Count |
|---|---|---|---|
| A. No-signal series | every observation in the **full history** is zero | `actuals_normalized` | **15** |
| B. WAPE-not-computable | sum of \|actual\| over the **backtest window** is zero | `accuracy_metrics` | **16** |
| C. Misranked champions | champion was not the most accurate model | rankings vs accuracy | **16** |

B ⊃ A, and the gap is exactly **one series**: `SSD__Phoenix__Forest__GBRP267`.

That series **does** carry real signal — 426.8 total absolute value across 130
observations, 67 of them nonzero, peaking at 60.74. But its last nonzero observation is
**2026-06-20**, and all 63 of its backtest target dates run **2026-06-21 → 2026-08-22**.
The D2 window policy placed its entire evaluation window in a dead 63-day tail, so the
backtest sums to exactly 0.0 and `wape` is undefined.

So: **15 is the no-signal series count; 16 is the defect population.** The defect is
driven by backtest-window computability, not by whole-series signal.

## 3. What changed

| | Before (P6) | After (P6C) |
|---|---|---|
| `FNAR-V2` championships | 15 | **0** |
| `ETS Explicit` championships | 6 | **21** |
| `FixedGrowth_1_5` championships | 16 | 17 |
| `ARIMA_Fixed` championships | 9 | 8 |

- In the **15 no-signal series**, `FNAR-V2` (mae 0.082–0.119) was replaced by
  `ETS Explicit` (mae **exactly 0.000**), which won the tie among 13 models that all
  achieved perfect zero error.
- In `GBRP267`, `ARIMA_Fixed` (mae 0.091) was replaced by `FixedGrowth_1_5`, selected on
  `rmse` — an improvement of 0.089 in mae.
- **Every one of `FNAR-V2`'s 15 P6 championships was an artifact of the defect.** It now
  holds zero championships across all 140 series. This is the first honest measurement
  of that model.

**No champion changed outside the 16-series defect population** — verified explicitly as
check V37. The 124 fully computable series were already correct and are untouched.

## 4. Champion validity is now an explicit field

`model_rankings` gained `champion_validity`, `champion_reason` and
`signal_quality_status`. The 15 no-signal series carry
`champion_validity = NOT_MEANINGFUL_NO_SIGNAL`, so **P7 can filter on a field rather
than on a hardcoded list**. Every other series carries
`MEANINGFUL_ACCURACY_RANKING`.

A no-signal series still has exactly one technical champion, for schema consistency —
but the Viewer must not present it as a recommendation.

## 5. New support artifact

`series_signal_quality.parquet` / `.csv` — 140 rows classifying every series as
`SIGNAL_PRESENT` (121), `TRAILING_ZERO_LATEST_ACTUAL` (4) or
`NO_SIGNAL_ALL_ZERO_ACTUALS` (15), with the full evidence per series. Derived from
`actuals_normalized` with tolerance 1e-12. **Counts were derived, never hardcoded.**

## 6. Governance

`model_rankings` was the only canonical artifact overwritten, plus the newly permitted
`series_signal_quality`. All **12 other processed artifacts were verified byte-identical
by sha256 taken before and after the run** — not merely by mtime.

An immutable snapshot of the pre-P6C rankings, with its own sha256, was captured
**before** the overwrite. Shiny, V1–V5 and raw Parquet verified clean via `git status`.
No models re-run, no accuracy recalculated, no `navigation_contract`, no
`taxonomy_counts`, no staging, no push.

## 7. P7 readiness — READY_FOR_P7_WITH_CAVEATS

P7 may start. Four caveats travel with the artifacts:

1. **15 no-signal series** must be surfaced with their champion suppressed. Filter on
   `champion_validity`, not on a list.
2. **`GBRP267` accuracy is measured on a dead tail.** Its champion is correct by policy,
   but the underlying accuracy is low-confidence. Re-backtesting is P5 scope and was not
   done.
3. **Aggregate accuracy by median, never mean** — 11 series-model pairs exceed
   `wape = 100`, max `1.25e23`.
4. **`cohort_manifest.has_15_model_backtests` is still stale `FALSE` for 90 series.**
   Derive readiness from `model_backtests_15_models`.

---

**V6_24_P6C_RANKING_TIEBREAK_NO_SIGNAL_CORRECTION_COMPLETED**

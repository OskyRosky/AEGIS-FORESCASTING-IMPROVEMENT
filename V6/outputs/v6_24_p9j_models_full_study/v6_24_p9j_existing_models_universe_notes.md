# P9J — Notes on the existing Models section

## What the old Models section actually is

Three pages under a `Models` sidebar group, built during the Model Lab work:

| Page | Shape | Source |
|---|---|---|
| **Universe** | title + 3 accordions + page-keyed assistant | mostly static prose, one artifact table |
| **Tournament** | title + **11 accordions** + pairwise DT | tournament engine CSVs |
| **Champion** | title + 7 accordions + Plotly leadership chart + 2 DT tables | champion decision + governance CSVs |

All three follow the same pattern: `section_head()`, a stack of `home_collapse()`
accordions, DT tables, and a closing `llm_explain_ui(...)` assistant. The
narrative quality is genuinely high — the Tournament guide explains *what is
being compared*, *why MASE is primary*, *why RMSSE is a guardrail*, and *why the
champion is conditional*. That teaching structure is the part worth keeping.

## The scope difference, measured

```
LEGACY tournament   13 models  ×  39 entities   ×  HDD only
V6.24 cohort        15 models  × 140 series     ×  CPU + HDD + IOPS + SSD
```

`tournament_model_scorecard.entity_count` is **39 for every model** — this is
the 39-key HDD slice recorded at the very start of this project.

**Model overlap is 12.** The legacy tournament carries `FastNeuralAR_MLP`, which
does not exist in V6.24. V6.24 carries `FNAR-V2`, `NLIN-DLIN_FIXED` and
`SMLP-TCN`, none of which ever entered the tournament.

## What does not exist in V6.24

Four things the old Models pages are built on have **no successor artifact**:

1. **MASE** — the legacy primary metric. `accuracy_metrics` has no column
   matching `mase`.
2. **RMSSE** — the legacy guardrail. No column either.
3. **Pairwise evidence** — `tournament_pairwise_evidence.csv` holds 78 ordered
   pairs = C(13,2), each with a bootstrap CI, a sign-test p-value and a
   BH-adjusted p-value. Nothing comparable exists under V6.24.
4. **A global champion decision** — the legacy champion is one model for the
   whole universe. V6.24's champion fields live **per series** inside
   `navigation_contract`.

None of these can be produced inside Shiny. Each would require a governed
offline computation, which is explicitly out of scope.

## The finding that changes the Champion page

The legacy Champion page states, as governed approved language:

> *"ETS Explicit was selected as champion with conditions."*

In V6.24, **ETS Explicit is the presentable champion on 6 of 125
signal-present series.**

It appears as `champion_model_name` on 21 rows, but 15 of those are the
no-signal series where P6C's tie-break crowns it and `champion_visible` is
`FALSE`. So the honest count is 6 — under 5% of the cohort.

Fourteen different models win at least one series:

```
FixedGrowth_6 21 · FixedGrowth_1_5 17 · AutoARIMA 16 · XGBoost 13 · Theta 12
ARIMA_Fixed 8 · LightGBM 7 · NLIN-DLIN_FIXED 7 · ETS_Current 7 · ETS Explicit 6
FixedGrowth_3 4 · FixedGrowth_4 4 · LinearRegression 2 · SMLP-TCN 1
```

Carrying the legacy sentence into Models FULL would be **factually wrong on the
new cohort**. It is not a wording preference — it is a claim the data
contradicts.

## What is safely reusable

- The **accordion teaching structure** on all three pages
- The **read-only discipline**: the tournament engine computes outside Shiny and
  `tournament_league_data()` only loads and orders. V6.24 must keep this.
- The **governance vocabulary**: conditions, confidence, approved vs forbidden
  statements, review triggers. The mechanism is excellent even though the
  specific statements no longer apply.
- The **per-series leadership chart** idea — V6.24 can build it honestly from
  `navigation_contract`, and it becomes far more informative with 14 winners
  across 140 series than it was with one global champion.

## What must be renamed

The word **"Tournament"** implies the bootstrap pairwise competition that
produced supported-better / supported-worse records. V6.24 has no such
evidence. Calling a page of cohort medians a "tournament" would import a
statistical claim that was never made.

Recommended: **Ranking Diagnostics**, with the page saying plainly that it
compares medians and championship counts, not head-to-head outcomes.

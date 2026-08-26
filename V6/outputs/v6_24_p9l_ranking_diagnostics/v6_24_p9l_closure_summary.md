# V6.24-P9L — Models FULL Ranking Diagnostics

**Stage:** V6.24-P9L · **Read-only.** No governed artifact was modified.

---

## 1. What shipped

**Models FULL → Ranking Diagnostics**, the honest replacement for the legacy
Tournament. It compares the 15 governed models across the 140-series cohort
using medians the artifact supports — and declares no winner.

**0 new files, 6 modified**, all additive. Two are one-line wiring.

---

## 2. The design problem, and the answer

The legacy Tournament could say *"model A beat model B, supported"* because it
ran a paired bootstrap with multiple-testing correction over 39 HDD entities.
V6.24 has no such artifact, no MASE, no RMSSE, and no global champion.

Rather than dress up medians as a competition, the page reports **two separate
headlines** and refuses to merge them:

| Headline | On MAE |
|---|---|
| Lowest diagnostic median | **Theta** (189.59) |
| Most series led | **FixedGrowth_6** (21 of 125) |

**They are different models — on every measure tested.** The page renders a
dedicated card saying so: *"Lowest median is Theta; most series led is
FixedGrowth_6. Neither is a winner."*

That disagreement is the finding, not a defect to be smoothed over.

---

## 3. The disagreement is measurable

A dedicated table gives every model its position under all six measures.
**ARIMA_Fixed moves 10 places** — 10th on MAE, 15th on WAPE and SMAPE. Maximum
spread across the cohort is 10 positions.

If the measures agreed, that table would be flat. It is not, which is the
concrete evidence that a single "standing" would mislead.

---

## 4. Verified numbers

- Champion counts **sum to exactly 125**, matching `champion_visible` — the 15
  no-signal series are excluded, and the chart subtitle says so
- Cohort medians recomputed independently and matched to four decimals
- Zero `mean()` calls in the helper
- Family filter: All 15 · Growth Baseline 4 · Statistical 5 · Machine Learning 3
  · Deep Learning 3
- All four sort options produce genuinely different orderings

---

## 5. Forbidden-claims audit on the rendered page

| Term | Occurrences | All inside |
|---|---|---|
| MASE / RMSSE | **0** | — |
| tournament winner | **0** | — |
| league standings | **0** | — |
| official global rank | **0** | — |
| p-value | 1 | *"V6.24 does not contain … p-values, or a global champion artifact"* |
| global champion | 3 | the same absence sentence |
| head-to-head | 2 | *"This is not a head-to-head tournament"* |

Zero assertive uses. All seven assistant answers pass the context-aware guard.

---

## 6. Two bugs I hit

**A silent no-op edit.** My anchor-based replacement of the server file did not
match, so the file was written back **unchanged**. Everything parsed, the app
started, the page rendered — and every server output was empty. Caught because
the browser check read `metricOpts: null` and `NO CHART` rather than trusting
that the edit had landed. Redone by line position and verified by grepping for
the new symbols before restarting.

**Intent routing order.** *"What changed from the old HDD Tournament?"* routed
to `mr_not_tournament` because the tournament guard ran before the comparison
guard. Same ordering class as the P9G bug. The quick-prompt button passes an
explicit intent so it worked, but a user **typing** that question got the wrong
answer. Fixed; 8/8 routing.

---

## 7. What I deliberately did not do

- **No Champion FULL** — P9M
- **No pairwise, no bootstrap, no p-values, no MASE/RMSSE** — the artifacts do
  not exist and computing them is forbidden
- **No global champion**
- **No downloads**
- **No change** to Models FULL Universe, legacy Models, or any V6.24 MVP page

---

## 8. Known caveats

1. **The champion-count chart now appears on both Universe and Ranking.** Q1.
2. **The disagreement view is a position table, not a heatmap.** The prompt
   allowed either; the table was lower risk. Q2.
3. **The column is labelled "Position"** with the disclaimer in the card lead
   rather than in the header itself. Q3.

---

## 9. Next stage

**READY_FOR_P9M_CHAMPION_FULL.**

P9M should own the per-series champion: the lookup against the shared Viewer
selection, the ranking-policy explanation, and the no-signal suppression. The
championship distribution already exists and is verified.

`V6_24_P9L_RANKING_DIAGNOSTICS_COMPLETED`

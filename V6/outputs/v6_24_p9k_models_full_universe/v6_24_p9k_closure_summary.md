# V6.24-P9K — Models FULL Universe

**Stage:** V6.24-P9K · **Read-only.** No governed artifact was modified.
**Downloads:** deferred to P9G2 — not implemented, not pretended.

---

## 1. What shipped

A new **Models FULL** sidebar group with its **Universe** page, built entirely
on the V6.24 governed artifacts. The legacy **Models** group — Universe,
Tournament, Champion — is untouched and still works.

**3 new files, 6 modified.** Five of the six modifications are one or two lines
of wiring; the sixth appends CSS. No legacy logic file was edited.

---

## 2. Every number re-derived

| Card | Shown | Re-derived from parquet |
|---|---|---|
| Governed models | 15 | 15 |
| Operational series | 140 | 140 |
| Model-series rows | 2,100 | 2,100 |
| Presentable champion | 125 | 125 |
| No usable signal | 15 | 15 |
| Models leading ≥1 series | 14 | 14 |

The champion counts **sum to exactly 125**, matching `champion_visible`, which
proves the 15 no-signal series are excluded rather than silently folded in.

Cohort medians were recomputed independently for the top models and matched to
four decimals.

---

## 3. What the page will not say

Enforced by `v6_24_mf_validate_no_global_claims()` and audited against the real
rendered text:

| Term | Occurrences | All inside |
|---|---|---|
| MASE / RMSSE | 1 each | *"The previous section also relied on … None of those has a successor artifact in V6.24"* |
| global champion | 3 | *"does not select a global champion"*, *"no global winner"* |
| head-to-head | 2 | *"No head-to-head result"*, *"not a head-to-head tournament"* |
| pairwise evidence | 1 | *"V6.24 carries no pairwise evidence"* |
| bootstrap support | 1 | *"No bootstrap support"* |
| tournament winner | **0** | — |
| "ETS Explicit is the champion" | **0** | — |

Zero assertive uses. The page states plainly that it does not compute a
tournament, does not select a global champion, and that Ranking Diagnostics and
Champion FULL are later stages.

---

## 4. A guard bug I had to fix twice

The first claim guard was a substring scan. It flagged the page's **own
disclaimers** — the same failure mode that bit me in P9E (a "points-only" check
matching the word inside a comment) and P9G (a horizon check matching "4-year"
inside the denial). Third time for this pattern.

Fixed by dropping sentences that carry a denial or absence marker before
scanning. Then a second defect appeared immediately: the sentence splitter
treated `:` as a terminator, so *"Absent from V6.24:"* was separated from its
own list and the list got scanned as a claim. Colons no longer split.

Now verified in both directions: it flags genuine claims and stays clean on all
approved wording and all six assistant answers.

---

## 5. What I deliberately did not do

- **No Ranking Diagnostics, no Champion FULL** — P9L and P9M
- **No tournament, no pairwise, no global champion** — those artifacts do not
  exist and computing them is forbidden
- **No change to legacy Models** or to any V6.24 MVP page
- **No downloads**

---

## 6. Known caveats

1. **Ordering is by median MAE for readability.** Median MAE and median WAPE do
   not agree, and the page says so. Q1.
2. **The champion-count chart lives on Universe.** It is championship evidence;
   P9M owns the per-series detail. Q2.
3. **The legacy Champion page still shows its own Plotly chart.** That is
   legacy code, deliberately untouched.

---

## 7. Next stage

**READY_FOR_P9L_RANKING_DIAGNOSTICS.**

P9L should build the honest replacement for the old Tournament: cohort medians
and championship counts, explicitly not a head-to-head competition. The helper
functions and the claim guard it needs already exist.

`V6_24_P9K_MODELS_FULL_UNIVERSE_COMPLETED`

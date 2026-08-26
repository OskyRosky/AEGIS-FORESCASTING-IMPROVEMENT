# V6.24-P9K — Models FULL Universe: design summary

## What was built

A new sidebar group **Models FULL** with one page, **Universe**, alongside the
untouched legacy **Models** group.

```
Models            (legacy, unchanged)   Universe · Tournament · Champion
V6.24 MVP         (unchanged)           Overview · Viewer · Accuracy · Forecast · Taxonomy
Models FULL       (new)                 Universe
```

## Page structure

| Block | Content | Source |
|---|---|---|
| A | Scope disclosure — what the page is and what it does **not** claim | live counts |
| B | *How to read this universe* — 7 explanatory points | static |
| C | *What changed from the previous model section* — comparison table | P9J facts vs live counts |
| D | *Model families compared* — 4 display families, governed family beside each model | both classifications |
| E | Eight summary cards | accuracy_metrics + navigation_contract |
| F | Universe table, one row per governed model | accuracy_metrics |
| G | Series-level champion count chart (Highcharter bar) | navigation_contract |
| H | What comes next — Ranking Diagnostics, Champion FULL | static |
| I | Evidence-aware assistant, 6 prompts | P9G pattern |

## Three design decisions

**1. The model list is read, not declared.** `v6_24_mf_model_list()` reads
`accuracy_metrics` and reconciles it against the P9D registry, so a drift
between the two surfaces as a validation failure instead of being hidden by a
hardcoded vector.

**2. Both family classifications are shown.** The artifact's `model_family` is
3-valued (Baseline 7 / Challenger 5 / Neural 3). The four display families come
from the P9D map. They **cut across** each other — ETS Explicit is a Challenger
shown under Statistical, LinearRegression is a Baseline shown under Machine
Learning. Showing only the display grouping would let it be mistaken for
methodology, so each model carries its governed family beside it.

**3. Medians, never means.** `v6_24_mf_universe_table()` contains zero calls to
`mean()`. On this cohort LinearRegression has a mean MAE of **5.86e21** against
a median of **870**.

## What the page refuses to say

Per P9J decisions D3, D5 and D8, and enforced by
`v6_24_mf_validate_no_global_claims()`:

- no head-to-head or bootstrap result as current evidence
- no global champion
- no MASE or RMSSE as a current V6.24 metric
- the champion column is labelled **series-level**, never global
- the ordering is stated as readability, not a standing

Where those terms appear at all, they appear inside a denial or in the labelled
list of what the previous section relied on and V6.24 does not carry.

## The claim guard, and why it had to be context-aware

The first version was a plain substring scan. It flagged the page's own
disclaimers — *"this is not a head-to-head tournament"* contains
`head-to-head`, and *"Absent from V6.24: MASE, RMSSE"* contains both metrics
while asserting their absence.

The guard now splits text into sentences, drops any sentence carrying a denial
or absence marker, and scans only what remains. A second defect surfaced
immediately: splitting on `:` separated *"Absent from V6.24:"* from its own
list, so the list was scanned as a claim. Colons no longer split.

Verified both ways: it flags real claims (`"ETS Explicit is the champion."`,
`"The median MASE is 6.90."`) and stays clean on all approved wording and on
every one of the six assistant answers.

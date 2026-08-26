# V6.24 P9M - Champion FULL, design summary

## What this page replaces

The legacy **Models -> Champion** page states that ETS Explicit was selected as
champion. That decision covered 13 models over 39 HDD entities. Champion FULL
replaces it for the V6.24 cohort of 140 series and 15 governed models.

## The central decision: no global champion

V6.24 contains **no cohort-wide champion artifact**. `navigation_contract`
records `champion_model_name` and `champion_visible` **per series**. The page
therefore reports a distribution, never a single name, and one card states
plainly that the champion for the whole cohort is *not defined in V6.24*.

- 125 of 140 series have a presentable champion.
- 14 different models lead at least one series.
- The most frequent leader, FixedGrowth_6, leads 21 series
  (16.8% of presentable) - a count, not a decision.
- ETS Explicit, the legacy champion, is the presentable champion on
  **6 of 125** series. It appears on 21 contract rows, but
  15 of those are suppressed no-signal series where the
  tie-break assigns it.

## The visibility gate

15 series carry `NO_SIGNAL_ALL_ZERO_ACTUALS`. Every observed actual is
zero, so a model predicting zero scores a perfect error without having modelled
anything - all 195 rows with an error of exactly zero
belong to these series. For them `champion_visible` is FALSE and the page shows
no champion at all, only the tie-break model explicitly labelled as not
presentable.

## Shared selection

The series is chosen once, in **V6.24 MVP -> Viewer**. `selected_series()` is
exposed from the MVP server and passed into the Models FULL server. Champion
FULL follows it and never writes back. When nothing is selected it discloses
that and offers its own selector over all 140 series.

## What this page deliberately does not do

- It does not name a champion for the cohort.
- It does not rank models against each other; that is Ranking Diagnostics.
- It does not recompute champions, rankings or the visibility gate.
- It does not present a no-signal tie-break as a recommendation.

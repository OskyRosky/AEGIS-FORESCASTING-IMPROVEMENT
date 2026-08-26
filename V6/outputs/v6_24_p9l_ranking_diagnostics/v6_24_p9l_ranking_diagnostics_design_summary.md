# V6.24-P9L - Ranking Diagnostics design summary

## Structure
A Disclosure - not a tournament, plus scope
B Guide accordion - 6 explanatory points
C Setup - measure / family / ordering + Analyze (pending vs applied)
D Cards - 9, including an explicit disagreement card
E Diagnostic comparison table (DT, 13 columns)
F Diagnostic median chart (Highcharter bar)
G Series-level champion count chart (Highcharter bar, sums to 125)
H Where the measures disagree (DT position table)
I Evidence-aware assistant, 7 prompts

## Why two headlines instead of one
The legacy page could name a winner because it held pairwise bootstrap
evidence. V6.24 does not. Reporting one ordering would imply a decision that
was never made, so the page reports the lowest diagnostic median and the model
leading the most series separately, and states plainly when they differ - which
on this cohort is always.

## Why a position table for disagreement
A heatmap was permitted. A position table was chosen because it answers the
question directly: how far does a model move depending on the measure used.
ARIMA_Fixed moves 10 places between MAE and WAPE.

## Read-only guarantees
No pairwise, no bootstrap, no p-value, no MASE/RMSSE, no global champion, no
ranking recalculation. Zero mean() calls. Champion counts gated on
champion_visible so the 15 no-signal series cannot inflate them.

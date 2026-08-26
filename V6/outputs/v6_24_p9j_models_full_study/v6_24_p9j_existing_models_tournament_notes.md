# P9J — Notes on the existing Tournament page

## What "tournament" means in the legacy implementation

A **governed bootstrap pairwise competition**, computed offline by the
tournament engine and only loaded by Shiny.

- `tournament_pairwise_evidence.csv` — 78 rows = C(13,2) ordered pairs.
  Each row carries `median_delta_mase`, `bootstrap_ci_low/high`,
  `sign_test_p_value`, `bh_adjusted_p_value`, `practical_threshold`,
  `practically_meaningful`, `statistically_supported`, `comparison_status`.
- `tournament_model_evidence_summary.csv` — per model:
  `comparisons_tested = 12`, `supported_better_count`, `supported_worse_count`,
  `inconclusive_count`, `net_supported_evidence`.
- `tournament_model_scorecard.csv` — `official_median_mase`,
  `official_median_rmsse`, guardrail statuses, `risk_status`,
  `eligible_for_champion_consideration`, `champion_exclusion_reason`.
- `tournament_preliminary_standings.csv` — 13 models with a
  `preliminary_position`.

This is a real statistical procedure: a paired bootstrap with multiple-testing
correction. `comparison_status` is one of `supported_difference` or
`inconclusive`, so the page can say a model was better, worse, or that the
evidence did not settle it.

## Is any of it computed in Shiny?

**No.** `tournament_league_data()` merges the scorecard with the evidence
summary and sorts by net supported evidence then median MASE. The comment in
`R/helpers.R` is explicit: *"No recompute, no composite score; ordering is for
readability only."* That is exactly the contract V6.24 already follows.

## What can carry over to FULL

| Element | Carries? | Why |
|---|---|---|
| Read-only load-and-order discipline | **Yes** | Already the V6.24 standard |
| Accordion guide structure | **Yes** | Good teaching layout |
| Median-based comparison | **Yes** | V6.24 also uses medians |
| Risk status / eligibility columns | Adaptable | V6.24 has caveats and signal quality instead |
| **Median MASE** | **No** | No MASE anywhere in V6.24 |
| **Median RMSSE** | **No** | No RMSSE anywhere in V6.24 |
| **Pairwise matrix** | **No** | No artifact; computing it is forbidden |
| **supported-better / worse records** | **No** | Derived from the pairwise bootstrap |
| **Preliminary standings** | **No** | V6.24 ranking is per-series only |
| **Challenger evaluation** | **No** | In V6.24 all 15 models are scored identically |

## Recommendation

Do **not** build a Tournament page in FULL. Build **Ranking Diagnostics**:

- per-model medians across the cohort (MAE, RMSE, WAPE where computable)
- championship counts per model, from `navigation_contract`
- explicit statement that this is a diagnostic summary, that there is no
  head-to-head evidence, and that medians are used because the cohort mean is
  distorted by extreme values

And disclose the absence rather than hide it: a short block saying the legacy
pairwise bootstrap covered 13 models over 39 HDD entities and has no successor
on the 140-series cohort.

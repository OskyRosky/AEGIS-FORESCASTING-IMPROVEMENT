# P9J — Models FULL parity map

Full detail in `v6_24_p9j_models_full_parity_map.csv`. Summary of the 16
required elements:

| # | Old element | Verdict | FULL target |
|---|---|---|---|
| 1 | Models sidebar group | reuse | new `Models — FULL` group, old one untouched |
| 2 | Universe landing | reuse shell | same accordions, V6.24 counts |
| 3 | Model families | adapt | show governed 3-valued AND display 4-valued |
| 4 | Model universe table | **rebuild** | medians from accuracy_metrics, not MASE |
| 5 | Tournament guide | **rewrite** | becomes a ranking-diagnostics guide |
| 6 | Tournament standings | **rename + rebuild** | cohort diagnostic, not standings |
| 7 | Pairwise evidence | **DO NOT BUILD** | no artifact; computing it is forbidden |
| 8 | Challenger evaluation | **drop** | all 15 models scored identically in V6.24 |
| 9 | Champion guide | **rewrite** | champion is per-series |
| 10 | Champion at a glance | **replace** | championship distribution across 14 models |
| 11 | Why champion was selected | **replace** | explain `P6C_RANKING_POLICY_V2` |
| 12 | Global champion wording | **BLOCKING** | ETS Explicit wins 6 of 125 — never restate |
| 13 | Per-series champion wording | **new** | visible / suppressed / no-signal |
| 14 | Assistant | replace engine | P9G evidence-aware assistant |
| 15 | Download explanation | defer | with P9G2 |
| 16 | Governance / traceability | reuse | cohort_id, ranking_policy_version |

## The three risk levels

**BLOCKING** — elements that would state something false on the new cohort:
- #12 the global champion claim
- #7 pairwise evidence, if fabricated

**HIGH** — elements whose data source vanished:
- #4 median MASE in the universe table
- #5, #6 the tournament metrics and standings
- #9, #10, #11 the champion rationale

**LOW** — pure UX that transfers cleanly:
- #1, #2, #14, #15, #16

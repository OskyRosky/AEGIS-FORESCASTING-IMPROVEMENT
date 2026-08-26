# P9J — Notes on the existing Champion page

## What the legacy Champion page claims

One **global** champion for the entire model universe: **ETS Explicit**,
"selected with conditions".

Supporting evidence, all from the 39-entity HDD tournament:
- median MASE 6.90 (lowest of 13)
- median RMSSE 1.86
- head-to-head record 8 supported-better, 0 supported-worse
- confidence: **medium**

Governance record in `champion_conditions_protocol.csv`:
- **C-001** `medium_confidence` — action MONITOR, must be displayed
- **C-002** `conditional_champion_status` — "champion with conditions, not an
  unconditional winner", action KEEP_WITH_CONDITIONS

`champion_dashboard_language.csv` holds 13 statements classified by audience as
`allowed`, `allowed_with_context` or forbidden, each with a reason and a
replacement. That is a genuinely strong governance mechanism.

## How V6.24 differs — and it is not a small difference

| | Legacy | V6.24 |
|---|---|---|
| Champion scope | one, global | **per series** |
| Where it lives | `champion_decision.csv` | `navigation_contract.champion_*` |
| Selection metric | median MASE + pairwise | governed ranking policy `P6C_RANKING_POLICY_V2` |
| Suppression | none | `champion_visible = FALSE` on 15 no-signal series |
| Distinct winners | 1 | **14** |
| ETS Explicit | THE champion | champion on **6 of 125** presentable series |

## The number that decides the rewrite

**ETS Explicit wins 6 of 125 signal-present series — under 5%.**

It shows as `champion_model_name` on 21 rows, but 15 of those are the no-signal
series where the P6C tie-break crowns it and `champion_visible` is `FALSE`.
(That coincidence is by design: `ETS Explicit` is also `V6_24_REFERENCE_MODEL`.)

Meanwhile `FixedGrowth_6` and `FixedGrowth_1_5` win 21 and 17 series.

So the legacy statement *"ETS Explicit was selected as champion with
conditions"* is not merely stale wording on the new cohort — **it is a claim the
V6.24 data contradicts.** It must not appear as a FULL claim.

## What Champion FULL should be

1. **Championship distribution** — how many series each of the 14 winning
   models leads. This is the honest global view V6.24 can support.
2. **Per-series lookup** — reuse the shared Viewer selection, as Accuracy and
   Forecast already do.
3. **Explicit suppression** — the 15 no-signal series get no champion, with the
   zero-versus-zero explanation already used in Accuracy and Forecast.
4. **Ranking policy explanation** — replace "why ETS Explicit won" with how
   `P6C_RANKING_POLICY_V2` picks a per-series champion and why the tie-break
   exists.
5. **Legacy governance history** — optionally keep the conditions and approved
   language in a clearly-labelled *historical* block, so the governance record
   is not lost while its claim is not restated.

## What must never be copied

- Any sentence naming a single global champion
- median MASE / RMSSE figures
- the 8-0 head-to-head record
- `champion_dashboard_language` statements as live product wording

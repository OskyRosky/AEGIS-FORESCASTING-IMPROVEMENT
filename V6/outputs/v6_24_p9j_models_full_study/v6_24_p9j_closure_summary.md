# V6.24-P9J — Models FULL Parity Study

**Stage:** V6.24-P9J · **STUDY ONLY** — no code, no CSS, no artifacts touched.

---

## 1. What I studied

The three legacy `Models` pages — **Universe**, **Tournament**, **Champion** —
their UI structure, their helper functions, and every artifact they read. Then
I audited what the V6.24 governed cohort can actually support.

---

## 2. The scope difference, measured

```
LEGACY   13 models  ×   39 entities  ×  HDD only
V6.24    15 models  ×  140 series    ×  CPU + HDD + IOPS + SSD
```

`tournament_model_scorecard.entity_count` is **39 for every model** — the HDD
slice from the beginning of this project.

**Only 12 models overlap.** Legacy has `FastNeuralAR_MLP` (absent from V6.24);
V6.24 has `FNAR-V2`, `NLIN-DLIN_FIXED`, `SMLP-TCN` (never in the tournament).

---

## 3. Four things the old pages need that V6.24 does not have

| Missing | Legacy role | V6.24 |
|---|---|---|
| **MASE** | primary metric | no column |
| **RMSSE** | guardrail | no column |
| **Pairwise evidence** | 78 pairs, bootstrap CI, BH-adjusted p-values | no artifact |
| **Global champion decision** | one champion for the universe | per-series only |

None can be produced inside Shiny. Each needs a governed offline computation.

---

## 4. The finding that decides the Champion page

Legacy approved language states:

> *"ETS Explicit was selected as champion with conditions."*

**In V6.24, ETS Explicit is the presentable champion on 6 of 125
signal-present series — under 5%.**

It appears as `champion_model_name` on 21 rows, but 15 are the no-signal series
where P6C's tie-break crowns it and `champion_visible` is FALSE.

Fourteen models win at least one series; `FixedGrowth_6` (21) and
`FixedGrowth_1_5` (17) lead most often.

Carrying the legacy sentence into FULL would not be stale wording — it would be
**a claim the new data contradicts**.

---

## 5. Recommendations

**Universe FULL** — fully supported. Build it.

**Tournament FULL** — **do not build a tournament.** Build **Ranking
Diagnostics**: cohort medians plus championship counts, with an explicit note
that no head-to-head evidence exists on this cohort. The word "tournament"
imports a statistical claim that was never made for the 140 series.

**Champion FULL** — build it as a **championship distribution** plus per-series
lookup plus explicit no-signal suppression. No global champion.

**Legacy governance record** — the conditions protocol and the approved-language
table are a genuinely good mechanism. Keep them as clearly-labelled *history*
rather than deleting them.

---

## 6. What still needs a decision (see the semantic decisions table)

Three are **blocking** for later stages:

- **D3** no real tournament is possible → decides P9L
- **D5** no global champion artifact → decides P9M
- **D8** the ETS Explicit claim must be dropped from FULL claims

---

## 7. Governance

- **0** Shiny files modified · **0** CSS · **0** JS · **0** files added
- **0** processed or raw artifacts modified
- Old Models section verified intact (`section_universe`, `section_tournament`,
  `section_champion` all still present)
- No SQL, no model execution, no recomputation, no new tournament, no new
  champion, no push

Proven by comparing pre- and post-stage SHA-256 hashes of all 57 R/CSS/JS files.

---

## 8. Next stage

**READY_FOR_P9K_MODELS_FULL_UNIVERSE.**

P9L and P9M are ready **with caveats** — both require the semantic decisions
above to be confirmed, because each must be built smaller and more honest than
its legacy counterpart.

`V6_24_P9J_MODELS_FULL_STUDY_COMPLETED`

# Stage 07 — V2 Models Tournament: Visual Simplification Follow-up

## Goal
Oscar rejected the previous league-view redesign as too table-heavy
("no es de mi agrado, para nada"). This follow-up adds a **prominent visual**
(bracket-inspired flow) to Models > Tournament, reorganizes the page so the
visual leads, slims the technical tables, and removes governance/policy content
that belongs on the Governance page.

Scope: **V2 only**. No data, governed artifacts, models, forecasts, tournaments,
metrics, or champion decisions were touched or recomputed.

## What changed

### New visual: "Tournament visual overview" (open)
A pure HTML/CSS, bracket-inspired **flow rail** built by `tournament_flow_ui()`
from the governed league frame (`tournament_league_data()` = scorecard +
pairwise evidence summary). Four stages with arrows narrowing toward the champion:

1. **All models enter** — 13, round-robin, with model chips (net-evidence badge each).
2. **Head-to-head** — 78 pairwise comparisons.
3. **Positive record** — the 7 models with net evidence > 0, shown as chips.
4. **Selected under conditions** — champion card: ETS Explicit, MASE 6.90,
   RMSSE 1.86, 8/0 better/worse, "Champion under conditions" tag.

A calm note banner makes the governance position explicit: it is a **visual aid**
from governed pairwise evidence; the real tournament is round-robin (not
elimination); it does **not** recompute the champion or invent scores
(no fake "57-43" round scores).

### Page reorganization (`section_tournament()`)
- Subtitle simplified.
- 5 compact summary cards: kept.
- "How to read this tournament": kept (open).
- **NEW** "Tournament visual overview": inserted (open) — leads the page.
- "Tournament League View" scoreboard: kept (open), now below the visual.
- "Governed standings table" → renamed **"Detailed governed metrics"** (collapsed).
- "Pairwise evidence (technical)" → renamed **"Head-to-head evidence details"**
  (collapsed) with an explanation of why there are 78 rows.
- **REMOVED** "Source & governance policy" collapse → replaced by a single
  italic footer sentence.

### Slimmed standings table (`tournament_standings_table()`)
Reduced from **12 to 9 columns**: Model, Origin, Family, Median MASE,
Median RMSSE, MASE guardrail, RMSSE guardrail, Eligibility, Risk.
Dropped: Coverage, Audit risk, Champion. `order` col 3 asc; left-align
targets updated to c(0,1,2,5,6,7,8).

### Styling
- New `.tflow*` classes (light + dark) and `.tess-foot-note` in custom.css.
- body.R CSS cache-buster bumped `?v=20260624a` → `?v=20260624b`.

## Files modified
- V2/shiny_app/ui/tabs.R — new `tournament_flow_ui()`; restructured `section_tournament()`.
- V2/shiny_app/R/helpers.R — slimmed `tournament_standings_table()` to 9 columns.
- V2/shiny_app/www/custom.css — new `.tflow*` + `.tess-foot-note` (light/dark).
- V2/shiny_app/ui/body.R — CSS version bump to v=20260624b.

## Files created
- stage07_..._report.md (this file)
- stage07_..._validation.csv
- stage07_..._launch.csv

## Validation
- All three R files parse OK.
- Structure checks all PASS (flow builder + section, league kept, detailed
  metrics renamed/collapsed, head-to-head renamed/collapsed, policy removed,
  footer added, scatter removed, composite absent).
- App serves HTTP 200 (LEN 179788) on http://127.0.0.1:3838 (PID 3312).

## Governance confirmations
- No data files or governed artifacts modified.
- No models, forecasts, or tournaments run.
- No metrics (MASE/RMSSE/pairwise) recomputed.
- Champion decision unchanged: ETS Explicit, selected under conditions, medium confidence.
- No composite score or weighting created. Visual is labeled as an aid, not an
  official elimination bracket.

## Launch / stop
- URL: http://127.0.0.1:3838  ·  PID: 3312
- Logs: outputs/shiny_mvp/7_V2_MODELS_TOURNAMENT_VISUAL_SIMPLIFICATION_FOLLOWUP/logs
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 3312`

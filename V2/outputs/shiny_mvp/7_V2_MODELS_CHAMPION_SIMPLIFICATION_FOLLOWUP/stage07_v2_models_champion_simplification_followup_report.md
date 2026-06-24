# Stage 07 — V2 Models Champion Simplification Follow-up

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_MODELS_CHAMPION_SIMPLIFICATION_FOLLOWUP
**Active root:** V2 (V1 frozen, untouched)
**Page:** Models > Champion

## Goal
Shorten Models > Champion, remove Governance-heavy content, and make series-level
evidence clearer — especially the difference between the **global governed champion**
(ETS Explicit, selected under conditions) and **series-level local leaders**
(e.g. Theta leads the most individual series).

## Champion page — BEFORE
A long, uncollapsed wall mixing champion + governance + diagnostics:
1. Champion Decision (two rows of KPI cards — 8 cards)
2. Champion evidence
3. Governance conditions / caveats (DT)
4. Approved dashboard language
5. Source / lineage (DT)
6. Block A scope / Not implemented / No scoring layer notes
7. Series-Level Diagnostic Evidence (two rows of KPI cards)
8. Leadership count by model (plotly)
9. Series-level evidence table (DT)
10. Exceptions review (DT)
11. Diagnostic governance note

## Champion page — AFTER (all collapsible, consistent expand/collapse)
1. **Champion at a glance** (open) — compact horizontal strip: Champion, Decision,
   Median MASE, Median RMSSE, Pairwise support, Confidence. No KPI wall.
2. **Why ETS Explicit was selected** (open) — concise evidence card + info list.
3. **Series-level diagnostic evidence** (open) — intro, **global vs local dual callout**
   (ETS Explicit ★ vs Theta (8)), compact diagnostic stat strip, and the new
   **series leadership map** (39 tiles, one per series, grouped by local leader,
   ETS-led series in green).
4. **Leadership count by model** (collapsed) — plotly chart + explicit clarification
   that local leaders do not decide the global champion (Theta vs ETS Explicit).
5. **Series-level details** (collapsed) — per-series DT comparison.
6. **Local exceptions review** (collapsed) — series where ETS Explicit is not the
   local leader, largest MASE gap first.

## Sections removed from Champion
- Governance conditions / caveats (DT)
- Approved dashboard language
- Source / lineage (DT)
- Block A scope / Not implemented / No scoring layer notes
- Diagnostic governance note
(These belong in Governance / Methodology, not Champion.)

## Key conceptual clarification (Oscar's confusion)
A dedicated dual callout now states both ideas side by side:
- **Global governed champion:** ETS Explicit — selected under conditions from
  aggregated tournament evidence (lowest official median MASE, pairwise support,
  guardrails, eligibility, conditions).
- **Most frequent series-level leader:** Theta (8) — leads the most individual
  series locally; diagnostic only, does not decide or replace the global champion.

## Data sources (governed artifacts, read-only)
- champion_decision.csv
- model_lab_champion_summary.csv
- tournament_entity_model_scores.csv (39 series x 13 models = 507 rows)
No metrics recomputed; no composite score; no weights.

## Files modified
- shiny_app/ui/tabs.R (new champion_glance_ui, champion_dual_ui,
  champion_series_stat_ui, champion_series_leadership_map_ui; rewritten section_champion)
- shiny_app/www/custom.css (champ-glance, champ-dual, clead* classes, light + dark)
- shiny_app/ui/body.R (CSS cache-bust ?v=20260624e)
- shiny_app/server/server.R (suspendWhenHidden=FALSE for the 3 champion diagnostic outputs)

## Validation
section_champion smoke render: ALL_GOOD (18/18 structural checks). 39 series rows.
Top series-level leader: Theta (8). All removed sections confirmed absent.
server.R and tabs.R parse OK.

## Governance confirmations
- No data / governed artifacts modified.
- No models / forecasts / tournaments run.
- No metrics recomputed.
- Champion decision unchanged: ETS Explicit, selected under conditions.

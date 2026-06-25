# Stage 07 — V2 Models > Universe Cleanup Follow-up

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_MODELS_UNIVERSE_CLEANUP_FOLLOWUP
**Date:** 2026-06-24
**Active root:** V2 (V1 frozen, untouched)

## Objective
Declutter Models > Universe after Oscar's visual review: remove the "At a glance"
KPI cards, hide deferred deep-learning models (NBEATS, NHITS) from the visible
page, and fix the empty "Full governed model table".

## Changes
- **Removed "At a glance" KPI card block** (4 cards). Replaced with a single
  explanatory sentence inside "Model families compared".
- **Hid deferred deep-learning models** from the visible page. Visible set is now
  the 13 active models that entered the governed tournament
  (`included_in_tournament == TRUE`). NBEATS and NHITS are excluded from the
  families view and the table. The underlying artifact was NOT modified.
- **Fixed the empty table.** The previous "Full governed model table" used a DT
  widget inside a collapsed (`display:none`) section, so it never drew (classic
  hidden-htmlwidget issue). Replaced with a static HTML table
  (`universe_static_table_ui`) that renders reliably even while collapsed.
- **CSS cache bust:** `custom.css?v=20260623b` -> `?v=20260624a` (the new
  `.uni-family`/`.uni-chip` styles were being served from a stale cached file,
  which is why families looked like plain text in the review).
- Kept "How to read this universe" (open) and "Model families compared" (open,
  now styled chips). Generic deferred note added; no model names listed.

## Page structure (after)
1. Header
2. How to read this universe (collapsible, open)
3. Model families compared (collapsible, open) — intro sentence + 4 family cards with chips
4. Governed model table (collapsible, closed) — static HTML table, 13 rows

## Visible model set (13)
statistical (5), growth baseline (4), machine learning (3), lightweight neural (1).
Excluded from view: NBEATS, NHITS (deep learning, deferred).

## Scope confirmation
- No data artifacts modified. No data/processed or governed files touched.
- No models run, no forecasts generated, no tournaments rerun, no metrics recomputed.
- Champion decision unchanged (ETS Explicit, selected under conditions).
- Only Models > Universe touched. Other pages untouched.

## Files modified
- shiny_app/ui/tabs.R
- shiny_app/ui/body.R (CSS version bump only)
- shiny_app/www/custom.css

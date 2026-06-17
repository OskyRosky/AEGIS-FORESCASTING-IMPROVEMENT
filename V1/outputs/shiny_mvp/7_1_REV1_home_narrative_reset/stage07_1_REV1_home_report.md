# Stage 07 — Block 7.1-REV1 — PROJECT / Home Narrative Reset

## Summary

PROJECT / Home was rewritten from an internal, developer-oriented build-status
page into a simple, reader-friendly landing page aimed at PMs, engineers, and
business reviewers. The page now **explains the forecast improvement
methodology in plain language** instead of showing internal governance and
build-stage cards.

No other dashboard page was changed. The dashboard remains read-only: no
recompute, no model runs, no forecast generation, and no change to any governed
artifact or champion decision.

## What the new Home contains

- **A. Hero** — Title "TESSERACT v2 Forecast Improvement Platform" with a plain
  one-line subtitle.
- **B. Why this dashboard exists** — one clean prose card (no card grid)
  explaining that TESSERACT v2 currently relies on a few basic models, and this
  dashboard explores a broader, evidence-based way to forecast.
- **C. How the methodology works** — a minimal 5-step flow: historical data →
  baseline & challenger models → rolling/expanding evaluation windows →
  forecast accuracy metrics (MASE primary, RMSSE guardrail, wMAPE/SMAPE/bias
  diagnostics) → model tournament and governed recommendation.
- **D. Model families compared** — one clean list: baseline/reference,
  statistical, machine learning, deep learning candidate (no per-model list).
- **E. Where to go next** — a simple navigation guide to Overview, Universe,
  Tournament, Champion, Risks, and Explorer.
- **F. Visual review note** — reminder to review visually before the next block.

## Content removed from Home

Build-stage / Stage 07 card; Approved-with-conditions card; Read-only card;
V1 active version card; "Governed snapshot" KPI cards; ETS Explicit card;
Medium confidence card; MASE/RMSSE top-level snapshot card; Audit-ready
evidence card; Goal #3 alignment card; Read-only Evidence Layer card; No
recompute card; the governed snapshot info_list with champion metrics.

These belong in Overview, Champion, Governance, Methodology, or Version — not on
the landing page.

## Files modified

- `shiny_app/ui/tabs.R` — rewrote `section_home()`; added `home_step()` helper.
- `shiny_app/www/custom.css` — appended `.home-prose`, `.home-flow`,
  `.home-step*` styles (plus dark-theme variants). Additive only.

`shiny_app/R/helpers.R` was backed up but not modified.

## Validation

All checks in `stage07_1_REV1_home_validation.csv` are **pass**. The served Home
section contains the new narrative and none of the removed internal cards or
forbidden language ("winner", "best", "unconditional", "absolute best").

## Runtime

- URL: http://127.0.0.1:3838
- HTTP status: 200 (LEN 62195)
- Logs: `home_rev1_stdout.log`, `home_rev1_stderr.log`

## Recommendation

READY_FOR_OSCAR_VISUAL_REVIEW_7_1_REV1_HOME

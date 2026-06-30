# V4.7 — Download + Audit Local — Closure Summary

**Status:** `V4_7_DOWNLOAD_AUDIT_LOCAL_COMPLETED`
**Date:** 2026-06-29
**Scope:** 4 MVP panels only (Champion, Tournament, Forecast Viewer, Governance/Risks)
**App:** http://127.0.0.1:3839 (PID 34456) — HTTP 200

## What changed
The previous single `.md` download button was replaced by a clear, professional
**"Download explanation"** call-to-action. Clicking it opens a `modalDialog` that:

- shows the **document name** for the current section
  (e.g. `AEGIS_Explanation_Tournament_2026-06-29`);
- offers three formats: **Markdown (.md)**, **PDF (.pdf)**, **Word (.docx)**;
- has a **Close** button and a discrete governance note.

The downloaded document mirrors the **latest visible explanation** (title, asked
question, executive summary, what the evidence says, why it matters, limitations,
confidence, governance footer). **Sources used / technical traceability are
intentionally excluded** from the downloaded file — they remain collapsed in the
dashboard so the document reads cleanly.

## Format availability (runtime detection, no installs)
`.llm_export_caps()` detects local tooling at runtime:

- **MD** — always available (written directly).
- **DOCX** — enabled only if local **pandoc** is present.
- **PDF** — enabled only if local **pandoc + a LaTeX engine** are present.

On this machine pandoc / LaTeX / officer / zip are **not** installed, so PDF and
DOCX appear **disabled with a clear note** ("PDF unavailable in this local
environment." / "Word unavailable in this local environment.") and the app keeps
working. If a future local environment ships pandoc (and LaTeX for PDF), both
formats light up automatically — no code change required.

## Download samples
- `sample_md_path`: `outputs/v4_7_download_audit/AEGIS_Explanation_Tournament_2026-06-29.md`
- `sample_pdf_status`: unavailable in this local environment (no pandoc/LaTeX) — disabled with note
- `sample_docx_status`: unavailable in this local environment (no pandoc) — disabled with note
- `notes`: MD verified end-to-end for Tournament and Champion via live download; content reflects the latest composed answer; no sources/traceability included.

## Live verification
- Tournament — "How does SMLP-TCN compare to the champion?" → modal name
  `AEGIS_Explanation_Tournament_2026-06-29`; MD download 200; contains
  `SMLP-TCN at 2.72x`; no sources/traceability.
- Champion — "Should we promote the challenger to replace the champion?" → modal
  name `AEGIS_Explanation_Champion_2026-06-29`; MD download contains the bounded
  governed response ("I can only answer using the governed evidence…"), preserves
  `ETS Explicit`, recommends no promotion.

## Governance invariants (all upheld)
No SQL · no models · no Azure · no real LLM · no data/processed or data/raw
mutation · champion frozen (ETS Explicit) · governance unchanged · V1/V2/V3
untouched · scope still 4 MVP modules · no new packages installed.

## Validation
`v4_7_validation.csv` — 20/20 PASS.

## Files
- `shiny_app/R/llm_explain.R` (modified)
- `shiny_app/www/custom.css` (modified)
- `shiny_app/ui/body.R` (cache-buster v=20260629e)
- `outputs/v4_7_download_audit/` audit CSVs + sample MD + runtime logs

**Do not advance to V4.8 until visual review and authorization.**

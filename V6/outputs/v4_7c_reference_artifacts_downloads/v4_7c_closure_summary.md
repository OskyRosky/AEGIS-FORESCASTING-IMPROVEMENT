# V4.7C — Reference Artifacts LLM + Governed Download Formats — Closure Summary

**Status:** `V4_7C_REFERENCE_ARTIFACTS_DOWNLOADS_COMPLETED` — PASS (22/22)
**Date:** 2026-06-29
**Scope:** Reference / Artifacts section only + Governed Downloads. No advance to V4.8.

## What shipped

### Part A — AEGIS Explanation Assistant for Reference / Artifacts
- A new governed assistant now closes the **Reference → Artifacts** section. It explains what
  the governed artifacts are, how they relate, what they feed across the dashboard, and how to
  interpret them.
- Grounded in real registry facts: **43 governed artifacts** across **9 categories**, **42 available
  now**, **1 on the roadmap** (TTL capacity view), **8 direct governed downloads**, and **14
  section→artifact mappings** from the dashboard handoff manifest.
- 5 custom quick prompts (what they are used for / which feed the model pages / which support
  governance / a good first download / relationship between artifacts).
- Multi-format explanation download (MD/PDF/DOCX/HTML/TXT) reuses the existing local export
  tooling; the downloaded document contains **no sources or traceability** (those stay in the
  dashboard).

### Part B — Governed multi-format artifact downloads
- Each of the 8 governed downloads now opens a **per-artifact modal** offering six formats:
  - **CSV** — the canonical artifact, served **verbatim** via `file.copy` from its governed path
    (no transformation, read-only).
  - **MD / TXT / HTML** — rendered, human-readable copies with a metadata header
    (artifact, description, purpose, canonical file, source path, last modified, rows, columns)
    plus the full data table.
  - **PDF / DOCX** — the same rendered Markdown converted with local pandoc / TinyTeX, gated by
    `.llm_export_caps()` (shown with an unavailable note when the local environment lacks them).
- Defensive 200-row preview cap with a mandatory "canonical full artifact is the CSV" note;
  all governed downloads are tiny (≤15 rows) so they render in full.

## Engineering notes
- `llm_explain_ui` / `llm_explain_server` were parametrized (`panel_title`, `panel_sub`,
  `quick_prompts`). The default prompt set replicates the original input ids and query strings
  exactly, so the **9 existing assistants are unchanged** (verified live on the Tournament module).
- New file `R/artifact_export.R` (sourced in `global.R` after `llm_compose.R`) holds the readers,
  metadata, document builders, the per-artifact modal, and `register_artifact_downloads()`.
- Artifact download outputs use `suspendWhenHidden = FALSE` so the Shiny download links receive
  their URL even though the section/modal are hidden at load (fixed an empty-href issue).

## Verification (live, port 3839)
- App listening; stderr clean (NO_ERRORS); pandoc 3.10 + TinyTeX active.
- Assistant renders at the end of the section, generates a grounded answer, traceability collapsed,
  explanation MD download = 200 / no sources leak.
- Tournament scorecard downloads: CSV 200/2598B verbatim, MD 200/4038B, TXT 200/3852B,
  HTML 200/6411B, PDF 200/107916B (%PDF), DOCX 200/12692B (PK zip).
- Regression: existing Tournament assistant keeps original title/sub/4 default prompts and
  still generates a grounded answer.

## Post-review placement correction
- During closure review the AEGIS Explanation Assistant block was found to have been inserted
  inside `section_methodology()` instead of `section_artifacts()`, so it was rendering under the
  **Methodology** page.
- Fixed: the block was moved to the **end of `section_artifacts()`** (after the
  "Artifact Notes / Lineage / Evidence" group). `section_methodology()` now ends with its
  "Methodology Notes" group and no longer contains the assistant.
- Re-verified live (port 3839): the assistant renders under **Reference → Artifacts**, generates a
  grounded answer (43 artifacts / 9 categories / 8 downloads), and is **absent from Methodology**
  (`Ask AEGIS about these artifacts` not present while Methodology is shown). The 8 governed
  download modals still open with all 6 formats and valid hrefs.

## Governance invariants (held)
Champion frozen (ETS Explicit) · LLM explains, never decides · CSV canonical & verbatim ·
no silent truncation · no SQL / model recompute / Azure / real LLM / external API ·
no data/processed or data/raw mutation · V1/V2/V3 untouched.

**Do not advance to V4.8 without explicit visual review and authorization.**

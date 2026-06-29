# V4.7 Download Formats Expansion — Closure Summary

Status: **V4_7_DOWNLOAD_FORMATS_EXPANDED_COMPLETED** · 20/20 checks PASS

## What changed
The "Download explanation" modal now offers **five** formats, all enabled and
working in the local environment:

| Format | Extension | Engine | Status |
|--------|-----------|--------|--------|
| Markdown | `.md` | base R | working (zero-dep) |
| PDF | `.pdf` | pandoc + TinyTeX (LaTeX) | working (native) |
| Word | `.docx` | pandoc | working (native) |
| Web page | `.html` | base R (self-contained) | working (zero-dep) |
| Plain text | `.txt` | base R | working (zero-dep) |

## Tooling installed (user-level, no admin, authorized)
- R package `pandoc` (+ deps `gh`, `gitcreds`, `httr2`, `ini`)
- pandoc binary **3.10** → `…/AppData/Local/r-pandoc/r-pandoc/3.10/pandoc.exe`
- **TinyTeX** (LaTeX) → `…/AppData/Roaming/TinyTeX` (`pdflatex` present)

The app activates this tooling at startup (`global.R` → `.llm_ensure_pandoc()`),
setting `RSTUDIO_PANDOC` and prepending the TinyTeX bin to `PATH`, so PDF and
Word convert natively with no per-request setup.

## Governance invariants preserved
- Downloaded documents contain **no sources / no technical traceability**
  (verified for MD/HTML/TXT: `hasSources = false`).
- Each download reflects the **latest visible explanation** (handlers isolate
  the current response + question).
- Champion **frozen** = ETS Explicit. No SQL, models, forecast recompute,
  Azure, real LLM, or data mutation. V1/V2/V3 untouched.

## Live verification (V4 Shiny :3839, PID 17620)
Tournament explanation → modal `AEGIS_Explanation_Tournament_2026-06-29`:
- Markdown — HTTP 200, 1003 B, `# AE…`
- PDF — HTTP 200, 103406 B, `%PDF`
- Word — HTTP 200, 11303 B, `PK\x03\x04` (valid docx zip)
- HTML — HTTP 200, 1944 B, `<!do…`
- Plain text — HTTP 200, 1027 B, `AEGI…`

All five render as enabled download links (no disabled/unavailable states).

## Next
Pending Oscar visual review + authorization before advancing to V4.8 final
local validation.

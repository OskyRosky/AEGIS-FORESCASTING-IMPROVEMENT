# AEGIS V5.4 — Download Implementation Report

## Two download families

### A. Explanation downloads (`shiny_app/R/llm_explain.R`)
The AEGIS Explanation Assistant renders the visible explanation into 5 formats.
The document mirrors ONLY the visible content (title, question, executive
summary, evidence, why it matters, limitations, confidence, governance footer) —
sources/traceability are intentionally excluded, so no raw full data is embedded.

| Format | Builder / renderer | Toolchain |
|--------|--------------------|-----------|
| MD | `.llm_build_markdown` → `writeLines(useBytes)` | zero-dep |
| TXT | `.llm_build_txt` → `writeLines` | zero-dep |
| HTML | `.llm_build_html` (self-contained) → `writeLines` | zero-dep |
| DOCX | `.llm_render_export(md, file, 'docx')` → `rmarkdown::pandoc_convert` | pandoc |
| PDF | `.llm_render_export(md, file, 'pdf')` → `pandoc_convert` | pandoc + LaTeX |

Capability gating: `.llm_export_caps()` returns `md/html/txt = TRUE` always,
`docx = pandoc_available`, `pdf = pandoc_available && (is_tinytex || pdflatex)`.
On V5.1–V5.3 images `pdf` was FALSE (no LaTeX) → the PDF button was cleanly
disabled. V5.4 baked TinyTeX so `pdf = TRUE`.

### B. Governed downloads (`shiny_app/R/artifact_export.R`)
Each governed artifact (`ARTIFACT_DOWNLOAD_SPECS`) opens a modal offering CSV
(verbatim) + rendered MD/PDF/DOCX/HTML/TXT.

| Format | Builder / renderer | Toolchain |
|--------|--------------------|-----------|
| CSV | `file.copy(artifact_abs_path(key), file)` VERBATIM | none (byte copy) |
| MD | `.artifact_build_md` → `writeLines` | zero-dep |
| TXT | `.artifact_build_txt` → `writeLines` | zero-dep |
| HTML | `.artifact_build_html` → `writeLines` | zero-dep |
| DOCX | `.llm_render_export(.artifact_build_md, file, 'docx')` | pandoc |
| PDF | `.llm_render_export(.artifact_build_md, file, 'pdf')` | pandoc + LaTeX |

## Write behavior (governance)
- All renderers write to the `file` argument, which in Shiny `downloadHandler`
  is a per-session **tempfile in the container tempdir (`/tmp`)**.
- `.llm_render_export` uses `tempfile(fileext='.md')` for the intermediate MD.
- **No writes** to `/app/data/processed`, `/app/data/raw`, or `/app/outputs`
  (all read-only mounts). Verified live: writes to mounts fail read-only; only
  `/tmp` is used. `data/raw` is not mounted.

## Docker relevance
The only Docker-specific risk was the LaTeX engine for PDF (pandoc was already
present). Resolved in V5.4 by baking TinyTeX + the pandoc LaTeX packages into
the image (documented rebuild, same tag `aegis-dashboard:v5.1`). No app logic
was changed.

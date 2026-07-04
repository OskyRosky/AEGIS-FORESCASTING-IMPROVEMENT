# Stage 1B — Project Documentation PDF + Shiny Viewer

Date: 2026-06-25
Status: STAGE1B_CLOSED -> READY_FOR_OSCAR_VISUAL_REVIEW
Active root: ...\AEGIS-FORESCASTING-IMPROVEMENT\V3
Scope: derive a PDF from the governed Markdown and embed/serve it in
Reference -> Methodology -> Project Documentation. Stage 1 was NOT redone. The
Architecture Diagram was not modified. No Stage 2 / pipeline / AI / model / deploy work.

## 1. Files created
- docs/methodology/_build_pdf.R  (versionable build script: governed MD -> HTML via commonmark + CSS)
- docs/methodology/aegis_v3_project_documentation.pdf  (derived artifact, 124.6 KB)
- shiny_app/www/reference/aegis_v3_project_documentation.pdf  (served copy)
- outputs/stage1b_project_documentation_pdf/report.md (this file)
- outputs/stage1b_project_documentation_pdf/validation.csv
- outputs/stage1b_project_documentation_pdf/visual_checks.csv
- (intermediate aegis_v3_project_documentation.html was generated then removed)

## 2. Files modified
- shiny_app/ui/tabs.R  (section_methodology -> Project Documentation box):
  replaced the placeholder (icon + "will be linked/embedded once available" + "Placeholder"
  tag) with a real section: governed-source note, "Open in new tab" link, "Download PDF"
  link (download attribute), and an embedded <iframe> PDF viewer. No other page touched.
  Architecture Diagram box left unchanged.

## 3. PDF generation method
- Tooling check (reported first per rules): no pandoc, no quarto, no wkhtmltopdf on PATH;
  R tinytex package present but LaTeX NOT installed (is_tinytex = FALSE). No global installs
  or environment changes were made.
- Chosen safest local route: governed Markdown -> HTML (R `commonmark`, already installed,
  professional CSS template: title block, build date, auto table of contents from H2
  headings, sections) -> PDF via Microsoft Edge headless
  (`msedge.exe --headless --disable-gpu --no-pdf-header-footer --print-to-pdf`),
  Edge already present at "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe".
- Markdown remains the single governed source; PDF is a derived artifact. No new content
  was invented; existing limitations/planned items in the MD are preserved as-is.
- Output validated as a real PDF (magic bytes = %PDF), 16 TOC entries.

## 4. PDF Shiny integration
- Embedded <iframe src="reference/aegis_v3_project_documentation.pdf"> (720px viewer).
- "Open in new tab" link (target=_blank, rel=noopener).
- "Download PDF" link (download attribute -> aegis_v3_project_documentation.pdf).
- Read-only note: "This document is generated from the governed Markdown source and is
  provided as read-only project documentation."
- Tag "V3 documentation". Project Documentation placeholder fully removed.
- Shiny serves www/ at root, so the reference path is /reference/aegis_v3_project_documentation.pdf.

## 5. HTTP validation
- http://127.0.0.1:3838 -> HTTP 200.
- http://127.0.0.1:3838/reference/aegis_v3_project_documentation.pdf -> HTTP 200,
  Content-Type application/pdf, 127547 bytes.
- http://127.0.0.1:3838/reference/aegis_v3_architecture_diagram.png -> HTTP 200 (unchanged).
- Single listener on port 3838 (PID 6712).

## 6. Visual validation
- section_methodology() rendered HTML: iframe with the PDF path present (count = 1),
  "Open in new tab" and "Download PDF" actions present, governed-source note present,
  Project Documentation placeholder text removed, Architecture Diagram image still present.
- See stage1b visual_checks.csv.

## 7. Governance confirmation
- No data artifacts, forecasts, intervals, champion, metrics, model outputs, or governance
  decisions changed. Markdown remains the governed source; PDF is derived/read-only.
- Shiny remains a strict read-only consumer. V1 and V2 untouched.

## 8. Stage 1B status
- STAGE1B_CLOSED. Project Documentation is now viewable (embedded), openable, and
  downloadable from Reference -> Methodology.

## 9. Remaining limitations
- PDF is produced by Edge headless print (no pandoc/LaTeX); it is faithful to the Markdown
  but uses HTML/CSS layout rather than a LaTeX typesetting engine.
- Embedded iframe rendering depends on the browser's built-in PDF viewer; the
  Open/Download links are provided as robust fallbacks.
- Document content inherits the Stage 1 limitations/planned items (TTL supply
  prototype/simulated, intervals calibrated to 60 days, DL model replacement planned,
  daily refresh and AI/LLM layer planned).

## 10. Next recommended step
- Stage 2 — Pipeline / Daily Refresh Benchmark (local end-to-end timing first).
  NOT the AI/LLM layer yet. Awaiting Oscar authorization.

## Stop command
powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 6712

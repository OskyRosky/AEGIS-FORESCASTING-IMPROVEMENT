# Build the derived PDF from the governed Markdown source.
# Governed source : aegis_v3_project_documentation.md  (single source of truth)
# Derived artifact: aegis_v3_project_documentation.pdf
# Pipeline        : commonmark (MD -> HTML) + professional CSS, then
#                   Microsoft Edge headless (--print-to-pdf). No global installs.
# Run from V3/docs/methodology:
#   Rscript _build_pdf.R   (writes the intermediate HTML; Edge step done by caller)

suppressWarnings(suppressMessages(library(commonmark)))

md_path   <- "aegis_v3_project_documentation.md"
html_path <- "aegis_v3_project_documentation.html"

md_text <- paste(readLines(md_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
body    <- commonmark::markdown_html(md_text, extensions = TRUE)

# Add stable ids to <h2> headings and build a table of contents from them.
slugify <- function(x) {
  x <- tolower(x)
  x <- gsub("&amp;", "and", x, fixed = TRUE)
  x <- gsub("[^a-z0-9]+", "-", x)
  x <- gsub("(^-|-$)", "", x)
  x
}
h2 <- regmatches(body, gregexpr("<h2>(.*?)</h2>", body))[[1]]
toc_items <- character(0)
for (h in h2) {
  title <- sub("<h2>(.*?)</h2>", "\\1", h)
  plain <- gsub("<[^>]+>", "", title)
  id    <- slugify(plain)
  body  <- sub(h, paste0("<h2 id=\"", id, "\">", title, "</h2>"), body, fixed = TRUE)
  toc_items <- c(toc_items, paste0("<li><a href=\"#", id, "\">", plain, "</a></li>"))
}
toc <- paste0("<nav class=\"toc\"><h2>Contents</h2><ol>",
              paste(toc_items, collapse = ""), "</ol></nav>")

css <- "
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a2433; font-size: 12px; line-height: 1.5; }
.titlepage { padding: 40px 0 18px; border-bottom: 3px solid #2E75B6; margin-bottom: 22px; }
.titlepage .kicker { color: #2E75B6; font-weight: 700; letter-spacing: .08em; font-size: 12px; text-transform: uppercase; }
.titlepage h1 { font-size: 26px; margin: 8px 0 6px; color: #132238; }
.titlepage .meta { color: #5d6d7e; font-size: 12px; }
.toc { margin: 0 0 24px; padding: 14px 18px; background: #f5f8fc; border: 1px solid #d7e3f0; border-radius: 6px; }
.toc h2 { border: none; margin: 0 0 8px; padding: 0; font-size: 14px; color: #2E75B6; }
.toc ol { margin: 0; padding-left: 20px; color: #28405e; }
.toc a { color: #28405e; text-decoration: none; }
h1, h2, h3 { color: #132238; }
h2 { font-size: 16px; margin-top: 22px; padding-bottom: 4px; border-bottom: 1px solid #e2e8f0; }
h3 { font-size: 13px; margin-top: 16px; }
p, li { font-size: 12px; }
blockquote { margin: 10px 0; padding: 8px 14px; background: #fff8e6; border-left: 4px solid #b8860b; color: #5a4500; }
code { background: #eef2f7; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; font-size: 11px; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 18px 0; }
a { color: #2E75B6; }
"

title_block <- paste0(
  "<div class=\"titlepage\">",
  "<div class=\"kicker\">AEGIS Forecasting Improvement &middot; Tesseract V3</div>",
  "<h1>Project Documentation</h1>",
  "<div class=\"meta\">Version V3 &middot; Stage 1 baseline &middot; Build 2026-06-25<br>",
  "Derived (read-only) from the governed Markdown source aegis_v3_project_documentation.md</div>",
  "</div>"
)

html <- paste0(
  "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">",
  "<title>AEGIS V3 Project Documentation</title><style>", css, "</style></head><body>",
  title_block, toc, body,
  "</body></html>"
)

writeLines(html, html_path, useBytes = TRUE)
cat("HTML_WRITTEN=", html_path, " toc_items=", length(toc_items), "\n", sep = "")

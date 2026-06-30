# =====================================================================
# AEGIS V4.6 | llm_explain.R | Shiny Local On-Demand explanation panel
# ---------------------------------------------------------------------
# GOVERNANCE CONTRACT (read-only, local-only):
#   - Reads ONLY the precomputed V4.4 mock responses
#     (outputs/v4_4_mock_provider/v4_4_mock_responses.json).
#   - Does NOT call any LLM, Azure, OpenAI or external API.
#   - Does NOT recompute metrics, run models, or generate forecasts.
#   - Does NOT change the champion decision or champion language.
#   - Explanation only: no model changes, no champion changes.
#   - If the precomputed response is missing it degrades gracefully to
#     an "Invalid / unavailable" state; it never stops the app.
#
# This module renders an on-demand explanation panel inside the 4 MVP
# sections (champion / tournament / forecast / risks). The narrative is
# produced by a local deterministic mock provider - NOT a real LLM.
# =====================================================================

# Private cache (isolated, not attached to globalenv)
.llm_explain_env <- new.env(parent = emptyenv())

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
.llm_or <- function(a, b) {
  if (is.null(a) || length(a) == 0) return(b)
  if (length(a) == 1 && is.na(a)) return(b)
  a
}

# Coerce a (possibly list) field into a clean character vector.
.llm_chr_vec <- function(x) {
  if (is.null(x)) return(character(0))
  out <- tryCatch(as.character(unlist(x, use.names = FALSE)),
                  error = function(e) character(0))
  out <- out[!is.na(out) & nzchar(trimws(out))]
  out
}

# ---------------------------------------------------------------------
# Load precomputed V4.4 mock responses once (read-only), indexed by page.
# ---------------------------------------------------------------------
llm_explain_load <- function() {
  if (!is.null(.llm_explain_env$responses)) return(invisible(TRUE))

  resp_by_id <- list()
  meta <- list()

  root <- tryCatch(find_project_root(getwd()), error = function(e) getwd())
  path <- file.path(root, "outputs", "v4_4_mock_provider",
                    "v4_4_mock_responses.json")

  if (file.exists(path) && requireNamespace("jsonlite", quietly = TRUE)) {
    doc <- tryCatch(
      jsonlite::fromJSON(path, simplifyVector = FALSE),
      error = function(e) NULL
    )
    if (!is.null(doc) && !is.null(doc$responses)) {
      for (r in doc$responses) {
        pid <- .llm_or(r$page_id, NULL)
        if (!is.null(pid)) resp_by_id[[pid]] <- r
      }
      meta$provider       <- .llm_or(doc$provider, "mock")
      meta$provider_stage <- .llm_or(doc$provider_stage, "mock_no_llm")
      meta$generated_at   <- .llm_or(doc$generated_at, "")
      meta$is_real_llm    <- isTRUE(doc$is_real_llm)
      meta$uses_azure     <- isTRUE(doc$uses_azure)
    }
  }

  .llm_explain_env$responses <- resp_by_id
  .llm_explain_env$meta      <- meta
  .llm_explain_env$path      <- path
  invisible(TRUE)
}

llm_explain_get <- function(page_id) {
  llm_explain_load()
  .llm_explain_env$responses[[page_id]]
}

# ---------------------------------------------------------------------
# V4.7 | Local download/export capability detection (read-only, cached).
# MD / HTML / TXT are always available (written with base R, zero deps).
# PDF/DOCX are enabled when the local environment ships pandoc (and, for
# PDF, a LaTeX engine). Nothing is installed at runtime; if the tools are
# absent those formats degrade to a clearly-disabled state.
# ---------------------------------------------------------------------

# Make a locally-installed pandoc / TinyTeX discoverable to rmarkdown in
# this (possibly fresh) R process. Safe to call repeatedly; cached.
.llm_ensure_pandoc <- function() {
  if (isTRUE(.llm_explain_env$pandoc_ready)) return(invisible(TRUE))

  tryCatch({
    if (!nzchar(Sys.getenv("RSTUDIO_PANDOC")) &&
        requireNamespace("pandoc", quietly = TRUE)) {
      v <- tryCatch(pandoc::pandoc_installed_latest(), error = function(e) NA)
      if (!is.null(v) && !is.na(v)) {
        pandoc::pandoc_activate(version = v, rmarkdown = TRUE)
        Sys.setenv(RSTUDIO_PANDOC = dirname(pandoc::pandoc_bin(v)))
      }
    }
    # Put the TinyTeX bin on PATH so pandoc can find pdflatex for PDF.
    if (requireNamespace("tinytex", quietly = TRUE) &&
        isTRUE(tinytex::is_tinytex())) {
      bin <- file.path(tinytex::tinytex_root(), "bin", "windows")
      if (dir.exists(bin) && !grepl(bin, Sys.getenv("PATH"), fixed = TRUE)) {
        Sys.setenv(PATH = paste(bin, Sys.getenv("PATH"), sep = .Platform$path.sep))
      }
    }
  }, error = function(e) NULL)

  .llm_explain_env$pandoc_ready <- TRUE
  invisible(TRUE)
}

.llm_export_caps <- function() {
  if (!is.null(.llm_explain_env$export_caps)) return(.llm_explain_env$export_caps)

  .llm_ensure_pandoc()

  pandoc <- tryCatch(
    requireNamespace("rmarkdown", quietly = TRUE) &&
      isTRUE(rmarkdown::pandoc_available()),
    error = function(e) FALSE
  )
  latex <- tryCatch(
    (requireNamespace("tinytex", quietly = TRUE) && isTRUE(tinytex::is_tinytex())) ||
      nzchar(Sys.which("pdflatex")) || nzchar(Sys.which("xelatex")) ||
      nzchar(Sys.which("lualatex")),
    error = function(e) FALSE
  )

  caps <- list(
    md   = TRUE,
    html = TRUE,
    txt  = TRUE,
    docx = isTRUE(pandoc),
    pdf  = isTRUE(pandoc) && isTRUE(latex)
  )
  .llm_explain_env$export_caps <- caps
  caps
}

# Friendly, section-aware base name for the downloadable document.
# e.g. AEGIS_Explanation_Tournament_2026-06-29  (extension added later)
.llm_doc_basename <- function(page_id) {
  sec <- switch(
    .llm_or(page_id, ""),
    champion_overview   = "Champion",
    tournament          = "Tournament",
    forecast_viewer     = "Forecast_Viewer",
    governance_risks    = "Governance_Risks",
    reference_artifacts = "Reference_Artifacts",
    gsub("[^A-Za-z0-9]+", "_", .llm_or(page_id, "Explanation"))
  )
  sprintf("AEGIS_Explanation_%s_%s", sec, format(Sys.Date()))
}

# ---------------------------------------------------------------------
# Quick prompts (data-driven). Each entry: button id (namespaced),
# button label, and the query text sent to the composer when clicked.
# The default set keeps the exact ids + query strings the existing
# assistants already use, so their behavior is unchanged.
# ---------------------------------------------------------------------
.LLM_DEFAULT_QUICK_PROMPTS <- list(
  list(id = "qp_takeaway",  label = "Summarize the key takeaway",
       query = "Summarize the key takeaway"),
  list(id = "qp_changed",   label = "Explain what changed",
       query = "Explain what changed"),
  list(id = "qp_risk",      label = "Explain the main risk",
       query = "Explain the main risk"),
  list(id = "qp_attention", label = "What should I pay attention to?",
       query = "What should I pay attention to?")
)

# V4.7C | Reference / Artifacts assistant prompt set. The "download first"
# query is phrased to stay in-evidence (no "should I" trigger) so it is
# answered from the governed evidence rather than refused as a decision.
.LLM_REFERENCE_ARTIFACTS_PROMPTS <- list(
  list(id = "qp_takeaway",  label = "Explain what these artifacts are used for",
       query = "Explain what these artifacts are used for"),
  list(id = "qp_changed",   label = "Which artifacts feed the model pages?",
       query = "Which artifacts feed the model pages"),
  list(id = "qp_risk",      label = "Which artifacts support governance?",
       query = "Which artifacts support governance"),
  list(id = "qp_attention", label = "What should I download first?",
       query = "A good first governed artifact to download for orientation"),
  list(id = "qp_relation",  label = "Explain the relationship between artifacts",
       query = "Explain the relationship between these artifacts")
)

# ---------------------------------------------------------------------
# UI: closing-support explanation panel (one per MVP section)
# Appears at the END of each section: the user reads the section first,
# then asks AEGIS to explain it. It closes the section, it does not
# introduce it.
# ---------------------------------------------------------------------
llm_explain_ui <- function(id, page_title, button_label = "Generate explanation",
                           panel_title = NULL, panel_sub = NULL,
                           quick_prompts = .LLM_DEFAULT_QUICK_PROMPTS) {
  ns <- NS(id)
  panel_title <- .llm_or(panel_title, "Ask AEGIS about this section")
  panel_sub   <- .llm_or(
    panel_sub,
    sprintf("Generated from the governed evidence for %s.", page_title))
  tags$div(
    class = "llm-explain",
    `data-llm-page` = id,
    tags$div(
      class = "llm-explain-head",
      tags$div(
        class = "llm-explain-titlewrap",
        tags$span(class = "llm-explain-kicker", "AEGIS Explanation Assistant"),
        tags$h3(class = "llm-explain-title", panel_title),
        tags$p(class = "llm-explain-sub", panel_sub)
      )
    ),

    # Conversational question box -----------------------------------------
    tags$div(
      class = "llm-explain-ask",
      tags$label(`for` = ns("question"), class = "llm-ask-label",
                 "Ask a question about this section"),
      tags$textarea(
        id = ns("question"),
        class = "form-control llm-ask-input",
        rows = 2,
        placeholder = "Example: What is the main takeaway from this tournament?"
      ),

      # Optional quick prompts (data-driven) -----------------------------
      tags$div(
        class = "llm-quickrow",
        tags$span(class = "llm-quick-label", "Quick prompts:"),
        lapply(quick_prompts, function(qp)
          actionButton(ns(qp$id), qp$label, class = "llm-qp"))
      ),

      tags$div(
        class = "llm-cta-row",
        actionButton(ns("explain"), "Generate explanation",
                     class = "llm-explain-btn", icon = NULL)
      )
    ),

    tags$div(class = "llm-explain-status", uiOutput(ns("status"))),
    uiOutput(ns("panel")),

    # Transparency note - discrete -----------------------------------------
    tags$div(
      class = "llm-explain-foot-badge",
      title = "Local deterministic mock. No real LLM. No Azure connected.",
      "Local mock"
    )
  )
}

# ---------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------
.llm_status <- function(step) {
  step <- suppressWarnings(as.integer(step))
  if (is.na(step) || step <= 0L) return(NULL)
  if (step >= 4L) {
    return(tags$span(class = "llm-status llm-status-ready", "Ready"))
  }
  label <- switch(as.character(step),
    "1" = "AEGIS is analyzing the governed evidence\u2026",
    "2" = "AEGIS is checking limitations\u2026",
    "3" = "AEGIS is composing the explanation\u2026",
    "Working\u2026"
  )
  tags$span(class = "llm-status llm-status-building",
            tags$span(class = "llm-spinner"), label)
}

# Strip the governed boilerplate prefix and capitalize for executive prose.
.llm_clean_summary <- function(s) {
  s <- .llm_or(s, "")
  s <- sub("^\\s*Under governed,\\s*evidence-only conditions,\\s*", "", s,
           ignore.case = TRUE)
  s <- trimws(s)
  if (nzchar(s)) substr(s, 1, 1) <- toupper(substr(s, 1, 1))
  s
}

.llm_first_sentence <- function(s) {
  s <- trimws(.llm_or(s, ""))
  if (!nzchar(s)) return(s)
  m <- regexpr("[^.]*\\.", s)
  if (m > 0) trimws(regmatches(s, m)) else s
}

# Join evidence sentences into a single flowing paragraph (no bullets).
.llm_join_prose <- function(items) {
  items <- .llm_chr_vec(items)
  if (length(items) == 0) return("")
  items <- vapply(items, function(x) {
    x <- trimws(x)
    if (nzchar(x) && !grepl("[.!?]$", x)) x <- paste0(x, ".")
    x
  }, character(1))
  paste(items, collapse = " ")
}

# Compose a question-adaptive opening paragraph from governed evidence.
# Deterministic, local, bounded to the evidence pack. Not a real LLM.
.llm_compose_intro <- function(resp, question) {
  q <- trimws(.llm_or(question, ""))
  if (!nzchar(q)) return(list(text = NULL, bounded = FALSE))

  ql   <- tolower(q)
  summ <- .llm_clean_summary(resp$summary)
  why  <- .llm_first_sentence(resp$why_it_matters)
  lims <- .llm_chr_vec(resp$limitations)
  lims <- lims[!grepl("^LLM explains", lims)]
  risk <- if (length(lims)) lims[[1]] else .llm_first_sentence(summ)

  bounded <- grepl(
    paste0("should (i|we|they)|recommend|do you (think|recommend)|\\bpromote\\b|",
           "replace the champion|which model should|\\bpredict\\b|guarantee|",
           "\\bexact\\b|\\binvest\\b|\\bbuy\\b|make the decision"),
    ql)

  if (bounded) {
    txt <- paste0(
      "I can only answer using the governed evidence available for this section. ",
      "Based on the governed artifacts currently available, this section indicates: ",
      .llm_first_sentence(summ))
    return(list(text = txt, bounded = TRUE))
  }

  lead <- if (grepl("take ?away|summar|key|main point|overall|tl;dr", ql)) {
    paste0("The main takeaway is: ", .llm_first_sentence(summ))
  } else if (grepl("chang|different|move|update|since", ql)) {
    paste0("Based on the governed artifacts currently available, this is what the ",
           "evidence indicates about change: ", summ)
  } else if (grepl("risk|danger|concern|worry|wrong|fail|caution", ql)) {
    paste0("The main point to be careful about: ", risk)
  } else if (grepl("attention|watch|focus|important|look at|notice|pay", ql)) {
    paste0("What you should pay attention to: ", why)
  } else {
    paste0("Based on the governed artifacts currently available, this section ",
           "indicates: ", .llm_first_sentence(summ))
  }
  list(text = lead, bounded = FALSE)
}

# Visible, non-blocking "thinking" card shown while the answer composes.
.llm_thinking_card <- function(step) {
  steps <- c("Analyzing the governed evidence",
             "Checking limitations",
             "Composing the explanation")
  items <- lapply(seq_along(steps), function(i) {
    cls <- if (step > i) {
      "llm-think-step llm-think-done"
    } else if (step == i) {
      "llm-think-step llm-think-active"
    } else {
      "llm-think-step llm-think-pending"
    }
    tags$li(class = cls, steps[i])
  })
  tags$div(
    class = "llm-panel llm-thinking",
    tags$div(
      class = "llm-think-head",
      tags$span(class = "llm-spinner"),
      tags$span("AEGIS is analyzing this section and composing an explanation from the governed evidence\u2026")
    ),
    tags$ul(class = "llm-think-list", items),
    tags$p(class = "llm-think-note", "Local mock \u00b7 governed evidence only.")
  )
}

# Limitations stay as a short list (2-4 bullets max).
.llm_limitations <- function(items) {
  items <- .llm_chr_vec(items)
  if (length(items) == 0) {
    return(tags$p(class = "llm-muted", "No limitations recorded."))
  }
  if (length(items) > 4) items <- items[1:4]
  tags$ul(class = "llm-bullets llm-limits",
          lapply(items, function(x) tags$li(x)))
}

# Build a downloadable Markdown copy of the composed explanation.
# V4.7: the downloadable document mirrors the VISIBLE explanation only
# (title, question, executive summary, evidence, why it matters,
# limitations, confidence, governance footer). Sources used / technical
# traceability are intentionally NOT included in the downloaded document
# - they stay collapsed in the dashboard so the file reads cleanly.
.llm_build_markdown <- function(resp, question) {
  if (is.null(resp)) {
    return("# AEGIS Explanation\n\nNo governed explanation is available for this view.\n")
  }
  q       <- trimws(.llm_or(question, ""))
  title   <- .llm_or(resp$title, "Explanation")
  conf    <- .llm_or(resp$confidence, "insufficient_evidence")
  conf_lbl <- switch(conf,
    high = "high", medium = "medium", low = "low", "insufficient evidence")
  ans     <- .comp_answer(resp, q)

  lines <- c(
    sprintf("# AEGIS Explanation \u2014 %s", title), "",
    "_Local mock \u00b7 governed evidence only \u00b7 no model or champion changes._", "")
  if (nzchar(q))           lines <- c(lines, sprintf("**Question asked:** %s", q), "")
  if (nzchar(ans$lead))    lines <- c(lines, sprintf("**AEGIS response:** %s", ans$lead), "")
  lines <- c(lines,
    "## Executive summary", ans$exec, "",
    "## What the evidence says", ans$evidence, "",
    "## Why it matters", ans$why, "",
    "## Limitations")
  lines <- c(lines,
    if (length(ans$limitations)) paste0("- ", ans$limitations) else "- None recorded.")
  lines <- c(lines, "", sprintf("**Confidence:** %s", conf_lbl), "",
    "---",
    "Local mock \u00b7 governed evidence only \u00b7 no model or champion changes.",
    "")
  paste(lines, collapse = "\n")
}

# V4.7 | Plain-text (.txt) copy of the visible explanation (zero deps).
.llm_build_txt <- function(resp, question) {
  if (is.null(resp)) return("AEGIS Explanation\n\nNo governed explanation is available for this view.\n")
  q     <- trimws(.llm_or(question, ""))
  title <- .llm_or(resp$title, "Explanation")
  conf  <- .llm_or(resp$confidence, "insufficient_evidence")
  conf_lbl <- switch(conf, high = "high", medium = "medium", low = "low",
                     "insufficient evidence")
  ans   <- .comp_answer(resp, q)

  bar <- paste(rep("=", 64), collapse = "")
  out <- c(sprintf("AEGIS EXPLANATION - %s", toupper(title)), bar,
           "Local mock - governed evidence only - no model or champion changes.", "")
  if (nzchar(q))        out <- c(out, sprintf("QUESTION ASKED: %s", q), "")
  if (nzchar(ans$lead)) out <- c(out, sprintf("AEGIS RESPONSE: %s", ans$lead), "")
  out <- c(out,
           "EXECUTIVE SUMMARY", ans$exec, "",
           "WHAT THE EVIDENCE SAYS", ans$evidence, "",
           "WHY IT MATTERS", ans$why, "",
           "LIMITATIONS")
  out <- c(out, if (length(ans$limitations)) paste0("  - ", ans$limitations) else "  - None recorded.")
  out <- c(out, "", sprintf("CONFIDENCE: %s", conf_lbl), bar)
  paste(out, collapse = "\n")
}

# V4.7 | Self-contained HTML (.html) copy of the visible explanation
# (zero deps). Opens in any browser; users can Print -> Save as PDF.
.llm_build_html <- function(resp, question) {
  esc <- function(s) {
    s <- .llm_or(s, "")
    s <- gsub("&", "&amp;", s, fixed = TRUE)
    s <- gsub("<", "&lt;",  s, fixed = TRUE)
    s <- gsub(">", "&gt;",  s, fixed = TRUE)
    s
  }
  if (is.null(resp)) {
    return(paste0("<!doctype html><html><body><h1>AEGIS Explanation</h1>",
                  "<p>No governed explanation is available for this view.</p></body></html>"))
  }
  q     <- trimws(.llm_or(question, ""))
  title <- .llm_or(resp$title, "Explanation")
  conf  <- .llm_or(resp$confidence, "insufficient_evidence")
  conf_lbl <- switch(conf, high = "high", medium = "medium", low = "low",
                     "insufficient evidence")
  ans   <- .comp_answer(resp, q)

  lims <- if (length(ans$limitations)) {
    paste0("<ul>", paste0("<li>", vapply(ans$limitations, esc, character(1)), "</li>",
                          collapse = ""), "</ul>")
  } else "<p>None recorded.</p>"

  css <- paste0(
    "body{font-family:Segoe UI,Arial,sans-serif;max-width:760px;margin:40px auto;",
    "padding:0 20px;color:#23303f;line-height:1.55}",
    "h1{font-size:22px;border-bottom:2px solid #2e75b6;padding-bottom:8px}",
    "h2{font-size:15px;color:#2e75b6;margin-top:24px}",
    ".lead{background:#eef4fb;border-left:4px solid #2e75b6;padding:10px 14px;border-radius:6px}",
    ".tag{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:#2e75b6;font-weight:700}",
    ".q{color:#46566a;font-style:italic}",
    ".conf{display:inline-block;background:#e7f4ec;color:#1e7a46;border-radius:12px;",
    "padding:3px 10px;font-size:12px;font-weight:600}",
    ".foot{margin-top:28px;font-size:11px;color:#8a97a6;border-top:1px solid #e2e8ef;padding-top:10px}")

  parts <- c(
    "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
    sprintf("<title>AEGIS Explanation - %s</title>", esc(title)),
    sprintf("<style>%s</style></head><body>", css),
    sprintf("<h1>AEGIS Explanation &mdash; %s</h1>", esc(title)))
  if (nzchar(q))        parts <- c(parts, sprintf("<p class=\"q\">Question asked: %s</p>", esc(q)))
  if (nzchar(ans$lead)) parts <- c(parts,
    sprintf("<div class=\"lead\"><div class=\"tag\">AEGIS response</div><p>%s</p></div>", esc(ans$lead)))
  parts <- c(parts,
    sprintf("<h2>Executive summary</h2><p>%s</p>", esc(ans$exec)),
    sprintf("<h2>What the evidence says</h2><p>%s</p>", esc(ans$evidence)),
    sprintf("<h2>Why it matters</h2><p>%s</p>", esc(ans$why)),
    sprintf("<h2>Limitations</h2>%s", lims),
    sprintf("<p><span class=\"conf\">Confidence: %s</span></p>", esc(conf_lbl)),
    "<div class=\"foot\">Local mock &middot; governed evidence only &middot; no model or champion changes.</div>",
    "</body></html>")
  paste(parts, collapse = "\n")
}

# V4.7 | Convert the composed Markdown into PDF or DOCX using ONLY local
# tooling (pandoc, and LaTeX for PDF). Callers must gate on
# .llm_export_caps(); this is a thin, defensive wrapper that writes the
# requested format to `file`. It never installs anything and surfaces a
# clean error if the conversion is not possible.
.llm_render_export <- function(md_text, file, fmt) {
  .llm_ensure_pandoc()
  if (!requireNamespace("rmarkdown", quietly = TRUE) ||
      !isTRUE(rmarkdown::pandoc_available())) {
    stop("Local document conversion tooling (pandoc) is not available.")
  }
  tmp_md <- tempfile(fileext = ".md")
  writeLines(md_text, con = tmp_md, useBytes = TRUE)
  on.exit(unlink(tmp_md), add = TRUE)

  to <- switch(fmt, pdf = "pdf", docx = "docx",
               stop(sprintf("Unsupported export format: %s", fmt)))
  rmarkdown::pandoc_convert(
    input  = normalizePath(tmp_md, winslash = "/"),
    to     = to,
    output = file
  )
  invisible(file)
}

# V4.7 | The download modal: shows the document name and the available
# export formats. MD is always offered; PDF/DOCX are offered only when
# the local environment supports them, otherwise they appear clearly
# disabled with a short note (the app never breaks).
.llm_download_modal <- function(ns, doc_base, caps) {
  fmt_button <- function(out_id, label, kind, available) {
    if (isTRUE(available)) {
      downloadButton(ns(out_id), label, class = "btn llm-dl-format")
    } else {
      tags$div(
        class = "llm-dl-unavail",
        tags$button(type = "button", class = "btn llm-dl-format llm-dl-disabled",
                    disabled = NA, label),
        tags$div(class = "llm-dl-note",
                 sprintf("%s unavailable in this local environment.", kind))
      )
    }
  }

  modalDialog(
    title = "Download explanation",
    tags$div(
      class = "llm-dl-modal",
      tags$p(class = "llm-dl-ready",
             "Document ready for download:"),
      tags$div(class = "llm-dl-name", doc_base),
      tags$p(class = "llm-dl-select", "Select the download format:"),
      tags$div(
        class = "llm-dl-formats",
        fmt_button("download_md",   "Markdown (.md)",  "Markdown", caps$md),
        fmt_button("download_pdf",  "PDF (.pdf)",      "PDF",      caps$pdf),
        fmt_button("download_docx", "Word (.docx)",    "Word",     caps$docx),
        fmt_button("download_html", "Web page (.html)", "HTML",    caps$html),
        fmt_button("download_txt",  "Plain text (.txt)", "Text",   caps$txt)
      ),
      tags$p(class = "llm-dl-foot",
             "Local mock \u00b7 governed evidence only \u00b7 no model or champion changes.")
    ),
    footer = modalButton("Close"),
    easyClose = TRUE
  )
}

.llm_section_block <- function(heading, body) {
  if (is.null(body)) return(NULL)
  tags$div(
    class = "llm-block",
    tags$div(class = "llm-block-h", heading),
    body
  )
}

.llm_bullets <- function(items) {
  items <- .llm_chr_vec(items)
  if (length(items) == 0) return(NULL)
  tags$ul(class = "llm-bullets", lapply(items, function(x) tags$li(x)))
}

.llm_confidence_badge <- function(conf) {
  conf <- .llm_or(conf, "insufficient_evidence")
  cls <- switch(conf,
    high   = "llm-conf llm-conf-high",
    medium = "llm-conf llm-conf-medium",
    low    = "llm-conf llm-conf-low",
    "llm-conf llm-conf-insufficient"
  )
  label <- switch(conf,
    high   = "Confidence: high",
    medium = "Confidence: medium",
    low    = "Confidence: low",
    "Confidence: insufficient evidence"
  )
  tags$span(class = cls, label)
}

# Technical traceability - collapsed by default, NOT shown in main view.
# Holds sources used, claims traceability and provider-stage detail.
.llm_technical_traceability <- function(resp) {
  sources <- .llm_chr_vec(resp$sources_used)
  claims  <- resp$claims_traceability

  src_block <- if (length(sources)) {
    tags$div(
      class = "llm-trace-sub",
      tags$div(class = "llm-trace-sub-h", "Sources used"),
      tags$ul(class = "llm-bullets", lapply(sources, function(x) tags$li(x)))
    )
  } else NULL

  claims_block <- if (!is.null(claims) && length(claims)) {
    rows <- lapply(claims, function(c) {
      tags$tr(
        tags$td(class = "llm-trace-claim", .llm_or(c$claim, "")),
        tags$td(class = "llm-trace-src",
                tags$div(tags$b("source: "), .llm_or(c$source_artifacts, "")),
                tags$div(tags$b("fields: "), .llm_or(c$evidence_fields, "")),
                tags$div(tags$b("pack: "),   .llm_or(c$evidence_pack, "")))
      )
    })
    tags$div(
      class = "llm-trace-sub",
      tags$div(class = "llm-trace-sub-h", "Claims traceability"),
      tags$table(
        class = "llm-trace-table",
        tags$thead(tags$tr(tags$th("Claim"), tags$th("Maps to"))),
        tags$tbody(rows)
      )
    )
  } else NULL

  tags$details(
    class = "llm-collapse llm-technical",
    tags$summary("Technical traceability"),
    src_block,
    claims_block,
    tags$p(class = "llm-trace-meta",
           "Provider stage: local deterministic mock (mock_no_llm) \u00b7 ",
           "no real LLM \u00b7 no Azure connected.")
  )
}

.llm_governance_footer <- function() {
  tags$div(
    class = "llm-gov-footer",
    "Local mock \u00b7 governed evidence only \u00b7 no model or champion changes."
  )
}

# V4.7 | Visible call-to-action. It no longer downloads directly; it
# opens a modal that offers MD / PDF / DOCX for the CURRENT explanation.
.llm_download_row <- function(ns) {
  tags$div(
    class = "llm-download",
    actionButton(ns("dl_open"), "Download explanation",
                 class = "llm-download-btn", icon = icon("download"))
  )
}

# Full panel render from a precomputed response object. The visible
# narrative is COMPOSED at runtime from the evidence pack + question by
# the local composition engine (.comp_answer); it is not a stored echo.
.llm_render_panel <- function(resp, ns, question = NULL) {
  if (is.null(resp)) {
    return(tags$div(
      class = "llm-panel llm-panel-invalid",
      tags$p(class = "llm-invalid-msg",
             "The governed evidence for this view is not available right now, ",
             "so nothing can be shown."),
      .llm_governance_footer()
    ))
  }

  conf <- .llm_or(resp$confidence, "insufficient_evidence")
  is_insufficient <- identical(conf, "insufficient_evidence")

  title <- .llm_or(resp$title, "Explanation")
  q <- if (is.null(question)) "" else trimws(question)

  ans <- .comp_answer(resp, q)

  asked_block <- if (nzchar(q)) {
    tags$div(
      class = "llm-asked",
      tags$span(class = "llm-asked-label", "Question asked: "),
      tags$span(class = "llm-asked-text", q)
    )
  } else NULL

  answer_lead <- if (!is.null(ans$lead) && nzchar(ans$lead)) {
    cls <- if (isTRUE(ans$bounded)) {
      "llm-answer-lead llm-answer-bounded"
    } else {
      "llm-answer-lead"
    }
    tags$div(class = cls,
             tags$div(class = "llm-answer-tag", "AEGIS response"),
             tags$p(ans$lead))
  } else NULL

  body_sections <- if (is_insufficient) {
    tags$div(
      class = "llm-block llm-block-insufficient",
      tags$div(class = "llm-block-h", "Insufficient evidence"),
      tags$p(.llm_or(ans$exec,
        "There is not enough governed evidence to compose an explanation for this view."))
    )
  } else {
    tagList(
      .llm_section_block("Executive summary", tags$p(ans$exec)),
      .llm_section_block("What the evidence says", tags$p(ans$evidence)),
      .llm_section_block("Why it matters", tags$p(ans$why)),
      .llm_section_block("Limitations", .llm_limitations(ans$limitations)),
      tags$div(class = "llm-confwrap", .llm_confidence_badge(conf))
    )
  }

  tags$div(
    class = "llm-panel",
    asked_block,
    answer_lead,
    tags$h4(class = "llm-panel-title", title),
    body_sections,
    .llm_technical_traceability(resp),
    .llm_download_row(ns),
    .llm_governance_footer()
  )
}

# ---------------------------------------------------------------------
# Server: on-demand load + visible "thinking" + render (no compute, no
# LLM, no Azure). The thinking sequence is a local, non-blocking timer
# that walks Reading -> Checking -> Composing -> Ready.
# ---------------------------------------------------------------------
llm_explain_server <- function(id, page_id,
                               quick_prompts = .LLM_DEFAULT_QUICK_PROMPTS) {
  moduleServer(id, function(input, output, session) {
    ns <- session$ns

    rv <- reactiveValues(step = 0L, resp = NULL, question = "", ticking = FALSE)

    start_thinking <- function(q) {
      rv$question <- trimws(.llm_or(q, ""))
      rv$resp     <- tryCatch(llm_explain_get(page_id), error = function(e) NULL)
      rv$step     <- 0L
      rv$ticking  <- TRUE
    }

    observeEvent(input$explain, {
      q <- tryCatch(trimws(.llm_or(input$question, "")), error = function(e) "")
      start_thinking(q)
    }, ignoreInit = TRUE)

    # Optional quick prompts (data-driven) - each composes a bounded,
    # governed answer using the prompt's query text.
    lapply(quick_prompts, function(qp) local({
      qid <- qp$id; qq <- qp$query
      observeEvent(input[[qid]], start_thinking(qq), ignoreInit = TRUE)
    }))

    # Visible, non-blocking thinking driver. Depends only on rv$ticking;
    # the step read/write is isolated so it advances on the timer, not in
    # a tight loop.
    observe({
      if (!isTRUE(rv$ticking)) return()
      invalidateLater(600, session)
      isolate({
        if (rv$step < 4L) rv$step <- rv$step + 1L
        if (rv$step >= 4L) rv$ticking <- FALSE
      })
    })

    output$status <- renderUI(.llm_status(rv$step))

    output$panel <- renderUI({
      step <- rv$step
      if (is.null(step) || step <= 0L) return(NULL)
      if (step < 4L) return(.llm_thinking_card(step))
      .llm_render_panel(rv$resp, ns, rv$question)
    })

    # V4.7 | "Download explanation" opens a modal with the available
    # formats for the CURRENT (latest) explanation. The modal is only
    # reachable after a panel has rendered, so rv$resp is already set.
    observeEvent(input$dl_open, {
      showModal(.llm_download_modal(ns, .llm_doc_basename(page_id),
                                    .llm_export_caps()))
    }, ignoreInit = TRUE)

    # All handlers read the LATEST explanation via isolate(rv$*), so the
    # download always reflects the currently visible answer - never an
    # older precomputed one.
    output$download_md <- downloadHandler(
      filename = function() paste0(.llm_doc_basename(page_id), ".md"),
      content = function(file) {
        writeLines(
          .llm_build_markdown(isolate(rv$resp), isolate(rv$question)),
          con = file, useBytes = TRUE
        )
      }
    )

    output$download_pdf <- downloadHandler(
      filename = function() paste0(.llm_doc_basename(page_id), ".pdf"),
      content = function(file) {
        md <- .llm_build_markdown(isolate(rv$resp), isolate(rv$question))
        .llm_render_export(md, file, "pdf")
      }
    )

    output$download_docx <- downloadHandler(
      filename = function() paste0(.llm_doc_basename(page_id), ".docx"),
      content = function(file) {
        md <- .llm_build_markdown(isolate(rv$resp), isolate(rv$question))
        .llm_render_export(md, file, "docx")
      }
    )

    output$download_html <- downloadHandler(
      filename = function() paste0(.llm_doc_basename(page_id), ".html"),
      content = function(file) {
        writeLines(
          .llm_build_html(isolate(rv$resp), isolate(rv$question)),
          con = file, useBytes = TRUE
        )
      }
    )

    output$download_txt <- downloadHandler(
      filename = function() paste0(.llm_doc_basename(page_id), ".txt"),
      content = function(file) {
        writeLines(
          .llm_build_txt(isolate(rv$resp), isolate(rv$question)),
          con = file, useBytes = TRUE
        )
      }
    )

    # CRITICAL: this dashboard hides inactive sections via CSS. Without
    # suspendWhenHidden = FALSE the module outputs are suspended while the
    # section is hidden and never render when the user clicks.
    outputOptions(output, "status",        suspendWhenHidden = FALSE)
    outputOptions(output, "panel",         suspendWhenHidden = FALSE)
    outputOptions(output, "download_md",   suspendWhenHidden = FALSE)
    outputOptions(output, "download_pdf",  suspendWhenHidden = FALSE)
    outputOptions(output, "download_docx", suspendWhenHidden = FALSE)
    outputOptions(output, "download_html", suspendWhenHidden = FALSE)
    outputOptions(output, "download_txt",  suspendWhenHidden = FALSE)
  })
}

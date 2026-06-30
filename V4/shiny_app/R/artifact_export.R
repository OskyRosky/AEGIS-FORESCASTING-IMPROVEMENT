# =====================================================================
# artifact_export.R  |  V4.7C - Governed multi-format artifact downloads
# ---------------------------------------------------------------------
# Each governed download (ARTIFACT_DOWNLOAD_SPECS) can be opened in a
# multi-format modal:
#   - CSV  : the canonical artifact, served VERBATIM (file.copy, no
#            transformation). This is always available.
#   - MD / TXT / HTML : rendered, human-readable copies built locally
#            from the same governed data (metadata header + table).
#   - PDF / DOCX : the same rendered Markdown converted with local
#            pandoc / LaTeX, gated by .llm_export_caps().
#
# Rendered copies show a clear preview-cap note if a (very large) table
# is capped; the canonical full artifact is always the CSV. Governed
# CSVs here are tiny (<= 15 rows) so they render in full.
#
# Read-only contract: no recomputation, no mutation. The CSV is served
# exactly as produced by the Model Lab.
# =====================================================================

# Defensive preview cap for rendered (MD/TXT/HTML/PDF/DOCX) tables.
# The governed download set is tiny, so this never trips in practice.
.ART_PREVIEW_CAP <- 200L

# Friendly base file name for a rendered artifact document (no ext).
.artifact_doc_base <- function(spec) {
  nm <- gsub("[^A-Za-z0-9]+", "_", .llm_or(spec$label, spec$key))
  nm <- gsub("^_+|_+$", "", nm)
  sprintf("AEGIS_Artifact_%s_%s", nm, format(Sys.Date()))
}

# Gather everything a rendered document needs about one artifact.
.artifact_meta <- function(spec) {
  key <- spec$key
  df  <- tryCatch(load_csv_artifact(key), error = function(e) data.frame())
  if (!is.data.frame(df)) df <- data.frame()

  src <- tryCatch(artifact_abs_path(key), error = function(e) NA_character_)

  rel <- NA_character_
  reg <- artifact_registry_view()
  if (is.data.frame(reg) && all(c("artifact_key", "rel_path") %in% names(reg))) {
    row <- reg[reg$artifact_key == key, , drop = FALSE]
    if (nrow(row) > 0) rel <- as.character(row$rel_path[[1]])
  }

  mtime <- NA_character_
  if (!is.na(src) && nzchar(src) && file.exists(src)) {
    mtime <- tryCatch(
      format(file.info(src)$mtime, "%Y-%m-%d %H:%M"),
      error = function(e) NA_character_)
  }

  list(
    key      = key,
    name     = .llm_or(spec$label, key),
    desc     = .llm_or(spec$desc, ""),
    rel      = .llm_or(rel, paste0(key, ".csv")),
    date     = .llm_or(mtime, "not recorded"),
    ncol     = ncol(df),
    nrow     = nrow(df),
    cols     = names(df),
    df       = df,
    filename = tryCatch(artifact_download_filename(key),
                        error = function(e) paste0(key, ".csv"))
  )
}

# --- small cell/table renderers --------------------------------------
.art_cell <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""
  x
}

# Markdown pipe table (also used as the source for PDF/DOCX via pandoc).
.artifact_md_table <- function(df, cap = .ART_PREVIEW_CAP) {
  if (!is.data.frame(df) || nrow(df) == 0L || ncol(df) == 0L)
    return("_No rows recorded._")
  n    <- nrow(df)
  show <- df[seq_len(min(n, cap)), , drop = FALSE]
  cols <- names(show)
  esc  <- function(v) gsub("\\|", "\\\\|", gsub("[\r\n]+", " ", .art_cell(v)))
  header <- paste0("| ", paste(esc(cols), collapse = " | "), " |")
  sep    <- paste0("| ", paste(rep("---", length(cols)), collapse = " | "), " |")
  rows   <- vapply(seq_len(nrow(show)), function(i)
    paste0("| ", paste(esc(unlist(show[i, , drop = TRUE], use.names = FALSE)),
                       collapse = " | "), " |"),
    character(1))
  paste(c(header, sep, rows), collapse = "\n")
}

# HTML table.
.artifact_html_table <- function(df, cap = .ART_PREVIEW_CAP) {
  if (!is.data.frame(df) || nrow(df) == 0L || ncol(df) == 0L)
    return("<p><em>No rows recorded.</em></p>")
  n    <- nrow(df)
  show <- df[seq_len(min(n, cap)), , drop = FALSE]
  esc  <- function(v) {
    v <- .art_cell(v)
    v <- gsub("&", "&amp;", v, fixed = TRUE)
    v <- gsub("<", "&lt;",  v, fixed = TRUE)
    v <- gsub(">", "&gt;",  v, fixed = TRUE)
    v
  }
  thead <- paste0("<th>", esc(names(show)), "</th>", collapse = "")
  body  <- vapply(seq_len(nrow(show)), function(i) {
    cells <- paste0("<td>", esc(unlist(show[i, , drop = TRUE], use.names = FALSE)),
                    "</td>", collapse = "")
    paste0("<tr>", cells, "</tr>")
  }, character(1))
  paste0("<table class=\"artifact-table\"><thead><tr>", thead,
         "</tr></thead><tbody>", paste(body, collapse = ""),
         "</tbody></table>")
}

# Plain-text table (monospace-friendly pipe layout).
.artifact_txt_table <- function(df, cap = .ART_PREVIEW_CAP) {
  if (!is.data.frame(df) || nrow(df) == 0L || ncol(df) == 0L)
    return("No rows recorded.")
  n    <- nrow(df)
  show <- df[seq_len(min(n, cap)), , drop = FALSE]
  lines <- c(paste(names(show), collapse = " | "))
  for (i in seq_len(nrow(show))) {
    lines <- c(lines, paste(.art_cell(unlist(show[i, , drop = TRUE],
                                             use.names = FALSE)),
                            collapse = " | "))
  }
  paste(lines, collapse = "\n")
}

.artifact_purpose <- function(meta) {
  "Governed artifact consumed by the dashboard. This rendered copy is for human reading only; the canonical full artifact is the CSV, served verbatim."
}

.artifact_cap_note <- function(meta) {
  if (meta$nrow > .ART_PREVIEW_CAP) {
    sprintf(paste0("This rendered format includes a preview of the first ",
                   "%d of %d rows. The canonical full artifact is available ",
                   "as CSV."), .ART_PREVIEW_CAP, meta$nrow)
  } else NA_character_
}

# --- document builders -----------------------------------------------
.artifact_build_md <- function(spec) {
  m    <- .artifact_meta(spec)
  note <- .artifact_cap_note(m)
  lines <- c(
    sprintf("# Governed Artifact - %s", m$name), "",
    "_Read-only governed artifact - rendered for human reading - the canonical file is the CSV._", "",
    sprintf("- **Artifact:** %s", m$name),
    sprintf("- **Description:** %s", m$desc),
    sprintf("- **Purpose:** %s", .artifact_purpose(m)),
    sprintf("- **Canonical file:** %s", m$filename),
    sprintf("- **Source path:** %s", m$rel),
    sprintf("- **Last modified:** %s", m$date),
    sprintf("- **Rows:** %d", m$nrow),
    sprintf("- **Columns (%d):** %s", m$ncol,
            if (length(m$cols)) paste(m$cols, collapse = ", ") else "(none)"),
    ""
  )
  if (!is.na(note)) lines <- c(lines, sprintf("> %s", note), "")
  lines <- c(lines, "## Data", "", .artifact_md_table(m$df), "",
             "---",
             "Local governed artifact - served read-only - no recomputation.")
  paste(lines, collapse = "\n")
}

.artifact_build_txt <- function(spec) {
  m    <- .artifact_meta(spec)
  note <- .artifact_cap_note(m)
  lines <- c(
    sprintf("GOVERNED ARTIFACT - %s", toupper(m$name)),
    "Read-only governed artifact - rendered for human reading.",
    "The canonical file is the CSV.",
    "",
    sprintf("Artifact      : %s", m$name),
    sprintf("Description   : %s", m$desc),
    sprintf("Purpose       : %s", .artifact_purpose(m)),
    sprintf("Canonical file: %s", m$filename),
    sprintf("Source path   : %s", m$rel),
    sprintf("Last modified : %s", m$date),
    sprintf("Rows          : %d", m$nrow),
    sprintf("Columns (%d)   : %s", m$ncol,
            if (length(m$cols)) paste(m$cols, collapse = ", ") else "(none)"),
    ""
  )
  if (!is.na(note)) lines <- c(lines, note, "")
  lines <- c(lines, "DATA", .artifact_txt_table(m$df), "",
             "----",
             "Local governed artifact - served read-only - no recomputation.")
  paste(lines, collapse = "\n")
}

.artifact_build_html <- function(spec) {
  m    <- .artifact_meta(spec)
  note <- .artifact_cap_note(m)
  esc  <- function(v) {
    v <- as.character(v)
    v <- gsub("&", "&amp;", v, fixed = TRUE)
    v <- gsub("<", "&lt;",  v, fixed = TRUE)
    v <- gsub(">", "&gt;",  v, fixed = TRUE)
    v
  }
  note_html <- if (!is.na(note))
    sprintf("<p class=\"artifact-note\">%s</p>", esc(note)) else ""
  sprintf(paste0(
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">",
    "<title>Governed Artifact - %s</title>",
    "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:2rem;color:#1f2933;}",
    "h1{font-size:1.3rem;}.meta{margin:0 0 1rem;padding:0;list-style:none;}",
    ".meta li{margin:.15rem 0;}.artifact-note{background:#fff7e6;border:1px solid #f0c36d;",
    "padding:.5rem .75rem;border-radius:6px;}table.artifact-table{border-collapse:collapse;",
    "width:100%%;font-size:.85rem;}table.artifact-table th,table.artifact-table td{",
    "border:1px solid #d0d7de;padding:.3rem .5rem;text-align:left;}",
    "table.artifact-table thead{background:#f3f5f7;}footer{margin-top:1.5rem;color:#6b7280;",
    "font-size:.8rem;}</style></head><body>",
    "<h1>Governed Artifact - %s</h1>",
    "<p><em>Read-only governed artifact - rendered for human reading - the canonical file is the CSV.</em></p>",
    "<ul class=\"meta\">",
    "<li><strong>Artifact:</strong> %s</li>",
    "<li><strong>Description:</strong> %s</li>",
    "<li><strong>Purpose:</strong> %s</li>",
    "<li><strong>Canonical file:</strong> %s</li>",
    "<li><strong>Source path:</strong> %s</li>",
    "<li><strong>Last modified:</strong> %s</li>",
    "<li><strong>Rows:</strong> %d</li>",
    "<li><strong>Columns (%d):</strong> %s</li>",
    "</ul>%s<h2>Data</h2>%s",
    "<footer>Local governed artifact - served read-only - no recomputation.</footer>",
    "</body></html>"),
    esc(m$name), esc(m$name),
    esc(m$name), esc(m$desc), esc(.artifact_purpose(m)),
    esc(m$filename), esc(m$rel), esc(m$date), m$nrow,
    m$ncol, if (length(m$cols)) esc(paste(m$cols, collapse = ", ")) else "(none)",
    note_html, .artifact_html_table(m$df)
  )
}

# --- per-artifact multi-format download modal ------------------------
.artifact_download_modal <- function(spec, caps) {
  out <- function(suffix) paste0("dl_", spec$key, "_", suffix)
  fmt_button <- function(suffix, label, kind, available) {
    if (isTRUE(available)) {
      downloadButton(out(suffix), label, class = "btn llm-dl-format")
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
    title = "Download governed artifact",
    tags$div(
      class = "llm-dl-modal artifact-dl-modal",
      tags$p(class = "llm-dl-ready", "Document ready for download:"),
      tags$div(class = "llm-dl-name", .llm_or(spec$label, spec$key)),
      tags$p(class = "artifact-dl-modal-desc", .llm_or(spec$desc, "")),
      tags$p(class = "llm-dl-select", "Select the download format:"),
      tags$div(
        class = "llm-dl-formats",
        fmt_button("csv",  "CSV (.csv) \u00b7 canonical", "CSV",     TRUE),
        fmt_button("md",   "Markdown (.md)",     "Markdown", caps$md),
        fmt_button("pdf",  "PDF (.pdf)",         "PDF",      caps$pdf),
        fmt_button("docx", "Word (.docx)",       "Word",     caps$docx),
        fmt_button("html", "Web page (.html)",   "HTML",     caps$html),
        fmt_button("txt",  "Plain text (.txt)",  "Text",     caps$txt)
      ),
      tags$p(class = "llm-dl-foot",
             "CSV is the canonical artifact, served verbatim. MD / PDF / DOCX / HTML / TXT are rendered copies for reading.")
    ),
    footer = modalButton("Close"),
    easyClose = TRUE
  )
}

# --- server wiring: register all handlers for one artifact -----------
# Registers, for each governed download spec:
#   dl_<key>_open  -> opens the multi-format modal
#   dl_<key>_csv   -> verbatim file.copy of the canonical CSV
#   dl_<key>_md/_txt/_html -> rendered human-readable copies
#   dl_<key>_pdf/_docx     -> rendered via local pandoc/LaTeX (gated)
register_artifact_downloads <- function(input, output, session,
                                        specs = ARTIFACT_DOWNLOAD_SPECS) {
  for (.spec in specs) local({
    spec <- .spec
    key  <- spec$key

    observeEvent(input[[paste0("dl_", key, "_open")]], {
      showModal(.artifact_download_modal(spec, .llm_export_caps()))
    }, ignoreInit = TRUE)

    # CSV - canonical, verbatim copy from the governed path.
    output[[paste0("dl_", key, "_csv")]] <- downloadHandler(
      filename = function() artifact_download_filename(key),
      content  = function(file) {
        src <- tryCatch(artifact_abs_path(key), error = function(e) NA_character_)
        if (!is.na(src) && nzchar(src) && file.exists(src)) {
          file.copy(src, file, overwrite = TRUE)
        } else {
          writeLines("Governed artifact unavailable.", con = file)
        }
      }
    )

    # Rendered, human-readable copies.
    output[[paste0("dl_", key, "_md")]] <- downloadHandler(
      filename = function() paste0(.artifact_doc_base(spec), ".md"),
      content  = function(file)
        writeLines(.artifact_build_md(spec), con = file, useBytes = TRUE)
    )
    output[[paste0("dl_", key, "_txt")]] <- downloadHandler(
      filename = function() paste0(.artifact_doc_base(spec), ".txt"),
      content  = function(file)
        writeLines(.artifact_build_txt(spec), con = file, useBytes = TRUE)
    )
    output[[paste0("dl_", key, "_html")]] <- downloadHandler(
      filename = function() paste0(.artifact_doc_base(spec), ".html"),
      content  = function(file)
        writeLines(.artifact_build_html(spec), con = file, useBytes = TRUE)
    )

    # Rendered via local pandoc / LaTeX (gated by caps in the modal).
    output[[paste0("dl_", key, "_pdf")]] <- downloadHandler(
      filename = function() paste0(.artifact_doc_base(spec), ".pdf"),
      content  = function(file)
        .llm_render_export(.artifact_build_md(spec), file, "pdf")
    )
    output[[paste0("dl_", key, "_docx")]] <- downloadHandler(
      filename = function() paste0(.artifact_doc_base(spec), ".docx"),
      content  = function(file)
        .llm_render_export(.artifact_build_md(spec), file, "docx")
    )

    # The modal is inserted on demand and the section is hidden at load,
    # so keep these download outputs un-suspended; otherwise the Shiny
    # download links never receive their URL (href stays empty).
    for (sfx in c("csv", "md", "txt", "html", "pdf", "docx")) {
      outputOptions(output, paste0("dl_", key, "_", sfx),
                    suspendWhenHidden = FALSE)
    }
  })
  invisible(TRUE)
}

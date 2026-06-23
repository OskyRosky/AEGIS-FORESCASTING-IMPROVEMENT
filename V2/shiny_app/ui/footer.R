# TESSERACT v2 | footer.R | minimal clean shell footer (Block 7.0C-RESET)

app_footer <- function() {
  tags$footer(
    class = "app-footer",
    tags$span(class = "app-footer-text", "V1 \u00B7 Stage 07 \u00B7 Read-only dashboard")
  )
}

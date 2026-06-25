# TESSERACT v2 | footer.R | version and policy footer

app_footer <- function() {
  tags$footer(
    class = "app-footer",
    tags$div(
      class = "d-flex flex-wrap gap-3 justify-content-between",
      tags$span(tags$strong("Version:"), paste(APP_VERSION)),
      tags$span(tags$strong("Stage:"), APP_STAGE),
      tags$span(tags$strong("Policy:"), APP_POLICY),
      tags$span(tags$strong("Active root:"), APP_VERSION),
      tags$span(tags$strong("Audit state:"), "approved to Stage 07")
    )
  )
}

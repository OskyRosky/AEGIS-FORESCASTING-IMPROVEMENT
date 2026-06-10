# TESSERACT v2 | governance_server.R | governance placeholder outputs
governance_server <- function(input, output, session) {
  output$governance_placeholder <- renderUI({
    placeholder(
      "Forecast Governance",
      "Composite Score · Keep / Test / Replace / Review · Confidence scoring · Decision evidence",
      STAGE_LABELS$governance
    )
  })
}

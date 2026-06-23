# TESSERACT v2 | backtesting_server.R | backtesting placeholder outputs
backtesting_server <- function(input, output, session) {
  output$backtesting_placeholder <- renderUI({
    placeholder(
      "Backtesting Explorer",
      "Sliding Window · Expanding Window · Out-of-Time · Horizon-specific validation comparison",
      STAGE_LABELS$validation
    )
  })
}

# TESSERACT v2 | accuracy_server.R | accuracy placeholder outputs
accuracy_server <- function(input, output, session) {
  output$accuracy_placeholder <- renderUI({
    placeholder(
      "Accuracy Comparison",
      "MAPE · wMAPE · RMSE · MASE · Bias · slope_err · Drift - by entity and horizon bucket",
      STAGE_LABELS$accuracy
    )
  })
}

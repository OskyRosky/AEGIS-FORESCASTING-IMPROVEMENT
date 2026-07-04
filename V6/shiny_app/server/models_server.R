# TESSERACT v2 | models_server.R | models placeholder outputs
models_server <- function(input, output, session) {
  output$models_placeholder <- renderUI({
    placeholder(
      "Model Tournament",
      "Current TESSERACT models vs AutoARIMA · Theta · ETS variants · LightGBM · XGBoost",
      STAGE_LABELS$models
    )
  })
}

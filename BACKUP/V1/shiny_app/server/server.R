# TESSERACT v2 | server.R | server composition
source("server/overview_server.R")
source("server/forecast_overlay_server.R")
source("server/accuracy_server.R")
source("server/models_server.R")
source("server/backtesting_server.R")
source("server/governance_server.R")
source("server/settings_server.R")
source("modules/metric_cards/metric_cards_server.R")
source("modules/forecast_chart/forecast_chart_server.R")
source("modules/model_ranking/model_ranking_server.R")
source("modules/llm_summary/llm_summary_server.R")

app_server <- function(input, output, session) {
  overview_server(input, output, session)
  forecast_overlay_server(input, output, session)
  accuracy_server(input, output, session)
  models_server(input, output, session)
  backtesting_server(input, output, session)
  governance_server(input, output, session)
  settings_server(input, output, session)
}

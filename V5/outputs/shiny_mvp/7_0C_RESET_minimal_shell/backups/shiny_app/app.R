# TESSERACT v2 | app.R | application entrypoint
source("global.R")
source("ui/header.R")
source("ui/body.R")
source("server/server.R")

shinyApp(ui = app_ui(), server = app_server)

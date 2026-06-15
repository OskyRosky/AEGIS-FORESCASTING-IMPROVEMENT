# TESSERACT v2 | server.R | governed read-only server shell

app_server <- function(input, output, session) {
  observeEvent(input$stage07_section, {
    updateTabsetPanel(session, "stage07_tabs", selected = input$stage07_section)
  }, ignoreInit = TRUE)
}

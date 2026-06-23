# TESSERACT v2 | settings_tab.R | future settings navigation panel
settings_tab <- function() {
  nav_panel(
    "Settings",
    icon = icon("gear"),
    div(
      class = "container-fluid py-3 px-4",
      placeholder("Settings", "Reserved for future platform configuration.", "Stage 7: UI/UX + LLM")
    )
  )
}

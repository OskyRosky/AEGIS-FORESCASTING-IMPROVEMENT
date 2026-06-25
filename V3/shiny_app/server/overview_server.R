# TESSERACT v2 | overview_server.R | overview outputs
overview_server <- function(input, output, session) {
  output$kpi_entities <- renderUI({
    n <- if (!is.null(recommendations)) nrow(recommendations) else "-"
    kpi_card("Entities evaluated", n, "HDD Region + Forest")
  })

  output$kpi_improved <- renderUI({
    if (is.null(recommendations)) {
      return(kpi_card("Accuracy improved", "-", "Run setup.R"))
    }

    n_imp <- sum(recommendations$wmape_improvement_pct < 0, na.rm = TRUE)
    pct <- round(n_imp / nrow(recommendations) * 100)
    kpi_card("Accuracy improved", paste0(pct, "% up"), paste(n_imp, "of", nrow(recommendations), "entities"), "success")
  })

  output$kpi_delta <- renderUI({
    if (is.null(recommendations)) {
      return(kpi_card("Avg wMAPE delta", "-", ""))
    }

    avg <- mean(recommendations$wmape_improvement_pct, na.rm = TRUE)
    kpi_card("Avg wMAPE delta", paste0(round(avg, 1), "%"), "vs current TESSERACT", if (avg < 0) "success" else "danger")
  })

  output$kpi_best <- renderUI({
    if (is.null(recommendations)) {
      return(kpi_card("Best candidate", "-", ""))
    }

    best <- recommendations %>%
      filter(recommendation %in% c("Replace", "Test")) %>%
      count(recommended_model) %>%
      arrange(desc(n)) %>%
      slice(1)

    kpi_card("Best candidate", best$recommended_model[1], paste("Leads in", best$n[1], "entities"), "primary")
  })

  output$chart_comparison <- renderPlotly({
    build_comparison_chart(recommendations)
  })

  make_rec_box <- function(label, color) {
    renderUI({
      n <- if (!is.null(recommendations)) {
        sum(recommendations$recommendation == label, na.rm = TRUE)
      } else {
        0
      }
      rec_count_card(label, n, color)
    })
  }

  output$rec_replace <- make_rec_box("Replace", "success")
  output$rec_test <- make_rec_box("Test", "info")
  output$rec_keep <- make_rec_box("Keep", "secondary")
  output$rec_review <- make_rec_box("Review", "warning")

  output$best_model_box <- renderUI({
    req(recommendations)

    best <- recommendations %>%
      filter(recommendation %in% c("Replace", "Test")) %>%
      count(recommended_model) %>%
      arrange(desc(n)) %>%
      slice(1)

    div(
      class = "alert alert-primary py-2 mb-0",
      tags$small("BEST OVERALL CANDIDATE", class = "d-block text-primary fw-bold", style = "font-size: 10px;"),
      tags$strong(best$recommended_model[1]),
      tags$small(paste0(" · leads in ", best$n[1], " entities"), class = "text-muted")
    )
  })

  output$llm_insight <- renderText({
    get_llm_insight()
  })

  output$tbl_opportunities <- renderDT(
    build_opp_table(recommendations),
    options = list(
      pageLength = 6,
      dom = "t",
      scrollX = FALSE,
      columnDefs = list(list(className = "dt-center", targets = c(3, 4, 5)))
    ),
    rownames = FALSE,
    selection = "single"
  )
}

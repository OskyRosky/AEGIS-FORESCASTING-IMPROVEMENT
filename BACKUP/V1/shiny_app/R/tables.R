# TESSERACT v2 | tables.R | table builders
build_opp_table <- function(recommendations_data) {
  if (is.null(recommendations_data)) {
    return(data.frame(Note = "Run setup.R to generate sample data"))
  }

  recommendations_data %>%
    arrange(wmape_improvement_pct) %>%
    select(
      Entity = entity_key,
      `Current model` = current_model,
      `Proposed model` = recommended_model,
      `wMAPE Delta` = wmape_improvement_pct,
      Recommendation = recommendation,
      Confidence = confidence_level
    )
}

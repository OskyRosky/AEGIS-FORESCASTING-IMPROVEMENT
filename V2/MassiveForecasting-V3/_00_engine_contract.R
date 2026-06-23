###############################################################################
# forecast_engine/_00_engine_contract.R
#
# Propósito:
#   Definir el "contrato" (interfaces) del motor de forecasting (Fase 3),
#   sin depender de Shiny. Este archivo:
#     - Declara qué componentes soporta el motor (Total / Impuestos / Avanzado)
#     - Declara qué funciones se esperan (builders y runner)
#     - Provee una función de diagnóstico (engine_info) para trazabilidad
#
# Reproducibilidad / mantenibilidad:
#   - NO contiene lógica de modelado ni de backtesting.
#   - Solo define especificación, convenciones y puntos de entrada.
#   - Debe ser estable: si cambia, documentar el motivo.
###############################################################################

# =========================
# 1) Especificación del motor
# =========================

ENGINE_SPEC <- list(
  version = "v2.phase3",
  components = c("total", "tax", "advanced"),

  # Builders: construyen una "serie estándar" (dataframe y/o ts)
  series_builders = list(
    total    = "build_series_total()",
    tax      = "build_series_tax()",
    advanced = "build_series_advanced()"
  ),

  # Runner: corre modelos (vía registry) y retorna un bundle consumible por UI
  forecast_runner = list(
    bundle = "run_forecast_bundle(y_ts, h, model_ids, level=95, seed=123)"
  ),

  # Notas operativas (alineadas a lo acordado en Fase 3)
  notes = c(
    "Shiny consume. La cocina vive en forecast_engine + registry + helpers.",
    "Unidad oficial: millones de colones (conversion se hace en builders/caller).",
    "Ultimo mes: se incluye (dato cerrado/correcto).",
    "Ceros/negativos/NA: imputacion 3 prev + 3 next (con fallback)."
  )
)

# =========================
# 2) Diagnóstico / Trazabilidad
# =========================

engine_info <- function() {
  cat("\n=== FORECAST ENGINE INFO ===\n")
  cat("Version:", ENGINE_SPEC$version, "\n")
  cat("Components:", paste(ENGINE_SPEC$components, collapse = ", "), "\n\n")

  cat("Series builders:\n")
  for (nm in names(ENGINE_SPEC$series_builders)) {
    cat(" -", nm, "->", ENGINE_SPEC$series_builders[[nm]], "\n")
  }

  cat("\nForecast runner:\n")
  for (nm in names(ENGINE_SPEC$forecast_runner)) {
    cat(" -", nm, "->", ENGINE_SPEC$forecast_runner[[nm]], "\n")
  }

  cat("\nNotes:\n")
  for (s in ENGINE_SPEC$notes) cat(" -", s, "\n")

  invisible(ENGINE_SPEC)
}
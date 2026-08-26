# V6.24-P9B — Highcharts Migration Notes

Everything needed to replace Plotly with Highcharts in P9E and P9F.

---

## 1. There is nothing to install

`R/libraries.R` line 11:

```r
# Block 7.11 | interactive forecast charting (Forecast Viewer)
suppressPackageStartupMessages(library(highcharter))
```

`highcharter` has been a declared dependency of this app since Block 7.11, and
every legacy chart uses it: `fv_chart`, `fvp_chart`, `fvf_chart`, `acc_heatmap`,
`ttl_gauge`, `ttl_line_chart`, `ttl_heatmap`. There are 117 highcharter references
in `helpers.R` alone.

Introducing Plotly in P8 was not a technical choice — it broke an established
convention. The migration removes a dependency rather than adding one.

## 2. The reference implementation

`fvp_chart()` (helpers.R 622–717) is complete and should be ported almost
verbatim. Its pipeline:

```r
highchart() |>
  hc_chart(type = "line", zoomType = "xy",
           panning = list(enabled = TRUE), panKey = "shift",
           style = list(fontFamily = "Inter, system-ui, sans-serif")) |>
  hc_title(text = "Backtest Comparison", ...) |>
  hc_subtitle(text = "<series> · horizon <N> days · <M> models · <min> → <max>") |>
  hc_xAxis(type = "datetime", crosshair = TRUE) |>
  hc_yAxis(title = list(text = "Value"), crosshair = TRUE) |>
  hc_legend(enabled = TRUE) |>
  hc_tooltip(shared = FALSE, xDateFormat = "%Y-%m-%d", valueDecimals = 2) |>
  hc_exporting(enabled = TRUE) |>
  hc_credits(enabled = FALSE) |>
  hc_plotOptions(line = list(marker = list(enabled = TRUE, radius = 3),
                             lineWidth = 2))
```

Two owner requests are satisfied by single lines here:

- **"poder quitar series"** → `hc_legend(enabled = TRUE)`. Highcharts gives
  click-to-toggle for free.
- **export / download** → `hc_exporting(enabled = TRUE)`.

## 3. Series construction

**Actual** — reserved blue, deliberately heavier so it reads as truth:

```r
hc_add_series(name = "Actual", type = "line", color = "#10477e", lineWidth = 3,
              marker = list(enabled = TRUE, radius = 3, symbol = "circle"),
              data = list_parse2(data.frame(
                x = datetime_to_timestamp(a$date), y = round(a$value, 3))))
```

**Models** — one line each, iterated in family order so a given model keeps the
same colour between renders:

```r
.fvp_palette <- c("#d97706", "#2e9e5b", "#9b59b6", "#e0508a", "#0e7490",
                  "#b45309", "#1f77b4", "#7f8c1a", "#c0392b", "#16a085",
                  "#8e44ad", "#2c3e50", "#d35400")   # 13 colours
```

Thirteen colours for fifteen models means two would repeat if everything were
selected — which is one more reason the default selection should be small.

Per-series tooltip carries model, date, value, horizon, family and risk.

## 4. Mapping to V6.24 artifacts

Only the data accessors change. Everything above ports unchanged.

| Legacy accessor | Legacy source | V6.24 replacement |
|---|---|---|
| `fvp_actual_series(series, hist)` | `forecast_viewer_model_outputs.csv` (`date`, `actual_value`) | `actuals_normalized` (`series_date`, `actual_value`) filtered on `series_id` |
| `fvp_forecast_series(series, model, horizon)` | same file (`forecast_value`, `horizon_days`) | `model_backtests_15_models` (`target_date`, `predicted_value`) filtered on `series_id`, `model_name`, `horizon_steps` |
| `fvp_model_meta(series)` | same file (`model_family`, `is_selected_champion`, `risk_status`) | `accuracy_metrics` + `model_rankings` + `navigation_contract.champion_visible` |
| `fvf_forecast_series(series, window)` | forward parquet | `forecast_outputs` (`forecast_date`, `predicted_value`) |
| `fvf_boundary_date(series)` | forward parquet | `navigation_contract.forecast_start_date` or `forecast_outputs.train_end_date` |

**Verified**: `model_backtests_15_models.horizon_steps` exists with values 1–30,
identical in meaning to legacy `horizon_days`. The horizon selector transfers
directly.

## 5. Two V6.24-specific adaptations

**Champion star must be conditional.** `fvp_model_label()` appends `" ★ champion"`
whenever `is_selected_champion` is TRUE. V6.24 must additionally require
`champion_visible = TRUE`, so the 15 no-signal series show no star in the legend
or the checkbox list.

**Risk status has no V6.24 equivalent.** The legacy tooltip shows
`risk_status` (`ok` / `high_risk`). V6.24 has no such column. Use the caveat
context instead — `caveat_badge`, `signal_quality_status` — rather than inventing
a risk field.

## 6. The resize hook can probably go

`ui/tabs_v6_24_mvp.R` contains `v24_resize_hook()`, a JS listener firing
`window.resize` after a V6.24 sidebar click. It exists only because a Plotly widget
built inside a `display:none` container measures zero width.

Highcharts reflows more reliably on container change, and the legacy charts live
in the same CSS-toggled sections without any such hook. **P9E should test removing
it, and only remove it if the charts still draw correctly.** Do not delete it on
assumption.

The `outputOptions(suspendWhenHidden = FALSE)` calls must **stay** — the legacy
code uses the same technique at `taxonomy_navigation.R` line 532.

## 7. Removal checklist

After P9F, a source scan of the three V6.24 files must find:

- zero `plotly::` calls
- zero `plotlyOutput` / `renderPlotly`
- `highcharter::highchartOutput` / `renderHighchart` for every chart
- `hc_exporting(enabled = TRUE)` on the backtest and forecast charts
- `hc_legend(enabled = TRUE)` on both

## 8. Empty states

`fvp_empty_chart()` is a titled highchart with hidden axes and a calm grey message
— *"Select a series, choose models and horizon, then click Analyze Forecast."*

This matters with the Analyze button: between page load and the first click, the
chart area shows a deliberate invitation rather than a blank rectangle or an error.
`plotly_empty()`, which V6.24 currently uses, gives neither.

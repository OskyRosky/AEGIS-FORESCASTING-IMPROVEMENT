# V6.16 Lab Fix — Visual Review Feedback

## Review outcome

Oscar's first live review accepted the general Viewer structure but did not
accept V6.16 as closed because two product issues remained:

1. An unavailable Viewer combination displayed
   `Backtest not available for this pilot` inside the Key / Series dropdown,
   making a status message look like a selectable key.
2. Forecast still exposed the old key-first setup and did not represent the
   intended Metric -> Scenario -> Granularity -> Key / Series product logic or
   SSD-Phoenix forecast-only coverage.

The attached screenshots showed the Viewer behavior for
`HDD - Basilisk / Basilisk / Region` and the incomplete legacy Forecast panel.

## Accepted correction

V6.16 remains a lab. The fix does not authorize V6.17 or the full backtest run.

### Viewer

- Preserve the accepted eight-step unified setup.
- Keep Viewer actual-bearing only.
- Keep SSD-Phoenix out of Viewer.
- Render an empty Key / Series control for combinations outside the five cases.
- Show `Backtest not available for this pilot.` outside the dropdown.
- Preserve all 15 verified AEGIS models.

### Forecast

- Replace the key-first panel with:
  Metric -> Scenario -> Granularity -> Key / Series -> Forecast Window ->
  Actual History Window -> Analyze Forward Forecast.
- Use a prepared V6.16 artifact assembled outside Shiny.
- Include the existing 45-key HDD Enterprise/Region forward scope with actuals.
- Include SSD-Phoenix Forest for:
  - Low Volume No Efficiency
  - Low Volume With Efficiency
- Treat SSD-Phoenix honestly as forecast-only; do not fabricate actuals.

## Implementation result

The correction was implemented and browser-validated. Viewer unavailable
combinations now have zero selectable key options and the limit message is
outside the control. Forecast now reads one prepared artifact containing 78,142
rows across HDD and SSD-Phoenix. No model, Tesseract, SQL, Docker, Azure, V1-V5,
Assistant, or full-backtest execution was performed.

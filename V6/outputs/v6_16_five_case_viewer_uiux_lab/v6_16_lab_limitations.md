# V6.16 Corrected Lab Limitations

## Viewer remains a five-case pilot

Viewer proves the intended UI/UX against five prepared actual-bearing cases. It
does not provide the missing 557 HDD key-combinations and does not authorize a
596-key rebuild. An unavailable Metric / Scenario / Granularity combination
therefore shows a blank Key / Series control and the external message
`Backtest not available for this pilot.`

SSD-Phoenix is intentionally excluded from Viewer because it has no actuals.
Viewer still uses exactly 15 verified AEGIS models and horizons 1-30.

## Forecast is broader than Viewer but still bounded

The prepared Forecast lab artifact includes:

- HDD - EDB / Enterprise / Region: 45 keys, prepared actual history, and 180
  prepared forward days.
- SSD-Phoenix / Low Volume No Efficiency / Forest: 148 keys and 180 prepared
  forecast-only days.
- SSD-Phoenix / Low Volume With Efficiency / Forest: 152 keys and 180 prepared
  forecast-only days.

The SSD counts are scenario/key combinations; many keys occur in both
scenarios. SSD-Phoenix actuals do not exist and were not fabricated.

The Forecast lab does not yet include other HDD EDB scenarios/granularities,
HDD Basilisk forward cases, CPU, IOPS, SSD-MCDB, or other future metric scopes.
It freezes the latest locally prepared SSD forecast version per
scenario/key outside Shiny and does not expose a Forecast Version selector.
Prediction intervals are not carried into the V6.16 prepared Forecast artifact.

## Governance limits

- Shiny reads two productive lab inputs:
  `forecast_viewer_model_outputs_v2_pilot.csv` and
  `forecast_forward_outputs_v6_16_pilot.csv`.
- Source normalization, latest-version selection, and windowing happen in the
  external builder, not in Shiny.
- No model execution, Tesseract extraction, SQL write, Docker/Azure change,
  V1-V5 change, Assistant/LLM change, or scenario resolver wiring occurred.
- V6.17, R8-FIX-3, the four-hour budget, and the full backtest remain blocked
  pending Oscar's explicit authorization.

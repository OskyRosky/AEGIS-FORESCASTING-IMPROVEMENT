# V6.16 Five-Case Viewer Pilot Limitations

## Purpose

V6.16 is a controlled UI/UX lab. It proves the definitive unified Viewer flow
against a prepared, bounded backtest artifact. It is not evidence of full HDD
coverage and is not authorization for the full run.

## Included scope

Only these five Viewer-eligible cases are included:

1. HDD - EDB / Enterprise / Region / APC-Dedicated
2. HDD - EDB / Enterprise / Forest / NAMPRD07
3. HDD - EDB / Consumer / Region / APC-Dedicated
4. HDD - EDB / Consumer / Forest / NAMPRD07
5. HDD - Basilisk / Basilisk / Forest / namprd07

Each case has actuals, 15 verified AEGIS models, three origins, and horizons 1
through 30. The artifact contains 6,750 rows. P01 reuses governed legacy rows;
the other four cases were generated in the bounded pilot run.

## What the pilot proves

- The definitive sequence works as one setup panel:
  Metric -> Scenario -> Granularity -> Key / Series -> Horizon ->
  History Window -> Models -> Analyze Backtest.
- The dropdowns cascade across two metrics, three scenarios, two
  granularities, and case-sensitive key labels.
- All 15 verified models remain available and grouped by family.
- Actual values and selected prepared model forecasts render together.
- Horizon and History Window filter prepared rows.
- Data notes and analyzed-row downloads use the prepared pilot artifact.
- A combination outside the five prepared cases receives the clear message
  `Backtest not available for this pilot`.
- Shiny reads and filters prepared data; it does not train, backtest, extract,
  recalculate model outputs, or persist source data.

## What the pilot does not prove

- It does not prove coverage or runtime behavior for the 557 missing HDD keys.
- It does not validate a full 596-key rebuild.
- It does not establish full-run compute duration or operational stability.
- It does not fill the six missing Enterprise Region keys.
- It does not extend Basilisk history or fabricate missing observations.
- It does not add actuals for SSD-Phoenix, which remains Forecast-only.
- It does not authorize V6.17, R8-FIX-3, or any full backtest execution.

## Binding limits

The full 557-key execution remains blocked. No new Tesseract extraction, SQL
write, Docker/Azure change, V1-V5 change, Forecast redesign, Assistant/LLM
change, scenario resolver wiring, or 16th model is part of this pilot.

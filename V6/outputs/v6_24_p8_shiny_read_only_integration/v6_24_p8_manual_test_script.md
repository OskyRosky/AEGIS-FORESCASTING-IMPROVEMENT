# V6.24-P8 — Manual Test Script (for P9 visual QA)

How to run the app and what to click. Every expectation below is a **contract
field**, so if the UI disagrees with the artifact, the UI is wrong.

## Run it

```powershell
cd "C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6\shiny_app"
& "C:\Program Files\R\R-4.6.0\bin\Rscript.exe" -e "shiny::runApp('.', port=7824L, launch.browser=TRUE)"
```

Then open the **V6.24 MVP** group in the left sidebar.

---

## T1 — Overview

1. Open **V6.24 MVP → Overview**.
2. Expect the cards to read: operational series **140**, product ready **140**,
   viewer visible **140**, forecast visible **140**, ranking visible **140**,
   champion visible **125**, available **53**, available with caveat **87**,
   no-signal **15**, low-confidence window **1**.
3. Expect a persistent blue banner naming `GOVERNED_30_STEP_DAILY_FORECAST`
   and stating this is **not** a multi-year forecast.
4. Expect the "Coverage by metric" table to read HDD 50, SSD 50, CPU 20, IOPS 20.
5. **Expect no tile labelled "mean" anywhere.**

## T2 — Filter flow

1. Open **V6.24 MVP → Viewer**.
2. The first dropdown must be **Metric**, never Key.
3. Change Metric to `HDD` and confirm DB Type offers only `Basilisk` and `EDB`.
4. Change Metric to `IOPS` and confirm DB Type collapses to `NOT_APPLICABLE`
   — shown explicitly, not hidden.
5. Change Metric to `CPU` and confirm DB Type reads
   `UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE`.
6. Walk all six levels. The status line must turn green and read
   `Selected: <series_id>`.
7. **No dropdown should ever offer an option that yields no series.**

## T3 — Viewer, normal series

1. Select any `SIGNAL_PRESENT` series, e.g. Metric `CPU` → Scenario `Consumed`
   → Granularity `Region`.
2. Expect an identity block with metric, scenario, granularity, key, **key role**
   and route.
3. Expect a **Champion model** block naming the champion, the ranking metric and
   its value.
4. Expect the observed-history chart to draw.
5. Pick a model and expect the backtest chart to draw actual versus predicted.
6. Expect the ranking table to list all **15** models, ranks 1–15, with the
   champion marked.

## T4 — Viewer, no-signal series (the important one)

1. Select Metric `HDD` → DB Type `Basilisk` → Granularity `Forest` → any key.
2. Expect a red **NO_SIGNAL** badge and a **CHAMPION_NOT_MEANINGFUL** badge.
3. Expect the champion block to read
   **"Champion is not meaningful for this no-signal series."**
4. Expect the model named there to be labelled *"not a recommendation"*.
5. Expect the series to still be **fully selectable** with its charts drawing —
   a dead series must be distinguishable from a missing one.
6. In the ranking table, the top row must read **"technical only"**, not
   "champion".

## T5 — Viewer, low-confidence series

1. Select Metric `SSD` → Granularity `Forest` → Key `GBRP267`.
2. Expect a **LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO** badge.
3. Expect the caveat message to explain the series has historical signal but its
   evaluation window sits in a **zero tail**.
4. The champion is still shown here — this series is not no-signal.

## T6 — Forecast

1. Open **V6.24 MVP → Forecast** and select any series.
2. Expect `Forecast type = GOVERNED_30_STEP_DAILY_FORECAST` and
   `Forecast steps = 30`.
3. Expect the forecast window dates to differ by metric: CPU and IOPS start
   2023-07-21, SSD starts 2026-08-23, HDD varies per series. **This is correct** —
   each series forecasts from its own last observation.
4. Expect the chart to show recent observed history then exactly **30** forward
   points.
5. Expect the table to have exactly **30** rows with Negative and Extreme flag
   columns.
6. **Expect no "4-year" or "1,440-day" text anywhere.**

## T7 — Taxonomy

1. Open **V6.24 MVP → Taxonomy**.
2. Switch the scope selector through all **10** scopes.
3. `GLOBAL` must read 140. `BY_METRIC` must read 50/50/20/20.
4. Expect the note that **Key is a routing/display value, not a global canonical
   axis**.
5. Expect the caveat table to list every code with severity and `Blocking = no`.

## T8 — Nothing else broke

1. Open the legacy **Forecasting → Viewer**, **Accuracy** and **Forecast**
   sections and confirm they still work.
2. Open any assistant/LLM panel and confirm it still responds.
3. Confirm the sidebar groups all still expand.

---

## What would be a real failure

- A dropdown option that yields no series.
- A no-signal series presented with a champion recommendation.
- Any "4-year", "1,440-day" or mean-based figure.
- A median rendered as `0` instead of *"not computable"*.
- A legacy page or the assistant breaking.

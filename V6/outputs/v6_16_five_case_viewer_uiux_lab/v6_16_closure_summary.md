# V6.16 Five-Case Viewer UI/UX Lab Closure and Visual-Review Fix

## Final status

**COMPLETED, VISUALLY REVIEWED, CORRECTED, AND REVALIDATED**

Status token:
`V6_16_FIVE_CASE_VIEWER_UIUX_LAB_COMPLETED`

Corrected-lab status token:
`V6_16_FIVE_CASE_VIEWER_UIUX_LAB_FIX_COMPLETED`

V6.16 implemented the definitive unified Viewer experience against one
prepared five-case pilot artifact. Browser validation completed with HTTP 200,
five available pilot cases, one explicit unavailable combination, 15 verified
models, working Horizon selection, a rendered Actual-versus-model chart, and
complete data notes.

## Selected cases

| Case | Metric | Scenario | Granularity | Key |
|---|---|---|---|---|
| P01 | HDD - EDB | Enterprise | Region | APC-Dedicated |
| P02 | HDD - EDB | Enterprise | Forest | NAMPRD07 |
| P03 | HDD - EDB | Consumer | Region | APC-Dedicated |
| P04 | HDD - EDB | Consumer | Forest | NAMPRD07 |
| P05 | HDD - Basilisk | Basilisk | Forest | namprd07 |

All five cases have actuals. The pilot artifact has 6,750 rows: five cases,
three origins per case, 15 models, and 30 horizons.

## Artifacts created

1. `v6_16_selected_pilot_cases.csv`
2. `build_v6_16_pilot_backtest.py`
3. `forecast_viewer_model_outputs_v2_pilot.csv`
4. `v6_16_pilot_model_run_log.csv`
5. `v6_16_pilot_run_summary.json`
6. `v6_16_pilot_backtest_manifest.csv`
7. `v6_16_dashboard_feeding_contract.csv`
8. `v6_16_uiux_validation.csv`
9. `v6_16_pilot_limitations.md`
10. `v6_16_closure_summary.md`

## UI/UX behavior implemented

- One `Set up the backtest view` panel.
- Metric -> Scenario -> Granularity -> Key / Series cascade.
- Horizon and History Window controls.
- All 15 verified AEGIS models grouped into growth baseline, statistical,
  machine learning, and deep learning families.
- Analyze Backtest action that freezes the requested setup for rendering.
- Actual versus selected prepared model forecasts.
- Required data notes and a pilot-row download.
- Clear `Backtest not available for this pilot` handling.
- No Scenario Explorer, Multi-Metric tab, or Forecast Version control.

The Viewer reads only
`forecast_viewer_model_outputs_v2_pilot.csv`. Data preparation occurred outside
Shiny. The dashboard does not train, backtest, extract, or write source data.

## Validation results

All 27 checks in `v6_16_uiux_validation.csv` pass. The live application was
validated at `http://127.0.0.1:8081` from the primary worktree. P05 was analyzed
at horizon 10 with six selected models; the chart rendered Actual plus the six
model series, and notes reported all required dimensions and counts.

## Next-stage gates

- **V6.17:** technically eligible for planning, but must not start without
  explicit authorization.
- **Full backtest run:** blocked and not authorized.
- **R8-FIX-3:** blocked and not authorized.

## Recommended next step

Oscar should visually review the live Viewer on port 8081. If the definitive
UI/UX is accepted, explicitly authorize the next sequential stage and separately
decide whether any bounded or full backtest execution may proceed.

## Visual-review correction

Oscar accepted the general Viewer structure but identified that unavailable
Viewer status text appeared inside Key / Series and that Forecast still had the
incomplete legacy key-first setup. The corrected V6.16 lab now:

- leaves Viewer Key / Series empty for unavailable combinations;
- shows the pilot-limit message outside the dropdown;
- keeps SSD-Phoenix out of Viewer;
- replaces Forecast with the complete seven-step product cascade;
- includes prepared HDD Enterprise/Region with actual history;
- includes both required SSD-Phoenix scenarios as forecast-only;
- reads one prepared Forecast artifact assembled outside Shiny.

The Forecast artifact has 78,142 rows across 45 HDD keys and 300
SSD scenario/key combinations. Browser validation confirmed HDD actual plus
forecast rendering, SSD forecast-only rendering, 148/152 SSD keys by scenario,
required data notes, and HTTP 200. The full run and V6.17 remain blocked.

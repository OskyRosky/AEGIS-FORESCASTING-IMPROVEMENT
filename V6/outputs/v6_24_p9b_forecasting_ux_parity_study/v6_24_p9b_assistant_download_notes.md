# V6.24-P9B — Assistant and Download Notes

Both features already exist in the app. Neither needs to be built from scratch,
and one of them carries a design decision that must be made before P9G starts.

---

# Part 1 — LLM Assistant

## What exists

```r
llm_explain_ui(id, page_title, button_label, panel_title, panel_sub, quick_prompts)
llm_explain_server(id, page_id, quick_prompts)
```

Mounted once per section at the **end** of the page. The source comment states the
intent: *"It closes the section, it does not introduce it."* The user reads the
section, then asks about it.

`.LLM_DEFAULT_QUICK_PROMPTS` already matches the owner's screenshot exactly:

- Summarize the key takeaway
- Explain what changed
- Explain the main risk
- What should I pay attention to?

Plus a free-text box, a **Generate explanation** button, a four-step timed
"thinking" animation, a rendered answer panel, and an explanation download modal
(MD/TXT/HTML always; PDF/DOCX when pandoc is present).

Every answer carries the disclosure *"Local mock · governed evidence only · no
model or champion changes."* That line is an honesty statement, not decoration —
it should be reused verbatim.

## The blocking design point

```r
rv$resp <- llm_explain_get(page_id)     # llm_explain.R line 754
llm_explain_get <- function(page_id) {
  llm_explain_load()
  .llm_explain_env$responses[[page_id]]   # keyed by PAGE
}
```

**The evidence pack is static per page, not per selection.**

Mount it naively on the V6.24 Viewer and the panel will answer about *the section*
while sitting directly beneath a specific selected series. A user reading
"Summarize the key takeaway" underneath `HDD__Basilisk__NA__Forest__apcp150` will
reasonably assume the answer describes that series.

**An assistant that confidently describes the wrong series is worse than no
assistant.** Three honest options:

| Option | Effort | Honesty |
|---|---|---|
| A — build a selection-aware evidence pack from the governed artifacts | Medium | Full |
| B — mount as-is and label it clearly *"about this section, not this series"* | Low | Acceptable if the label is prominent |
| C — defer the assistant past P9G | None | Fine, but the owner asked for it |

**Recommendation: A.** The evidence is a straightforward read of fields that
already exist, and it is the only option that delivers what the owner actually
described.

## What a V6.24 evidence pack should contain

All of it **read**, none computed:

| Field | Source |
|---|---|
| series_id, route display label | `navigation_contract` |
| metric, db_type, scenario, segment, granularity, key | `navigation_contract` |
| key role | `navigation_contract.key_axis_status` |
| champion model and validity — **only when `champion_visible`** | `navigation_contract` |
| primary rank metric and value | `model_rankings` |
| median WAPE / MAE plus computability status | `navigation_contract` |
| signal quality | `series_signal_quality` |
| caveat badges and messages | `navigation_contract` |
| forecast type, 30 steps, window dates | `forecast_outputs`, `navigation_contract` |
| negative and extreme counts | `navigation_contract` |
| latest actual date and value | `actuals_normalized`, `forecast_outputs` |

Two rules the pack must respect:

1. **Never present a suppressed champion as a recommendation.** If
   `champion_visible` is FALSE the pack should say the champion is not meaningful
   and explain why, exactly as the UI does.
2. **Never fill a non-computable median with zero.** Sixteen series have a
   non-computable median WAPE; the pack must carry the status, not a number.

## Wiring cost

Two lines in `server/server.R`:

```r
llm_explain_server("llm_v24_viewer",   "v24_viewer")
llm_explain_server("llm_v24_forecast", "v24_forecast")
```

Two lines in the UI sections. The engine, prompts, animation and download modal
are reused unchanged.

---

# Part 2 — Downloads

## Two existing patterns

**`artifact_export.R`** — `register_artifact_downloads()` registers six formats
per governed artifact (`dl_<key>_{csv,md,txt,html,pdf,docx}`), served through
`.artifact_download_modal(spec, caps)` with a button per available format.
Capability detection is honest: MD/HTML/TXT always work, PDF/DOCX are enabled only
when pandoc and a LaTeX engine are present and are otherwise **clearly disabled**.
Nothing is installed at runtime.

Its limitation: it is built for *whole small artifacts* (≤ 15 rows, with a preview
cap), and CSV is a verbatim `file.copy` of the canonical file.

**`fvp_pilot_download_rows()`** in `viewer_pilot.R`, surfaced through
`uiOutput("fvp_download_ui")` under the chart — **rows for the current selection**.
This is the closer match for what the owner called *"download analysis"*.

## The right combination for V6.24

Take the **modal and format handling** from `artifact_export.R` and the
**filtered-rows** approach from `viewer_pilot.R`.

Note that read-only means *rows are never altered*, not *the file is copied*.
Writing a filtered subset of an artifact is fully compatible with the read-only
contract, provided no value is recomputed or reformatted on the way out.

## Download targets

| Target | Source | Filter |
|---|---|---|
| Observed actuals | `actuals_normalized` | selected `series_id` |
| Backtests | `model_backtests_15_models` | series + selected models + horizon |
| Forecast | `forecast_outputs` | series + selected model, all 30 steps |
| Ranking | `model_rankings` joined to `accuracy_metrics` | series, all 15 models |
| Contract row | `navigation_contract` | the single selected row |

CSV first. Other formats only if they come free from the existing modal.

## Filename convention

The owner asked for metric, route, model and date:

```
v6_24_backtest_HDD_apcp150_ETS-Explicit_20260823.csv
v6_24_forecast_SSD_GBRP267_FixedGrowth_1_5_20260823.csv
```

## Validation for P9G

- The downloaded rows match the visible selection exactly — same series, same
  models, same horizon.
- No value differs from the artifact.
- Row counts reconcile: forecast download is exactly 30 rows; ranking download is
  exactly 15.
- No governed artifact is modified.

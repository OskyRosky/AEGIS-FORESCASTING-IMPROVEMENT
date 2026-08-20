# V6.0F — Shiny Multi-Metric Integration Report

**Stage:** V6.0F — Shiny Multi-Metric Integration
**Date:** 2026-08-11
**Runtime used for validation:** R 4.6.0 at `C:\Program Files\R\R-4.6.0\bin\Rscript.exe`
**Live URL:** `http://127.0.0.1:8081`

---

## 1. What the app looked like before

Inspection of the existing app found a 14-section dashboard driven by
`app_sections()` in `ui/tabs.R`, a grouped sidebar in `ui/sidebar.R`, a single
`app_server()` in `server/server.R`, a governed read-only loader in
`R/data_loader.R` with a 40-entry artifact registry, and an assistant layer of
`llm_explain.R` (860 lines), `llm_compose.R` (282 lines), `llm_client.R` and the
`llm_summary` module, grounded in a frozen 74 KB evidence pack.

Nothing in that structure read `outputs/metrics_multi`.

## 2. What was added

Three new files, all additive:

| File | Role |
| --- | --- |
| `shiny_app/R/multi_metric_loader.R` | Loads the 10 governed artifacts, exposes dependent-filter helpers, and registers the new assistant pages |
| `shiny_app/ui/tabs_multi_metric.R` | The Multi-Metric Accuracy section |
| `shiny_app/server/multi_metric_server.R` | Read-only server logic, gating and downloads |

Five existing files received a hook each, 14 lines in total:

| File | Change |
| --- | --- |
| `global.R` | source the loader and the module server, then `mm_init()` |
| `ui/body.R` | source the new section file |
| `ui/tabs.R` | add `section_multi_metric()` to `app_sections()` |
| `ui/sidebar.R` | add the Multi-Metric item under Forecasting |
| `server/server.R` | call `multi_metric_server()` and register the assistant page |

No existing behaviour was removed or rewritten.

## 3. How the assistant was extended without touching it

`llm_explain_get(page_id)` resolves from an index built by `llm_explain_load()`.
The loader calls that function and then **adds** the 11 multi-metric entries to the
index for page ids that do not already exist. The frozen pack file is never
opened for writing and its hash is unchanged. If the new pack is missing, the
assistant behaves exactly as before.

The new entries reuse the legacy field shape, so the existing renderer, the
confidence badge, the limitations block, the traceability panel and all five
export formats work unchanged.

## 4. Read-only discipline

The section subsets governed data frames and formats them. It performs no join
beyond row filtering, no aggregation, and no metric computation. Numeric coercion
is presentation-only and never writes back.

One correction was required during this stage: `readr` was type-guessing
`forecast_version`, turning `2026-03-12` into a Date, which broke exact identity
matching. The loader now reads every artifact as character, and numeric columns
are coerced only for display. This preserves the identity tuple exactly as the
contract requires.

## 5. Live evidence

| Evidence | Result |
| --- | --- |
| App start | Listening on 127.0.0.1:8081 |
| Home page | HTTP 200, 316,354 bytes |
| Section renders | `content-section is-active`, heading Multi-Metric Accuracy |
| Filters | Six dependent selects rendered from the artifact |
| Scenario | Static "Not applicable" with the reason, no value sent |
| Rankings table | 134 groups for HDD region, 137 for SSD LVWE |
| Detail table | 9 windows for the HDD selection, 57 for NAMPRD07 LVWE |
| Coverage table | 16 rows including every unavailable source with its reason |
| Assistant | Explanation generated live with summary, evidence, limitations, confidence high and traceability |
| Downloads | Three links bound to real session download endpoints |
| Exports | MD, TXT, HTML, DOCX and PDF all produced |

Live values observed for the validation case:

| Series | Windows | Avg MAPE | Avg accuracy | Sources merged |
| --- | --- | --- | --- | --- |
| SSD-Phoenix LVWE, NAMPRD07 | 57 | 4.513 | 95.487 | 1 |
| SSD-Phoenix LVNE, NAMPRD07 | 58 | 4.498 | 95.502 | 1 |

Gating text captured live for SSD-Phoenix:

> Cross-version trend: not available · SINGLE_VERSION_ONLY
> Plan-to-plan comparison: not available · SINGLE_VERSION_ONLY
> Forecast curve: not available · NO_TARGET_DATE_GRAIN
> **Not drift** This selection reports observed accuracy for the retained cycle only.

## 6. Test status

T34 assistant exports was executed in this stage and passed for all five formats.
T35 container parity remains deferred to V6.0H by design.

## 7. What to look at during your own live review

Open `http://127.0.0.1:8081`, go to **Forecasting → Multi-Metric**, then:

1. Switch Metric between HDD-EDB and SSD-Phoenix.
2. Switch DB Type between the two SSD Low-Vol variants and confirm the numbers differ.
3. Confirm Scenario reads "Not applicable" and never "Enterprise".
4. Switch Granularity between region and forest and confirm the key list changes.
5. Select NAMPRD07 and confirm it is only offered under forest.
6. Confirm the single-version badge and the "Not drift" notice appear for SSD.
7. Scroll to the coverage table and confirm CPU, MCDB and IOPS appear with reasons rather than zeros.
8. Click **Generate explanation** and confirm the assistant answers with limitations and traceability.
9. Use the three CSV download buttons.
10. Visit the other pages and confirm nothing regressed.

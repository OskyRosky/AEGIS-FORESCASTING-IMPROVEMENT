# V4.6 — Shiny Local On-Demand · Integration Report

**Phase:** V4.6 (Shiny Local On-Demand explanation panel)
**Status:** `V4_6_SHINY_LOCAL_ON_DEMAND_COMPLETED`
**Provider:** mock · `mock_no_llm` · **no real LLM, no Azure connected**
**Dashboard:** http://127.0.0.1:3839 (PID 17868) — HTTP 200

---

## 1. What was built

A new **on-demand explanation panel** was integrated into the 4 MVP sections of the
**active section-based** V4 dashboard. When the user clicks the panel button, the app
loads the **precomputed V4.4 mock response** for that view and renders it according to
the V4.5 rendering contract. **Nothing is computed at click time** — the narrative is
read from a governed, read-only JSON artifact.

### Integration targets (active UI = `ui/body.R` → `ui/tabs.R`)

| MVP view | `data-section` | `ui/tabs.R` function | Module id | Button |
|---|---|---|---|---|
| Champion Overview | `champion` | `section_champion()` | `llm_champion_overview` | **Explain champion** |
| Tournament | `tournament` | `section_tournament()` | `llm_tournament` | **Explain tournament** |
| Forecast Viewer | `forecast` | `section_forecast()` | `llm_forecast_viewer` | **Explain forecast view** |
| Governance & Risks | `risks` | `section_risks()` | `llm_governance_risks` | **Explain governance & risks** |

The panel UI is inserted **immediately after each `section_head(...)`**, so it appears at
the top of each section without disturbing existing content.

---

## 2. Architecture

```
global.R
  └─ source("R/llm_explain.R")          # new (read-only)

R/llm_explain.R
  ├─ llm_explain_load()                 # reads outputs/v4_4_mock_provider/v4_4_mock_responses.json once
  ├─ llm_explain_get(page_id)           # returns precomputed response for a page
  ├─ llm_explain_ui(id, title, label)   # actionButton + status + panel container (Shiny module UI)
  └─ llm_explain_server(id, page_id)    # on click: load precomputed -> render (Shiny moduleServer)

ui/tabs.R   → llm_explain_ui(...) inserted in the 4 MVP sections
server/server.R → llm_explain_server(...) called 4x inside app_server
www/custom.css → .llm-explain* styles appended (light + dark)
```

The module is a clean Shiny module (`NS` + `moduleServer`), so it lives inside the
section `tags$div` and is wired once per section from the single `app_server` function.

---

## 3. Rendered panel (per V4.5 rendering contract)

Top-to-bottom, on click:

1. Header: kicker **"AEGIS Explanation (local)"** + view title + badge **`mock · local · no real LLM`** + button.
2. Status line: **Ready → Composing explanation (local mock — no real LLM)… → Ready**.
3. Banner: *"Provider: mock · Stage: mock_no_llm · This is a deterministic local mock, not a real LLM. No Azure OpenAI is connected."*
4. **Executive summary**
5. **What the evidence says** (bullets)
6. **Why it matters**
7. **Sources used** (collapsible `<details>`, always shown)
8. **Limitations** (collapsible `<details>`, always shown)
9. **Confidence** badge (high / medium / low / insufficient evidence)
10. **Show traceability** (collapsible: claim → source artifacts / evidence fields / evidence pack)
11. **Download (available in V4.7)** — disabled placeholder
12. Governance footer: *"Explanation only · no model changes · no champion changes · Data: read-only evidence pack"*

UI states implemented: **Ready**, **Building**, **Insufficient evidence**, **Invalid / unavailable**.

---

## 4. Data path verification

The precomputed loader returns full content for all 4 MVP pages:

| page_id | confidence | evidence bullets | sources | limitations | claims |
|---|---|---|---|---|---|
| champion_overview | high | 4 | 6 | 2 | 8 |
| tournament | high | 3 | 6 | 4 | 7 |
| forecast_viewer | high | 4 | 5 | 3 | 8 |
| governance_risks | high | 3 | 8 | 2 | 7 |

Source artifact: `outputs/v4_4_mock_provider/v4_4_mock_responses.json` (read-only).

---

## 5. Governance & safety

- **No LLM / no Azure / no external API.** The module reads a local JSON only
  (`is_real_llm=false`, `uses_azure=false`).
- **No compute at click time.** No model fit, no forecast recompute, no metric recompute.
- **Champion unchanged:** `APP_CHAMPION = "ETS Explicit"` (constants.R untouched).
- **No data mutation:** `data/processed` and `data/raw` are not touched; no SQL.
- **Explanation only:** governance footer + banner make the read-only, explain-only stance explicit on every panel.
- **Download disabled** until V4.7.
- **V1 / V2 / V3 untouched:** only `V4/shiny_app/*` files were modified.

---

## 6. Restart discipline

- Old V4 Shiny instance (PID 12708) stopped.
- Single restart on :3839 → PID 17868.
- Parse-checked all modified R files **before** restart (all OK).
- HTTP 200 confirmed; stderr log shows clean startup (only a pre-existing readr/vroom warning).

---

## 7. Out of scope (deferred)

- Real download of the explanation payload → **V4.7**.
- Final local validation / V4 closure → **V4.8**.
- Azure OpenAI readiness → **V4.9 (gated, optional)**.
- Executive-tone polish (V4.4 backlog) → still deferred.

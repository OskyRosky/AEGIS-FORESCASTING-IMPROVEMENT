# V4.1 — Panel Mockup (textual)

This is the **visible** experience the user sees on each page. Local-first, executive,
read-only. No real code in V4.1 — this defines the layout to build in V4.6/V4.7.

---

## A. Generic panel (Champion / Tournament / Governance & Risks)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🤖  LLM Explanation                                    [ ▾ collapse ]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   [ Summarize this view ]                                             │
│                                                                       │
│   Progress: ▓▓▓▓▓▓░░░░  Generating explanation…  (reading evidence)   │
│                                                                       │
│   ── LLM Explanation ───────────────────────────────────────────────  │
│                                                                       │
│   Executive summary                                                   │
│     <2–4 sentence executive narrative>                                │
│                                                                       │
│   What the evidence says                                              │
│     • <fact 1 traced to artifact>                                     │
│     • <fact 2 traced to artifact>                                     │
│                                                                       │
│   Why it matters                                                      │
│     <business interpretation, no causality beyond evidence>           │
│                                                                       │
│   Sources used                                                        │
│     • model_champion_comparison.csv                                   │
│     • model_dashboard_summary.csv                                     │
│                                                                       │
│   Limitations                                                         │
│     • Snapshot date 2026-06-28 (not resynced)                         │
│     • LLM explains, does not decide champion or governance            │
│                                                                       │
│   [ ⬇ Download summary ]   (enabled in V4.7)                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

**States:**
- **Idle:** only the `Summarize this view` button is shown.
- **Running:** progress bar/message visible; button disabled.
- **Done:** explanation sections rendered; Download enabled (V4.7).
- **Insufficient evidence:** Executive summary shows `insufficient evidence`, Limitations
  lists which artifacts/fields were missing, Download disabled.

---

## B. Forecast Viewer panel (filter-aware)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🤖  LLM Explanation — Forecast Viewer                  [ ▾ collapse ]│
├─────────────────────────────────────────────────────────────────────┤
│  Current selection (read-only echo):                                  │
│   entity = <…>   model(s) = <…>   horizon = <…>   window = <…>         │
│                                                                       │
│  Guided questions:                                                    │
│   [ Explain selected model ]  [ Compare selected models ]             │
│   [ Summarize forecast risk ] [ Explain selected forecast movement ]  │
│                                                                       │
│  Ask about this view (limited to selection):                          │
│   ┌───────────────────────────────────────────────────────────────┐  │
│   │ e.g. "What does the interval widening mean here?"             │  │
│   └───────────────────────────────────────────────────────────────┘  │
│   [ Summarize this view ]                                             │
│                                                                       │
│   Progress: ▓▓▓▓▓▓▓▓░░  Generating explanation…                       │
│                                                                       │
│   ── LLM Explanation ───────────────────────────────────────────────  │
│   Executive summary       <…>                                         │
│   What the evidence says  • <…>                                       │
│   Why it matters          <…>                                         │
│   Sources used            • forecasts_with_intervals.csv • actuals.csv│
│   Limitations             • Scoped to current selection only          │
│   [ ⬇ Download summary ]   (V4.7)                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Rule:** the free-text box is **limited to the selected evidence pack**. Any question
outside the pack returns `insufficient evidence` with guidance to adjust filters. The LLM
never uses outside knowledge.

---

## C. Placement notes

- The panel reuses the existing seam `shiny_app/modules/llm_summary/` (not modified in V4.1).
- One panel per page, placed **below** the page's main content (card/table/chart).
- The header "Project / Insights" grouping is optional; per-page inline panel is preferred so
  the explanation sits next to the evidence it describes.

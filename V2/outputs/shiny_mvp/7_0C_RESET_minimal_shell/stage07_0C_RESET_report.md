# Stage 07 — Block 7.0C-RESET — Minimal Clean Dashboard Shell

**Active project root:** `V1`
**Target app:** `V1/shiny_app`
**Date:** 2026-06-15
**Recommendation:** `READY_FOR_OSCAR_VISUAL_REVIEW_7_0C_RESET`

---

## 1. Objective

Reset the TESSERACT v2 dashboard to a simple, clean shell:

- Compact top header (navy).
- Persistent dark left sidebar with vertical menu only.
- Light body/content area with minimal placeholder content.
- No horizontal navigation links.
- No crowded governance / champion cards.

Layout-only block. No models, forecasts, metrics, or tournament were run.
`shinydashboard` was **not** used and **no packages were installed**.

---

## 2. What changed

The previous body rendered a hidden `tabsetPanel` (which surfaced as horizontal
tab links) and a crowded landing page (Stage 05 Closed, Stage 06 Approved,
Audit #6, Active Version, Champion summary, Governance note). These were removed.

The new shell uses plain Shiny + `bslib::page_fillable` with a CSS grid:

```
+----------------------------------------------------+
|  HEADER  TESSERACT v2 · Forecast Improvement  [V1][Stage 07][Read-only] |
+----------------+-----------------------------------+
|  SIDEBAR       |  BODY (light gray)                |
|  (dark navy)   |  TESSERACT v2 Dashboard           |
|  Dashboard     |  Forecast Improvement Platform    |
|  Executive...  |  [Layout ready][Read-only][Next]  |
|  Champion      |                                   |
|  ...           |                                   |
+----------------+-----------------------------------+
|  V1 · Stage 07 · Read-only dashboard               |
+----------------------------------------------------+
```

### Header
- Height 56px, navy background (`#102a43`).
- Left: **TESSERACT v2** + subtitle *Forecast Improvement Platform*.
- Right badges: **V1**, **Stage 07**, **Read-only**.

### Sidebar
- Fixed left column, width 260px, dark navy gradient, light text.
- Vertical menu only (CSS `flex-direction: column`). No horizontal links.
- 11 items: Dashboard, Executive Overview, Champion, Models, Evidence,
  Risk Register, Governance, Audit Trail, Source Artifacts, Methodology,
  Version Info.
- Icons via `shiny::icon` with a safe bullet fallback if fontawesome is absent.

### Body
- Light gray background, content to the right of the sidebar.
- Title **TESSERACT v2 Dashboard**, subtitle *Forecast Improvement Platform — Stage 07 Shiny MVP*.
- Exactly three placeholder cards: *Layout ready*, *Read-only mode*, *Next step*.

### Footer
- Minimal: `V1 · Stage 07 · Read-only dashboard`.

---

## 3. Removed / hidden old content

- Hidden `tabsetPanel` horizontal navigation — removed.
- Stage 05 Closed card — removed from landing.
- Stage 06 Approved card — removed from landing.
- Audit #6 card — removed from landing.
- Active Version card — removed from landing.
- Champion summary card — removed from landing.
- Governance note card — removed from landing.

`ui/tabs.R` was retired to a stub; its prior content is preserved in backups.

---

## 4. Launch result

| Item | Value |
|------|-------|
| URL | http://127.0.0.1:3838 |
| Host | 127.0.0.1 |
| Port | 3838 |
| HTTP status | 200 |
| Process ID | 35460 |
| Stop command | `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny_v1.ps1 -PidToStop 35460` |
| stdout log | outputs/shiny_mvp/7_0C_RESET_minimal_shell/reset_shell_stdout.log |
| stderr log | outputs/shiny_mvp/7_0C_RESET_minimal_shell/reset_shell_stderr.log |

The app is left running (HTTP 200).

---

## 5. Validation summary

All 16 layout checks PASS (see `stage07_0C_RESET_layout_validation.csv`):
header exists, header badges, left sidebar exists, sidebar vertical, sidebar
menu items, body right of sidebar, no horizontal nav links, old governance
cards hidden, old champion summary hidden, no winner/sample language, minimal
placeholder cards, body title/subtitle, minimal footer, server no-recompute,
HTTP 200.

Visual launch checks: `stage07_0C_RESET_visual_launch_validation.csv`.
Safety checks: `stage07_0C_RESET_safety_validation.csv`.

---

## 6. Safety

- Stage 05 / Stage 06 / Audit #6 artifacts: not modified.
- MassiveForecasting-V3: not modified.
- No models / forecasts / metrics / tournament recomputed.
- No champion decision changed.
- No charts, highcharter, reactable, or governed data bindings added.
- No packages installed; `shinydashboard` not used.
- All edits confined to `V1/shiny_app`. Backups under
  `outputs/shiny_mvp/7_0C_RESET_minimal_shell/backups/`.

---

## 7. Next recommended step

Block 7.0D — begin populating the **Dashboard** section content (still
read-only), wiring the first governed artifact summary into the body once the
shell is approved.

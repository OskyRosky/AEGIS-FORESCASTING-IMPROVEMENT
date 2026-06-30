# Stage 07 — V2 Governance Risk Register Layout Cleanup

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_GOVERNANCE_RISK_REGISTER_LAYOUT
**Scope:** V2 only. Layout / UX only. Read-only governed register preserved.

## 1. General Summary
Refactored **Governance → Risks / Risk Register** to follow the approved dashboard
layout pattern already used in Viewer, Accuracy, Forecast, TTL, and Models. The page
is now organized into five collapsible boxes built with `home_collapse(...)`:
an **About** intro (collapsed), a single **Risk Register Overview** box that groups all
summary cards, a dedicated **Governed Risk Register** table box, a dedicated
**Deferred Models** table box, and a collapsed **Conditional Decision Context** box.
No risk values, counts, severities, or governance decisions were changed — this is a
presentation-only reorganization.

## 2. Files Created
- `outputs/shiny_mvp/7_V2_GOVERNANCE_RISK_REGISTER_LAYOUT_CLEANUP/stage07_v2_governance_risk_register_layout_cleanup_report.md`
- `outputs/shiny_mvp/7_V2_GOVERNANCE_RISK_REGISTER_LAYOUT_CLEANUP/stage07_v2_governance_risk_register_layout_cleanup_validation.csv`
- `outputs/shiny_mvp/7_V2_GOVERNANCE_RISK_REGISTER_LAYOUT_CLEANUP/stage07_v2_governance_risk_register_layout_cleanup_launch.csv`
- `outputs/shiny_mvp/7_V2_GOVERNANCE_RISK_REGISTER_LAYOUT_CLEANUP/stage07_v2_governance_risk_register_layout_cleanup_visual_checks.csv`

## 3. Files Modified
- `V2/shiny_app/ui/tabs.R` — `section_risks()` rewritten into five `home_collapse` boxes.
- `V2/shiny_app/server/server.R` — added `outputOptions(..., suspendWhenHidden = FALSE)`
  for `risk_register_table` and `risk_deferred_models_table` so the DT tables render
  reliably inside collapsible boxes (same precedent as the champion page).

## 4. Risk Register Layout Changes
Before: a flat stack — two card grids, an inline "Risk register" heading + table, an
inline "Deferred models" heading + table, and a trailing governance note card.
After: five independently collapsible boxes:
1. **About the Risk Register** (collapsed)
2. **Risk Register Overview** (open) — all summary cards in one box
3. **Governed Risk Register** (open) — risk register table
4. **Deferred Models** (open) — deferred models table
5. **Conditional Decision Context** (collapsed) — carry-forward governance note

## 5. About Section Status
New collapsed `home_collapse` box "About the Risk Register" using `home-prose`. Text:
"This page summarizes governed risks carried forward from the Model Lab closure pack.
It is a read-only register: risks are displayed for transparency, auditability, and
future follow-up. This page does not add, remove, downgrade, recompute, or resolve any
risk." Collapsed by default to keep the page clean.

## 6. Risk Register Overview Status
Single open box grouping both `card_grid()` rows — all eight cards preserved with the
same `risk_register_values()` bindings: Registered risks (Governed register), High
(Highest severity), Medium (Carry-forward), Advisory / Minor (Non-blocking), Carried
forward to dashboard (Must stay visible), Carried forward to future work (Future
investigation), Deferred models (Not in final tournament), and the Governance /
Read-only register shell card. No numbers changed.

## 7. Governed Risk Register Table Status
Dedicated open box "Governed Risk Register" containing the descriptive note and
`DT::dataTableOutput("risk_register_table")` inside `tess-table-wrap`. The render
function is unchanged; `suspendWhenHidden = FALSE` ensures it renders inside the
collapsible. Ordering, columns, search, and sort behavior are unchanged.

## 8. Deferred Models Table Status
Dedicated open box "Deferred Models" containing the descriptive note and
`DT::dataTableOutput("risk_deferred_models_table")` inside `tess-table-wrap`. Render
function unchanged; `suspendWhenHidden = FALSE` added. Deferred rows are unchanged.

## 9. Conditional Decision Context Status
Moved into its own collapsed box "Conditional Decision Context". The original
`shell-card` with the `pill-amber` "Carry-forward" pill, the "Conditional decision
context" title, and the full conditional-decision paragraph are preserved verbatim.

## 10. Collapsible Sections Status
Five `home_collapse` boxes confirmed by smoke test. Default state: **3 open**
(Overview, Governed Risk Register, Deferred Models) and **2 collapsed** (About,
Conditional Decision Context). Each toggles independently.

## 11. Text Cleanup Status
Removed inline `section-block-title` headings ("Risk register", "Deferred models") in
favor of box titles/summaries. Added concise box summaries and a short About intro.
The conditional-decision paragraph and all card labels/pills are unchanged.

## 12. Data / Governance Preservation Status
All content is read from the existing `risk_register_values()`, `risk_register_table()`,
and `risk_deferred_models_table()` sources. No risk IDs, subjects, descriptions,
impacts, treatments, severities, carry-forward flags, or deferred rows were edited.

## 13. Confirmation No Data Artifacts Were Modified
Confirmed. No writes to any data artifact. Only `ui/tabs.R` and `server/server.R` were
edited; the remaining new files are report/CSV deliverables under `outputs/shiny_mvp/`.

## 14. Confirmation No Models / Forecasts Were Run
Confirmed. No engine, tournament, backtest, or model code was invoked. Only R parse
checks, an isolated UI smoke test, and the Shiny launch were executed.

## 15. Confirmation Champion Decision Was Not Changed
Confirmed. No champion/governance decision logic or artifact was touched. The
conditional decision context text remains exactly as before.

## 16. Validation Summary
21 / 21 requirements PASS — see
`stage07_v2_governance_risk_register_layout_cleanup_validation.csv`. Both modified R
files parse cleanly; smoke test confirms five boxes with the expected open/collapsed
defaults and both table outputs present.

## 17. App Launch Details
- Script: `scripts\start_shiny.ps1`
- Port: 3838 (single listener confirmed)
- Process ID: 13432
- URL: http://127.0.0.1:3838 — **HTTP 200**
- Previous instance (PID 14564) stopped before relaunch.
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 13432`

## 18. What Oscar Should Review
Open Governance → Risks and verify the About box (collapsed), the Risk Register
Overview cards, the Governed Risk Register table, the Deferred Models table, and the
Conditional Decision Context box all match the approved dashboard layout pattern, and
that all counts/rows are unchanged. See `..._visual_checks.csv`.

## 19. Total Execution Time
Approximately 4 minutes (edits, parse + smoke validation, single clean relaunch, and
deliverables).

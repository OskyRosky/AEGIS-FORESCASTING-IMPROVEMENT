# Stage 07 — V2 Reference Pages Layout Cleanup

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_REFERENCE_PAGES_LAYOUT
**Scope:** V2 only. Layout / UX only. All Reference pages remain read-only.

## 1. General Summary
Refactored the three **Reference** pages — **Artifacts**, **Methodology**, and
**Version** — to follow the approved dashboard layout pattern already used in Viewer,
Accuracy, Forecast, TTL, Governance Risks, and Governance Audit. Each page now opens
with a collapsed **About** intro and groups its content into clear collapsible
`home_collapse(...)` boxes. Architecture Diagram and Project Documentation are clean
placeholders only — no image or document is loaded. No data, artifact freshness, or
version values were changed.

## 2. Files Created
- `outputs/shiny_mvp/7_V2_REFERENCE_PAGES_LAYOUT_CLEANUP/stage07_v2_reference_pages_layout_cleanup_report.md`
- `outputs/shiny_mvp/7_V2_REFERENCE_PAGES_LAYOUT_CLEANUP/stage07_v2_reference_pages_layout_cleanup_validation.csv`
- `outputs/shiny_mvp/7_V2_REFERENCE_PAGES_LAYOUT_CLEANUP/stage07_v2_reference_pages_layout_cleanup_launch.csv`
- `outputs/shiny_mvp/7_V2_REFERENCE_PAGES_LAYOUT_CLEANUP/stage07_v2_reference_pages_layout_cleanup_visual_checks.csv`

## 3. Files Modified
- `V2/shiny_app/ui/tabs.R` — `section_artifacts()`, `section_methodology()`, and
  `section_version()` rewritten into `home_collapse` boxes. No other files changed:
  the artifact DT outputs (`artifact_catalog_table`, `artifact_lineage_table`) already
  carried `outputOptions(..., suspendWhenHidden = FALSE)` in `server/server.R`, and the
  download handlers (`dl_*`) work unchanged inside collapsibles, so no server change
  was required.

## 4. Reference Layout Changes
Every Reference page now follows the same structure: page title/subtitle → collapsed
**About** box → an open main **Overview** box → content grouped into dedicated
collapsible boxes (tables, metadata, placeholders, notes). Loose unboxed headings and
content were moved inside boxes.

## 5. Artifacts Page Status
Four collapsible boxes:
1. **About the Artifacts Reference** (collapsed) — read-only artifacts explanation.
2. **Artifact Overview** (open) — the 4 registry/availability KPI cards, values unchanged.
3. **Governed Artifact Inventory** (open) — description + governed downloads grid
   (`artifact-dl-grid`) + full artifact catalog table (`artifact_catalog_table`).
4. **Artifact Notes / Lineage / Evidence** (collapsed) — dashboard data lineage table
   (`artifact_lineage_table`) + the read-only "Single source of truth" governance note.

## 6. Methodology Page Status
Five collapsible boxes:
1. **About the Methodology Reference** (collapsed) — read-only methodology explanation.
2. **Methodology Overview** (open) — Data pipeline cards, Current dataset cards + info
   list, What the dashboard consumes, and Dashboard structure, all preserved.
3. **Architecture Diagram** (open) — placeholder only.
4. **Project Documentation** (collapsed) — placeholder only.
5. **Methodology Notes** (collapsed) — the artifacts-page pointer note + read-only tag.

## 7. Architecture Diagram Placeholder Status
Placeholder box present using the existing `method-figure` styling. Text reads
"Architecture diagram will be added here once the approved image is available." No
image is loaded; the smoke test confirms there is no `<img>` in the section. Will be
populated in a later step once Oscar provides the approved image.

## 8. Project Documentation Placeholder Status
Placeholder box present using the existing `method-figure method-figure-doc` styling.
Text reads "Project documentation will be linked or embedded here once the approved
document is available." No document, link, or filename was invented. Will be populated
in a later step once Oscar provides the approved document.

## 9. Version Page Status
Five collapsible boxes:
1. **About the Version Reference** (collapsed) — version-metadata explanation.
2. **Version Overview** (open) — App version / Forecast version / Artifacts available
   cards, values unchanged.
3. **Build / Runtime Metadata** (open) — Build & governance info list + Runtime info
   list, all values preserved (audit state, policy, champion, packages, project root).
4. **Artifact Freshness / Last Update** (open) — the data snapshot (forecast version,
   series × models, data contract build date, coverage), displayed values unchanged.
5. **Version Notes** (collapsed) — the read-only governed-build tag.

## 10. Collapsible Sections Status
All major sections are `home_collapse` boxes. Defaults: Artifacts = 2 open
(Overview, Inventory) / 2 collapsed (About, Notes); Methodology = 2 open (Overview,
Architecture Diagram) / 3 collapsed (About, Project Documentation, Methodology Notes);
Version = 3 open (Overview, Build/Runtime, Freshness) / 2 collapsed (About, Version
Notes). Each box toggles independently.

## 11. Text Cleanup Status
Loose `section-block-title` headings were moved inside boxes as sub-headings; box
titles/summaries use clean reference wording (Reference artifacts, Governed artifacts,
Methodology, Architecture diagram, Project documentation, Version metadata, Build
information, Read-only reference page). No user-visible internal labels (stage07, blog,
Shiny MVP status, scratchpad/temporary wording) are present.

## 12. Data / Artifact Preservation Status
All content is read from the existing `artifact_catalog_values()`,
`methodology_dataset_values()`, `artifact_registry_view()`, `version_runtime_values()`,
and the existing table outputs. No KPI values, info-row values, version metadata,
artifact freshness dates, or champion text were edited.

## 13. Confirmation No Data Artifacts Were Modified
Confirmed. No writes to any data artifact. Only `ui/tabs.R` was edited; the remaining
new files are report/CSV deliverables under `outputs/shiny_mvp/`.

## 14. Confirmation No Models / Forecasts Were Run
Confirmed. No engine, tournament, backtest, recalibration, or model code was invoked.
Only R parse checks, an isolated UI smoke test, and the Shiny launch were executed.

## 15. Confirmation Champion Decision Was Not Changed
Confirmed. No champion/governance decision logic or artifact was touched. The Version
page champion line and confidence text remain exactly as before.

## 16. Validation Summary
20 / 20 requirements PASS — see
`stage07_v2_reference_pages_layout_cleanup_validation.csv`. tabs.R parses cleanly;
smoke test confirms all three pages with the expected boxes, open/collapsed defaults,
preserved table/output IDs, placeholder text, no fake image/document, and no literal
escape artifacts.

## 17. App Launch Details
- Script: `scripts\start_shiny.ps1`
- Port: 3838 (single listener confirmed)
- Process ID: 17304
- URL: http://127.0.0.1:3838 — **HTTP 200**
- Previous instance (PID 5268) stopped before relaunch.
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 17304`

## 18. What Oscar Should Review
Open Reference → Artifacts, Reference → Methodology, and Reference → Version and verify
the About boxes (collapsed), the Overview boxes, the artifact tables/downloads, the
methodology content, the Architecture Diagram and Project Documentation placeholders
(no image/document yet), and the version/freshness values all match the approved
dashboard layout pattern with unchanged values. See `..._visual_checks.csv`.

## 19. Total Execution Time
Approximately 7 minutes (three function refactors, parse + smoke validation, single
clean relaunch, and deliverables).

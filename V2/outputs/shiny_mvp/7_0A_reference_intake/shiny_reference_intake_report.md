# Shiny Reference Intake Diagnostic

## Purpose
Inspect MassiveForecasting-V3 as a reference Shiny architecture before Stage 07 Block 7.0, without copying or modifying Shiny files.

## Active Project Root
`C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1`

## Reference Shiny Project Path
`C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1\MassiveForecasting-V3`

## Target Shiny App Path
`C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1\shiny_app`

## Key Reference Architecture Patterns
The reference app uses a modular Shiny dashboard structure with separate runner/library/UI/header/sidebar/body/server files. It contains dashboardPage/dashboardHeader/dashboardSidebar/dashboardBody patterns and tab/card/table style UI concepts.

## Reusable Patterns
Reusable or adaptable patterns include modular source organization, header/sidebar/body separation, sidebar navigation, dashboard cards/boxes, tabItems, and central dependency loading.

## Patterns Not To Reuse
Do not reuse forecasting engines, backtesting runners, data cooking/import scripts, model registry logic, project-specific CGR/income labels, or server-side recomputation patterns.

## Existing shiny_app Reconciliation
The target `shiny_app/` is populated and should be preserved until Stage 07 planning decides whether to wrap, supersede, or selectively adapt it. No target files were modified.

## Governance Fit / Gap Assessment
The reference layout fits with adaptation. Runtime modeling, forecasting, data cooking, and domain-specific copy do not fit the Stage 06 read-only/no-recompute governance contract.

## Recommended Stage 07 Structure
Use a TESSERACT-specific shell with Cover/Landing Page, Executive Overview, Champion Decision, Champion Conditions, Model Universe, Tournament Evidence, Pairwise Evidence, Risk Register, Deferred Models, Governance Actions, Audit Trail, Source Artifacts, Methodology / Metric Policy, and Footer / Version Info.

## Risks Before Implementation
- Runtime risk rows detected in reference app: 1035
- High-risk reference runtime rows: 359
- Dependencies inventoried: 16
- Existing target app files needing manual reconciliation: 38

## Recommendation
PROCEED_TO_STAGE_07_BLOCK_7_0_SHINY_SHELL_PLAN

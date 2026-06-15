# Stage 07 Block 7.0B Shell Plan Report

## Purpose
Create the Stage 07 Shiny shell plan, visual execution protocol, and baseline app launch record without modifying `shiny_app/`.

## Active Project Root
`C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1`

## Visual Execution Requirement
From 7.0C forward, every Shiny-changing block must launch the app, provide URL, port, HTTP status, PID, logs, modified files, and visual notes, and wait for Oscar visual inspection before proceeding.

## Reference App Influence
MassiveForecasting-V3 informs modular layout patterns: runner, header, sidebar, body, cards, tabs, footer/version concepts, and dependency organization.

## Why Reconcile Instead Of Rebuild From Scratch
The target `shiny_app/` is already populated. Stage 07 should preserve the current baseline, then selectively adapt or supersede files under a visual-validation protocol rather than wholesale replacement.

## Proposed Shell Architecture
The shell will use a V1-rooted, read-only dashboard structure with app runner, global setup, display-only libraries, constants, read-only data loader, header, sidebar, body/tabs, modules, CSS, and server orchestration.

## Navigation Map
The planned navigation includes Cover / Landing Page, Executive Overview, Champion Decision, Champion Conditions, Model Universe, Tournament Evidence, Pairwise Evidence, Risk Register, Deferred Models, Governance Actions, Audit Trail, Source Artifacts, Methodology / Metric Policy, and Footer / Version Info.

## File Change Plan
No `shiny_app/` file is modified in 7.0B. Later blocks will modify app/global/constants/loaders/UI/server/modules only after visual baseline inspection and Claude audit checkpoints.

## Governance Binding
All dashboard data must come from governed artifacts through read-only bindings. Champion decision remains conditional, confidence remains medium, FastNeuralAR_MLP risk and NBEATS/NHITS deferrals remain visible.

## Baseline App Launch Result
See `stage07_baseline_app_launch_validation.csv` for URL, PID, HTTP status, logs, and stop command.

## Risks
Existing app modules and `R/llm_client.R` require manual governance review. Reference runtime/modeling logic must not be reused.

## Next Recommended Block
PROCEED_TO_STAGE_07_BLOCK_7_0C_LANDING_PAGE after Oscar reviews the baseline UI.

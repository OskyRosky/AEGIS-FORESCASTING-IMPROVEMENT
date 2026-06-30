# V3.2G — Evaluated challengers integrated into the Forecast Viewer

Status: COMPLETED & VALIDATED (live).
Date: 2026-06-26

> **SUPERSEDED — see "V3.2G FINAL UI REFACTOR" at the bottom of this file.**
> The original integration below (6 challengers in a separate Viewer group +
> a Models → Evaluation page) was replaced, at the user's request, by a final
> UI/UX simplification: 4 Viewer families, only 3 Deep Learning models, and the
> Evaluation page merged into Tournament and Champion.

## Objective
Surface the 6 evaluated challenger candidates (V3.2D/V3.2E) inside the
Forecast Viewer (Forecasting > Viewer) as HISTORICAL BACKTEST lines, per the
user's explicit request ("para mi es importante verlo en el Viewer", "se debe
implementar"). Read-only; champion, forecasts, intervals and governance
unchanged.

## Design decisions (user-confirmed)
- Artifact strategy: **Option A** — append challenger rows directly to the
  existing Viewer artifact `data/processed/forecast_viewer_model_outputs.csv`
  (the artifact is also read by the Accuracy page, which therefore now also
  shows the challengers — accepted by the user).
- Presentation: **separate model-family group** labeled
  "Evaluation challengers (V3.2D/V3.2E)".
- Model labels: **short codes** (ENET-RIDGE, NLIN-DLIN_FIXED, LGBM-IMP-v2,
  XGB-IMP-v2, SMLP-TCN, FNAR-V2).

## What was done
1. Transform script `outputs/v3_2g_viewer_challenger_integration/append_challengers_to_viewer.R`
   maps `outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv`
   (81,720 rows, 6 candidates) into the Viewer contract and appends them:
   - model_name = candidate_id; model_family = "evaluation_challenger";
     model_origin = "challenger"; forecast_type = "backtest";
     is_challenger = True; is_selected_champion = False; risk_status = "ok";
     intervals empty. date = forecast_date; horizon_days = horizon.
   - Idempotent (strips prior evaluation_challenger rows); backs up original
     artifact to logs/ before writing.
2. `shiny_app/R/helpers.R`: added "evaluation_challenger" to FVP_FAMILY_ORDER
   and FVP_FAMILY_LABELS = "Evaluation challengers (V3.2D/V3.2E)". Server loops
   are generic so no server.R change was needed.
3. `shiny_app/ui/tabs.R`: added one how-to bullet explaining the challenger
   group is historical backtest only and does not change the champion.

## Feasibility facts (verified)
- 39 challenger series == 39 Viewer series exactly.
- Scale & dates identical (APC-Dedicated 2025-05-03 actual 2427.007518).
- Each challenger has 13,620 rows == per-model row count of existing Viewer
  models -> forecast_dates align, ACTUAL line unchanged.
- Horizon 1-30 (UI offers 5,10,15,20,25,30).

## Validation
- Append: 177,060 -> 258,780 rows; evaluation_challenger = 81,720; champion
  rows (is_selected_champion=True) = 13,620 untouched. Backup created.
- Smoke test: fvp_data 258,780 rows / 5 families; fvp_model_meta('APC-Dedicated')
  shows 6 challengers all non-champion; fvp_forecast_series ENET-RIDGE h=5 = 12
  pts; fvp_chart(ETS Explicit+ENET-RIDGE+SMLP-TCN) builds 4 series OK;
  champion still only ETS Explicit.
- Live: app pid 5672 on :3838, HTTP 200, 262KB, "Listening on", 0 errors
  (1 benign readr parsing warning). Static HTML contains the new group label.
- forecasts.csv (6/10) and forecasts_with_intervals*.csv (6/24-6/25) UNCHANGED;
  only forecast_viewer_model_outputs.csv modified.
- v3_2g_validation.csv: challenger_models=6, challenger_series=39,
  challenger_rows=81720, total_rows=258780, champion_rows=13620,
  backup_exists=1.

## Governance
No V1/V2 touched; no champion change; no forecasts.csv/intervals change; no
governance/promotion change (0 promoted); no model runs. Challengers shown as
historical backtest only. Viewer still "does not generate future forecasts".

## Reversibility
Original Viewer artifact backed up at
`outputs/v3_2g_viewer_challenger_integration/logs/forecast_viewer_model_outputs_BACKUP_<ts>.csv`.
Re-running the script is idempotent.

---

# V3.2G FINAL UI REFACTOR (closure)

Status: COMPLETED & VALIDATED (live, pid 36528 :3838 HTTP 200).
Date: 2026-06-26

## Objective (user 8-point spec)
A final UI/UX simplification before closing V3.2G — strictly presentation, no
data/governance change:
1. Remove the Models → Evaluation page completely.
2. Merge all evaluation content into the existing Tournament and Champion pages.
3. Keep the Models section with only: Universe, Tournament, Champion.
4. In the Forecast Viewer, keep only four model families: Growth Baseline,
   Statistical, Machine Learning, Deep Learning.
5. Rename "Lightweight Neural" to "Deep Learning".
6. Remove the standalone "Evaluation Challengers" group.
7. Only expose the three final Deep Learning models selected for comparison.
8. Preserve the underlying data and governance artifacts.

## What was done
- **Removed** `section_evaluation()` and its `app_sections()` registration in
  `shiny_app/ui/tabs.R`; removed the evaluation nav item in
  `shiny_app/ui/sidebar.R` and the evaluation `guide_entry` in
  `shiny_app/ui/body.R`. Models nav is now Universe / Tournament / Champion.
- **Merged into Tournament** (`section_tournament`): `dv =
  model_eval_dashboard_values()` plus four collapsibles — "Challenger
  evaluation at a glance" (KPI cards), "Challenger ranking"
  (`model_eval_ranking_table_ui`), "Evaluation summary & decision"
  (`model_eval_summary_table_ui`), "Runtime & guardrails"
  (`model_eval_runtime_table_ui`).
- **Merged into Champion** (`section_champion`): the existing "Challenger
  evaluation (V3.2D/V3.2E)" block now also renders the champion comparison
  table (`model_eval_champion_table_ui`); the dangling "See Models →
  Evaluation Results" reference points to the Tournament page.
- **Viewer families** (`shiny_app/R/helpers.R`): `FVP_FAMILY_ORDER` reduced to
  four families (no `evaluation_challenger`); `FVP_FAMILY_LABELS`
  `lightweight_neural = "Deep Learning"`. `fvp_model_label()` no longer adds the
  ⚠ high-risk badge (keeps the ★ champion badge); `fvp_chart()` uses a solid
  line for every model; `fvp_default_models()` swaps `FastNeuralAR_MLP` →
  `SMLP-TCN`. Viewer how-to bullet and model-picker hint updated; the Universe
  "Detailed results" row points to Tournament/Champion.
- **Viewer artifact** regenerated by
  `outputs/v3_2g_viewer_challenger_integration/refactor_viewer_deep_learning.R`:
  strips the `evaluation_challenger` rows, the six candidate codes and the
  legacy `FastNeuralAR_MLP` rows, then appends only SMLP-TCN, NLIN-DLIN_FIXED
  and FNAR-V2 mapped to `model_family = "lightweight_neural"`
  (is_challenger=True, is_selected_champion=False, risk_status="ok"). Idempotent;
  backs up the artifact first.

## Final Viewer structure
- **Growth baseline**: FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6
- **Statistical**: ARIMA_Fixed, AutoARIMA, ETS Explicit (★ champion), ETS_Current, Theta
- **Machine learning**: LightGBM, LinearRegression, XGBoost
- **Deep Learning**: SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2

## Validation
- Artifact: 204,300 rows. Family counts — growth_baseline 54,480,
  statistical 68,100, machine_learning 40,860, lightweight_neural 40,860
  (3 DL models × 39 series). Champion rows (is_selected_champion=True) = 13,620
  UNCHANGED. Backup `logs/forecast_viewer_model_outputs_BACKUP_20260626_135651.csv`.
  Script assertions (exactly 4 families; DL = the 3 models; no FastNeuralAR_MLP)
  all passed. `v3_2g_refactor_validation.csv` written.
- Smoke test `smoke_test_refactor.R`: FVP families = 4; Deep Learning = the 3
  models; label drops the high-risk badge; defaults include SMLP-TCN not
  FastNeuralAR_MLP; `app_sections()` builds; Models nav = Universe/Tournament/
  Champion; `section_evaluation` no longer exists. ALL CHECKS PASSED.
- Live: app pid 36528 on :3838, HTTP 200, "Listening on", 0 errors (1 benign
  readr parsing warning).

## Governance
No V1/V2 touched; champion ETS Explicit unchanged; no forecasts.csv / intervals
/ governance / promotion change (0 promoted); no model runs. Dropped ML/DL
candidates remain available in `full_candidate_outputs.csv` and the governed
model_eval summaries. Strictly a UI/UX simplification.


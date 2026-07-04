# V3.3A — Refresh Manifest (Pipeline Inventory)

**Stage:** V3.3A — Refresh Manifest
**Type:** Documentation / inventory only (no execution)
**Date:** 2026-06-26
**Project root:** `V3`
**Status:** `V3_3A_REFRESH_MANIFEST_COMPLETED`

---

## 1. Executive summary

V3.3A formalizes the inventory of the AEGIS daily refresh pipeline as the foundation for
the daily-at-10:00 automation (V3.3). It documents **15 stages** (S00–S14) with their real
scripts, inputs, outputs, dashboard areas, VPN/SQL needs, light/heavy classification,
runtime estimates, failure behavior, staging/promote policy and Last Update dependency.

No pipeline was executed. No models or backtests were run. No productive `data/processed`
artifact was modified. No scheduler was created. V3.3B (benchmark) was **not** started.

Key findings:
- **No top-level orchestrator exists yet** — stages run as individual scripts today.
- **Only S00/S01 require VPN+SQL.** Everything downstream is local compute on `data/processed`.
- **S03 (model execution/backtest) is the dominant cost** (~60–90 min, 60–90% of total).
- **Last Update today is driven by S02 (Transform)**; V3.3E will move it to an end-of-pipeline
  seal (S11) so the header reflects full-pipeline success, not just data refresh.
- **Auth is interactive today** (`ActiveDirectoryInteractive` in `python/ingestion/config.py`);
  whether it runs unattended with VPN + cached token is the #1 open question for V3.3B.

---

## 2. Pipeline structure

| Order | Stage | Group | Light/Heavy |
|-------|-------|-------|-------------|
| 0 | S00 Auth / VPN / SQL pre-check | gate | light |
| 1 | S01 Ingestion | ingestion | light |
| 2 | S02 Transform / data contract | transform | light |
| 3 | S03 Model execution / backtest | models | **HEAVY** |
| 4 | S04 Forecast outputs / viewer handoff | forecasting | light |
| 5 | S05 Tournament / scorecard / champion | models | heavy |
| 6 | S06 Candidate / canonical universe (15 models) | models | light |
| 7 | S07 Evaluation exports | evaluation | light |
| 8 | S08 Governance exports (6.0–6.5) | governance | light |
| 9 | S09 Reference exports | reference | light |
| 10 | S10 Dashboard artifacts consolidation | dashboard | light |
| 11 | S11 Last Update / run metadata seal | metadata | light |
| 12 | S12 Pipeline status | metadata | light |
| 13 | S13 Champion auto-apply + audit | governance | light |
| 14 | S14 Final validation | validation | light |

---

## 3. Daily full refresh path

```
10:00 Scheduler
  -> S00 VPN/SQL gate
  -> S01 Ingestion (SQL -> data/raw)
  -> S02 Transform (data/raw -> data/processed staging)
  -> S03 Model execution / backtest        [HEAVY ~60-90 min]
  -> S04 Forecast outputs / viewer handoff
  -> S05 Tournament / scorecard / champion
  -> S06 Canonical 15-model universe
  -> S07 Evaluation exports
  -> S08 Governance exports (6.0-6.5)
  -> S09 Reference exports
  -> S10 Dashboard artifacts consolidation
  -> S14 Final validation
  -> (validate OK) Promote staging -> data/processed
  -> S11 Last Update seal + S12 Pipeline status
  -> S13 Champion auto-apply (if guardrails pass) + audit
  -> Dashboard refreshed
```

Expected total: **~75–105 min sequential** (full daily). Start 10:00 → ready **~11:15–11:45**.
To be confirmed with measured numbers in V3.3B.

---

## 4. Optional light/heavy path (future)

The manifest tags each stage `is_light_stage` / `is_heavy_stage` so a two-tier schedule can
be enabled later without rework:

- **daily_light (~5–8 min):** S00, S01, S02, S04 (cached), S07, S08, S09, S10, S11, S12, S14.
- **weekly_heavy (~75–105 min):** adds S03, S05, S06, S13 (re-train + re-tournament + champion).

Current decision is **full daily**; the light/heavy split is documented but **not** activated.

---

## 5. Auth / VPN / SQL considerations

- Only **S00 + S01** touch the network. Source: `tesseractearth.database.windows.net` /
  `TesseractEarthDW`, ODBC Driver 18, auth `ActiveDirectoryInteractive`
  (`python/ingestion/config.py`).
- **Gate rule (S00):** if VPN is down or SQL is unreachable, abort before any write and keep
  the prior day's artifacts intact.
- **Open risk:** interactive auth may prompt a browser login each run. V3.3B must confirm
  whether a cached token over VPN runs unattended, or whether a non-interactive method
  (service principal / managed identity, planned for the Azure phase) is required.

---

## 6. Input / output map (high level)

| Stage | Reads | Writes |
|-------|-------|--------|
| S01 | Azure SQL | `data/raw/*.csv` |
| S02 | `data/raw/*` | `data/processed/{actuals,forecasts,forecast_comparison,entities,run_metadata}.csv` |
| S03 | `data/processed/{actuals,forecasts}` + features | `outputs/model_lab/*` metrics & forecasts |
| S04 | S03 outputs | `data/processed/forecast_viewer_model_outputs.csv` + intervals |
| S05 | S03 metrics | `outputs/model_lab/tournament_engine/*` + champion decision |
| S06 | S05 scorecard + candidate medians | `data/processed/model_universe_canonical.csv` |
| S07 | S03/S04 | `outputs/dashboard/*.csv` |
| S08 | S07 + champion | `outputs/governance/*.csv` |
| S09 | config + run_metadata | Reference-tab artifacts |
| S11 | pipeline completion | `data/processed/run_metadata.csv` + `last_update.csv` |
| S12 | per-stage timings | `data/processed/refresh_status.csv` |
| S13 | S05 champion vs prior | `outputs/v3_3_daily_refresh/champion_change_audit.csv` |

---

## 7. Dashboard area mapping

- **Universe (15 models)** ← S06 canonical
- **Models** ← S03 + S05
- **Forecasting / Viewer** ← S04
- **Tournament / Champion** ← S05 (+ S13 audit)
- **Accuracy / Evaluation** ← S07
- **Governance** ← S08
- **Reference** ← S09
- **Header Last Update / Status** ← S11 + S12

---

## 8. Staging / promote policy

- Each writing stage produces output in a **staging area** first.
- Promotion to `data/processed/` happens **only after S14 validation passes**.
- On any abort, `data/processed/` retains the **prior successful day**; the dashboard never
  shows half-written files.
- `S11` (Last Update) and `S12` (status) are written **last**, so the header only advances on
  a fully successful run.

---

## 9. Failure behavior

| Condition | Behavior |
|-----------|----------|
| VPN/SQL down (S00/S01) | ABORT before any write; keep prior day |
| Transform/model/eval/gov failure | ABORT; keep prior `data/processed`; do not seal Last Update |
| Tournament/champion failure (S05) | Keep prior champion |
| Guardrail fail (S13) | Keep prior champion; log to audit |
| Validation fail (S14) | Mark run `partial`/`failed` in `refresh_status.csv`; do not promote |

---

## 10. Runtime estimate summary

| Bucket | Estimate |
|--------|----------|
| Gate + Ingestion + Transform (S00–S02) | ~3 min |
| Model execution / backtest (S03) | ~60–90 min (HEAVY) |
| Tournament + canonical (S05–S06) | ~6 min |
| Forecast + Evaluation + Governance + Reference (S04, S07–S09) | ~6–12 min |
| Metadata + audit + validation (S10–S14) | ~5 min |
| **Total full daily** | **~75–105 min sequential** |
| Light path (no S03/S05/S06/S13) | ~5–8 min |

Measured anchors: XGBoost ~22.3 min; LightGBM ~7.7 min; 60-day 13-model backtest ~10.3 min.

---

## 11. Open questions for V3.3B benchmark

1. Does `ActiveDirectoryInteractive` run unattended over VPN with a cached token, or do we
   need a non-interactive auth flow now?
2. Exact end-to-end wall-clock on this machine (single timed full run).
3. Is there a standalone **Reference export** runner (S09), or is Reference purely static
   config + run_metadata?
4. Is there a standalone **dashboard consolidation** step (S10) beyond S04/S07/S08?
5. Can S03 be parallelized safely to cut the ~22 min XGBoost bottleneck?
6. Which artifacts must be staged vs can be written in place safely?

---

## 12. Recommended next step

Proceed to **V3.3B — Runtime Benchmark**: one manual, VPN-connected, timed end-to-end run to
(a) measure real per-stage and total duration, and (b) resolve the auth/Reference/consolidation
open questions. **Do not start V3.3B without explicit authorization.**

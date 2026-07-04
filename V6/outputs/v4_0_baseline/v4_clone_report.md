# V4.0 — Baseline Formal V4 (Clone Report)

- **Status:** `V4_0_BASELINE_COMPLETED`
- **Date:** 2026-06-29
- **Project:** AEGIS V4 (local-first LLM explanation layer)
- **Based on:** V3 (`V3_MVP_CLOSED`)

## 1. What V4 is

V4 is a new, fully self-contained active version cloned from the closed V3 MVP. Its
purpose is to add a **local-first LLM explanation layer** on top of existing,
governed artifacts — **not** a new forecasting engine.

**Mother rule (carried into V4):** Shiny does not compute or modify productive
artifacts; it may only build temporary read-only evidence packs for on-demand LLM
explanations. In V4.0 that logic is **not** implemented yet — this phase only
formalizes the baseline.

## 2. How V4 was created

- V4 was cloned from V3 via `robocopy /E`, excluding `.venv`, `__pycache__`, and `*.pyc`.
- At clone time, file parity was 1798 = 1798.
- Root markers were updated to make V4 the active version:
  - `config/project_root_policy.json`: `active_version = V4`, `based_on_version = V3`,
    `v3_mvp_status = V3_MVP_CLOSED`.
  - `ACTIVE_PROJECT_ROOT.md` and `VERSION_INFO.md` updated to V4 (based_on V3).

## 3. Baseline evidence (verified live 2026-06-29)

| Item | Observed |
|------|----------|
| V1 / V2 / V3 / V4 roots exist | TRUE / TRUE / TRUE / TRUE |
| active_version | V4 |
| based_on_version | V3 |
| v3_mvp_status | V3_MVP_CLOSED |
| Governance model scope (`model_universe_canonical.csv` rows) | 15 |
| Champion | ETS Explicit |
| V4 `run_metadata` snapshot | 2026-06-28T17:27:14 (forecast_version 2026-05-01) |
| V4 dashboard (port 3839) | HTTP 200, LEN 275129 |
| V3 dashboard (port 3838, reference) | HTTP 200, LEN 275129 |

## 4. Accepted caveats

- **Snapshot date:** V4 was cloned **before** the 2026-06-29 V3 manual refresh, so V4
  `data/processed/run_metadata.csv` shows **2026-06-28T17:27:14** and the dashboard
  "Last Update" reads **2026-06-28**. This is **accepted by decision** — V4 is an
  explanation layer and does not need the freshest data to design the LLM. **No
  resync to 2026-06-29 was performed in this phase.**
- **File count divergence (V3 = 1923 vs V4 = 1800):** Expected. V3 grew after V4 was
  cloned because today's V3 manual refresh created additional run directories,
  backups, and logs inside V3. Parity at clone time was 1798 = 1798.
- **`run_metadata.model_count = 16`** is the data-contract series count in the
  actual/forecast contract; the **governance model scope is 15** as defined by
  `model_universe_canonical.csv`. Governance scope (15) is authoritative.

## 5. What was NOT done in V4.0 (guardrails honored)

- No V4.1 work started; no evidence packs designed; no LLM buttons created.
- No Shiny UI changes; no Azure OpenAI connection; Nayeli pattern is future reference only.
- No resync of V4 to 2026-06-29.
- No changes to V1 / V2 / V3.
- No SQL executed; no models run.
- No modification of `data/raw` or productive `data/processed`.
- No promotion of any artifact; champion and governance unchanged.

## 6. Closure

**V4.0 is formally closed: `V4_0_BASELINE_COMPLETED`.** Next phase (V4.1 — LLM design,
paper only) is **pending explicit authorization** and not started.

# AEGIS V6.0A — Clone Report

**Stage:** V6.0A — Baseline Clone desde V5 (Track A — Consumidor read-only)
**Status:** `V6_0A_BASELINE_CLONE_COMPLETED`
**Date:** 2026-07-03

## What was done
V6 was created as a **controlled robocopy clone of the closed V5** (V5 LOCAL
DOCKER MVP CLOSED), excluding `.venv / __pycache__ / *.pyc / *.pyo /
.Rproj.user / .ipynb_checkpoints`. Root markers were updated to V6; the app code
was **not** modified (byte-parity). A native local smoke confirmed the dashboard
starts identically from its own V6 root.

## Clone
- Command: `robocopy V5 V6 /E /XD .venv __pycache__ .Rproj.user .ipynb_checkpoints /XF *.pyc *.pyo /MT:16`
- Result: exit 1 (files copied OK). **V6 = 2271 files / 1415.1 MB** — exact
  count/size parity with V5.

## Parity (byte-level, SHA256 aggregate)
| Area | V5 | V6 | Status |
|------|----|----|--------|
| data/processed | 24 files · B0880D33…D61 | 24 · B0880D33…D61 | IDENTICAL |
| outputs/model_lab/model_lab_closure_pack | 13 · 00F3F644…0C | 13 · 00F3F644…0C | IDENTICAL |
| shiny_app | 48 · 441A1B59…1C | 48 · 441A1B59…1C | IDENTICAL |

## Root markers updated (V6 only)
- `ACTIVE_PROJECT_ROOT.md` → active root = V6 (V1–V5 frozen; describes Track A/B + hard gate).
- `VERSION_INFO.md` → version_name=V6, based_on=V5, current_status=V6.0A, next_stage=V6.0B.
- `config/project_root_policy.json` → active_version=V6, based_on_version=V5, v5_mvp_status=V5_DOCKER_LOCAL_MVP_CLOSED (valid JSON).

## Native smoke (V6 own root)
Launched `scripts/start_shiny.ps1 -PreferredPort 3841` → PID 35568 →
**HTTP 200, LEN 303501** (= V5.0A native baseline), champion **ETS Explicit**,
**15 models**, horizons **30/60/180**, **10** "Generate explanation". Server
stopped cleanly (port 3841 released).

## Governance / safety
- No Azure, no SQL, no real refresh, no functional change. `shiny_app` is
  byte-identical to V5.
- Champion frozen = ETS Explicit; 15 models; prohibited models absent (inherited).
- V1/V2/V3/V4/V5 untouched. V5 Docker container remained healthy on :8080; V5
  data hashes unchanged.

## Note (inherited cosmetic quirk)
`shiny_app/R/constants.R` `APP_VERSION = "V4"` (inherited from V4→V5; V5 never
bumped it). Left **unchanged** to preserve clone byte-parity. Can be updated to
"V6" as a documented cosmetic step later (e.g., in V6.0B or a UI polish stage).

## Next
**V6.0B — Azure Readiness + Architecture Decisions** (audit + decisions only; no
Azure resources). Requires explicit authorization.

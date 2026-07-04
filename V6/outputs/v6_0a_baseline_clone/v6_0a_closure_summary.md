# AEGIS V6.0A — Closure Summary

**Stage:** V6.0A — Baseline Clone desde V5 (Track A — Consumidor read-only)
**Status:** `V6_0A_BASELINE_CLONE_COMPLETED`
**Date:** 2026-07-03
**Authorization:** "Iniciemos ... Primero vamos con: V6.0A — Baseline Clone desde V5."

## Outcome
V6 creado como copia controlada de V5 (cerrado). Paridad byte a byte en data,
closure pack y shiny_app; markers actualizados a V6; smoke nativo local OK; V5 y
versiones previas intactas. Sin Azure, sin SQL, sin refresh real, sin cambio
funcional. Sin blockers.

---

## Tabla 1 — Artifacts creados/modificados

| artifact | path | created_or_modified | purpose | status |
|----------|------|---------------------|---------|--------|
| V6 (árbol completo) | AEGIS-.../V6/ | created | copia controlada de V5 | PASS |
| ACTIVE_PROJECT_ROOT.md | V6/ | modified | active root = V6 | PASS |
| VERSION_INFO.md | V6/ | modified | version_name=V6, based_on=V5, status V6.0A | PASS |
| config/project_root_policy.json | V6/ | modified | active_version=V6 (valid JSON) | PASS |
| v6_0a_preflight_check.csv | V6/outputs/v6_0a_baseline_clone/ | created | pre-flight | PASS |
| v6_0a_clone_report.md | " | created | reporte de clon | PASS |
| v6_0a_parity_check.csv | " | created | paridad byte-level | PASS |
| v6_0a_root_marker_check.csv | " | created | markers | PASS |
| v6_0a_dashboard_smoke_check.csv | " | created | smoke nativo | PASS |
| v6_0a_invariants_check.csv | " | created | invariantes | PASS |
| v6_0a_validation.csv | " | created | DoD 20 checks | PASS |
| v6_0a_closure_summary.md | " | created | este archivo | PASS |
| logs/v6_0a_shiny_*.log | V6/outputs/v6_0a_baseline_clone/logs/ | created | logs del smoke | PASS |
| shiny_app / data / outputs | V6/ | UNCHANGED (byte-parity) | sin cambio funcional | PASS |

## Tabla 2 — Parity / clone validation

| check | expected | observed | status | evidence |
|-------|----------|----------|--------|----------|
| file_count | V5==V6 | 2271==2271 | PASS | Get-ChildItem |
| total_size | V5==V6 | 1415.1==1415.1 MB | PASS | Measure-Object |
| data/processed hash | identical | B0880D33…D61 == | PASS | SHA256 |
| closure_pack hash | identical | 00F3F644…0C == | PASS | SHA256 |
| shiny_app hash | identical | 441A1B59…1C == | PASS | SHA256 |
| exclusions | venv/pycache/pyc | applied | PASS | robocopy /XD /XF |

## Tabla 3 — Root markers

| marker | field | observed | status |
|--------|-------|----------|--------|
| ACTIVE_PROJECT_ROOT.md | active_root | V6 | PASS |
| VERSION_INFO.md | version_name / based_on | V6 / V5 | PASS |
| VERSION_INFO.md | current_status / next_stage | V6.0A / V6.0B | PASS |
| project_root_policy.json | active_version / valid | V6 / valid JSON | PASS |
| constants.R | APP_VERSION | V4 (inherited quirk, unchanged for parity) | NOTED |

## Tabla 4 — Dashboard smoke (native, V6 root)

| check | expected | observed | status |
|-------|----------|----------|--------|
| http_200 | 200 | 200 LEN 303501 | PASS |
| champion | ETS Explicit | found | PASS |
| scope | 15 models | found | PASS |
| horizons | 30/60/180 | found | PASS |
| assistants | 10 | x10 | PASS |
| server stopped | port released | 3841 free | PASS |
| V5 untouched | intact | Docker healthy; data unchanged | PASS |

## Tabla 5 — Riesgos / blockers

| risk_id | area | risk | severity | blocker | mitigation | status |
|---------|------|------|----------|---------|-----------|--------|
| R1 | azure_permissions | falta confirmar permisos Azure (prereq V6.0B) | medium | no | se cierra en V6.0B antes de crear recursos | open_for_v6_0b |
| R2 | app_version_label | constants.R APP_VERSION="V4" (cosmético) | low | no | dejar para paso cosmético documentado | noted |
| R3 | onedrive_locks | clon bajo OneDrive | low | no | robocopy /R:2 OK; sin locks | mitigated |
| R4 | highcharts_license | licencia Highcharts (heredado) | medium | no | endpoint privado en V6.3 | carried_forward |

**Blockers: NONE.**

## Tabla 6 — Estado global V6

| stage | status | notes | next_step |
|-------|--------|-------|-----------|
| V6.0A | V6_0A_BASELINE_CLONE_COMPLETED | clon controlado de V5, paridad, smoke | **current** |
| V6.0B | pending | Azure Readiness + Architecture Decisions (audit only) | needs authorization |
| V6.1–V6.4 | pending | Track A (identity/registry/deploy/downloads) | needs authorization |
| GATE | pending | hard gate review antes de Track B | needs authorization |
| V6.5–V6.10 | pending | Track B (SQL/refresh/scheduler/LLM/observability/closure) | gated |

---

**Do NOT advance to V6.0B without explicit Oscar authorization.**

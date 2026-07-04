# AEGIS V5.3 — Closure Summary

**Stage:** V5.3 — External Volumes / Artifact Mounts
**Status:** `V5_3_EXTERNAL_VOLUMES_ARTIFACT_MOUNTS_COMPLETED`
**Date:** 2026-07-03
**Authorization:** verbatim "Autorizo iniciar AEGIS V5.3 — External Volumes / Artifact Mounts."

## Outcome

Formalized and proved the external volume / artifact contract for AEGIS V5. The
image carries **only code + R dependencies**; all governed artifacts live outside
the image and are consumed from **read-only** bind mounts (`data/processed`,
`outputs`). All 9 required loader artifacts are present in the container.
`data/raw` is neither baked nor mounted and is not a runtime dependency. An
external probe change was reflected inside the container **without rebuild,
without image-ID change, and without restart**. Read-only writes are blocked.
`data/processed` and `data/raw` are byte-identical to their pre-stage baseline.
Image ID unchanged (`ed86271fff04`). V5.1 files, V5.2 Compose, and V1–V4 intact.
Smoke test 11/11 PASS. No blockers.

---

## Table 1 — Artifacts created / modified

| artifact | path | created_or_modified | purpose | status |
|----------|------|---------------------|---------|--------|
| v5_3_preflight_check.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | pre-flight gate | PASS |
| v5_3_runtime_artifact_manifest.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | 43-row runtime dependency manifest | PASS |
| v5_3_runtime_artifact_map.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | image-vs-mount map | PASS |
| v5_3_compose_volume_audit.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | compose volume audit | PASS |
| v5_3_volume_contract.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | volume contract for V5.4/5.5/5.7/5.8 | PASS |
| v5_3_container_mount_inspection.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | in-container mount checks | PASS |
| v5_3_no_rebuild_reflection_test.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | reflection test table | PASS |
| v5_3_no_rebuild_reflection_test.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | reflection test report | PASS |
| v5_3_readonly_enforcement.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | RO write-block evidence | PASS |
| v5_3_smoke_test_results.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | reused smoke test (11/11) | PASS |
| v5_3_immutability_check.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | data/image immutability | PASS |
| v5_3_compose_hardening_review.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | hardening decision (no change) | PASS |
| v5_3_compose_integrity_check.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | compose integrity | PASS |
| v5_3_volume_usage_guide.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | local usage guide | PASS |
| v5_3_risk_register.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | 8 risks | PASS |
| v5_3_validation.csv | outputs/v5_3_external_volumes_artifact_mounts/ | created | 32-check Definition of Done | PASS |
| v5_3_closure_summary.md | outputs/v5_3_external_volumes_artifact_mounts/ | created | this file | PASS |
| _presence_probe2.R | outputs/v5_3_external_volumes_artifact_mounts/ | created | repeatable in-container presence probe | PASS |
| host_probe.txt | outputs/v5_3_external_mount_probe/ | created | reflection probe evidence (v2) | PASS |
| logs/*.log (4) | outputs/v5_3_external_volumes_artifact_mounts/logs/ | created | mount/reflection/readonly/smoke logs | PASS |
| docker-compose.yml / Dockerfile / .dockerignore / entrypoint.sh / smoke_test.ps1 | V5/ | UNCHANGED | V5.1/V5.2 integrity | PASS |

## Table 2 — Runtime artifact manifest summary

| artifact_group | host_path | container_path | required_count | present_count | missing_count | status | notes |
|----------------|-----------|----------------|----------------|---------------|---------------|--------|-------|
| closure_pack | ./outputs/model_lab/model_lab_closure_pack | /app/outputs/model_lab/model_lab_closure_pack | 4 | 8 | 0 | PASS | 4 required + 4 optional |
| tournament | ./outputs/model_lab/tournament_engine | /app/outputs/model_lab/tournament_engine | 2 | 4 | 0 | PASS | standings + scorecard required |
| challenger | ./outputs/model_lab/challenger_* | /app/outputs/model_lab/challenger_* | 0 | 2 | 0 | PASS | diagnostics |
| governance | ./outputs/governance/6_3_champion_conditions | /app/outputs/governance/6_3_champion_conditions | 2 | 2 | 0 | PASS | conditions + language |
| audit | ./outputs/... + governance/audit_6 | /app/outputs/... | 0 | 5 | 0 | PASS | audit trail |
| methodology | ./outputs/... + ./docs | /app/outputs/... + /app/docs | 0 | 1 | 1 | PASS | benchmark_semantics optional, docs not mounted |
| forecasting | ./data/processed | /app/data/processed | 0 | 11 | 0 | PASS | forecasts/intervals/viewer/actuals |
| ttl | ./outputs + ./data/processed | /app/... | 0 | 2 | 1 | PASS | ttl_capacity roadmap placeholder |
| model_eval | ./data/processed | /app/data/processed | 0 | 6 | 0 | PASS | canonical 15-model universe |
| llm | ./outputs/v4_4_mock_provider | /app/outputs/v4_4_mock_provider | 1 | 1 | 0 | PASS | mock assistants JSON |
| **TOTAL** | — | — | **9 required** | **42** | **2 (opt/roadmap)** | **PASS** | 9/9 required present; 0 blocking |

## Table 3 — Volume / mount validation

| check | expected | observed | status | evidence |
|-------|----------|----------|--------|----------|
| /app/data/processed exists | yes | yes (24 csv) | PASS | docker exec |
| /app/outputs exists | yes | yes | PASS | docker exec |
| /app/outputs/model_lab | yes | yes | PASS | docker exec |
| /app/outputs/governance | yes | yes | PASS | docker exec |
| /app/data/raw | absent | no | PASS | docker exec |
| /app/BACKUP | absent | no | PASS | docker exec |
| /app/.env | absent | no | PASS | docker exec |
| data/processed read-only | write blocked | Read-only file system | PASS | docker exec touch |
| outputs read-only | write blocked | Read-only file system | PASS | docker exec touch |
| relative paths in compose | yes | ./ relative source | PASS | docker-compose.yml |
| no C:\Users / OneDrive in source | none | none | PASS | docker-compose.yml |

## Table 4 — No-rebuild reflection test

| test | expected | observed | image_id_before | image_id_after | status | evidence |
|------|----------|----------|-----------------|----------------|--------|----------|
| host probe v1 visible in container | visible | "Version 1." read | ed86271fff04 | ed86271fff04 | PASS | docker exec cat |
| host probe updated (v2) visible | visible no rebuild | "Version 2." read | ed86271fff04 | ed86271fff04 | PASS | docker exec cat |
| no docker build / compose build | not run | none | ed86271fff04 | ed86271fff04 | PASS | command history |
| no restart needed | reflected while Up | reflected without restart | ed86271fff04 | ed86271fff04 | PASS | uptime |
| image ID unchanged | same | unchanged | ed86271fff04 | ed86271fff04 | PASS | docker images |
| dashboard after probe | 200 | 200 (LEN 303385) | ed86271fff04 | ed86271fff04 | PASS | Invoke-WebRequest |

## Table 5 — Runtime / smoke validation

| check | expected | observed | status | evidence |
|-------|----------|----------|--------|----------|
| http_200 | 200 | 200 (LEN 303385) | PASS | smoke test |
| assistants | 10 | Generate explanation x10 | PASS | smoke test |
| champion | ETS Explicit | found | PASS | smoke test |
| scope | 15 models | found | PASS | smoke test |
| horizons | 30/60/180 | all found | PASS | smoke test |
| no python | NO_PYTHON | NO_PYTHON | PASS | smoke test |
| no data/raw baked | NO_RAW | NO_RAW | PASS | smoke test |
| no secrets in history | none | none | PASS | smoke test |
| container health | healthy | healthy | PASS | docker inspect |
| logs no critical error | benign | dplyr/vroom/Inter only | PASS | container logs |

## Table 6 — Riesgos / blockers

| risk_id | area | risk | severity | blocker_yes_no | mitigation | status |
|---------|------|------|----------|----------------|-----------|--------|
| R1 | downloads_v5_4 | outputs RO may affect V5.4 downloads | low | no | exports render to /tmp; RO doesn't block reads | open_for_v5_4 |
| R2 | repo_relocation | artifacts missing if repo moved / wrong cwd | low | no | relative ./ mounts; run from V5 root | mitigated |
| R3 | relative_mount_cwd | mounts depend on running from V5 root | low | no | documented in usage guide | mitigated |
| R4 | probe_confusion | probe files mistaken for productive artifacts | low | no | namespaced v5_3_*, not in registry | mitigated |
| R5 | inter_font_runtime | bslib downloads Inter font (inherited) | low | no | offline bundle future | carried_forward |
| R6 | highcharts_license | Highcharts commercial license (inherited) | medium | no | legal review flagged | carried_forward |
| R7 | refresh_headless_mfa | real refresh MFA/headless (inherited) | medium | no | refresh deferred to V5.5/V5.6 | carried_forward |
| R8 | windows_onedrive_locks | OneDrive locks affect host artifacts | low | no | RO reads; no host mutation | mitigated |

**Blockers: NONE.**

## Table 7 — Estado global V5

| stage | status | notes | next_step |
|-------|--------|-------|-----------|
| V5.0A | V5_0A_BASELINE_CLONE_COMPLETED | clone from V4 | done |
| V5.0B | V5_0B_DOCKER_READINESS_REPRODUCIBILITY_COMPLETED | audit + decisions | done |
| V5.1 | V5_1_DOCKERFILE_DASHBOARD_IMAGE_COMPLETED | R-only image built | done |
| V5.2 | V5_2_DOCKER_COMPOSE_SHINY_SERVICE_COMPLETED | compose shiny service | done |
| V5.3 | V5_3_EXTERNAL_VOLUMES_ARTIFACT_MOUNTS_COMPLETED | external volume contract proven | **current** |
| V5.4 | pending | dockerized downloads validation | needs authorization |
| V5.5 | pending | refresh service dry-run/validate | gated |
| V5.6 | deferred | controlled refresh in container | MFA/headless gate |
| V5.7 | pending | docker runbook / internal docs | pending |
| V5.8 | pending | final docker closure | pending |

---

**Do NOT advance to V5.4 without explicit Oscar authorization.**

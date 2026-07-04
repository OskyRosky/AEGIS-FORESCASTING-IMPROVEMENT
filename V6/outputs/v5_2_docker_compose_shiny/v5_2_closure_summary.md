# AEGIS V5.2 — Closure Summary

**Stage:** V5.2 — Docker Compose Shiny Service
**Status:** `V5_2_DOCKER_COMPOSE_SHINY_SERVICE_COMPLETED`
**Date:** 2026-07-03
**Authorization:** verbatim "Autorizo iniciar AEGIS V5.2 — Docker Compose Shiny Service."

## Outcome

The manual V5.1 `docker run ...` command is now a reproducible one-line flow:
`docker compose up -d shiny`. A single `shiny` service serves the R-only AEGIS
dashboard, reusing the validated `aegis-dashboard:v5.1` image, with
`data/processed` and `outputs` mounted **read-only** and `data/raw` **not
mounted**. Container is healthy, HTTP 200 on `http://127.0.0.1:8080`, smoke test
**11/11 PASS**. No new features, no functional change, no refresh service, no
SQL / models / Azure / real LLM. V5.1 files and image unchanged. V1–V4 intact.

---

## Table 1 — Artifacts created / modified

| artifact | path | created_or_modified | purpose | status |
|----------|------|---------------------|---------|--------|
| docker-compose.yml | V5/docker-compose.yml | created | single `shiny` service, RO mounts, 8080:3838 | PASS |
| v5_2_preflight_check.csv | outputs/v5_2_docker_compose_shiny/ | created | pre-flight gate evidence | PASS |
| v5_2_compose_file_report.md | outputs/v5_2_docker_compose_shiny/ | created | compose design report | PASS |
| v5_2_compose_config_check.csv | outputs/v5_2_docker_compose_shiny/ | created | `docker compose config` validation | PASS |
| v5_2_compose_up_report.md | outputs/v5_2_docker_compose_shiny/ | created | up result report | PASS |
| v5_2_compose_up_check.csv | outputs/v5_2_docker_compose_shiny/ | created | up runtime checks | PASS |
| v5_2_smoke_test_results.csv | outputs/v5_2_docker_compose_shiny/ | created | reused V5.1 smoke test (11/11) | PASS |
| v5_2_mount_validation.csv | outputs/v5_2_docker_compose_shiny/ | created | RO mount + host-leak checks | PASS |
| v5_2_v5_1_integrity_check.csv | outputs/v5_2_docker_compose_shiny/ | created | V5.1 files/image integrity | PASS |
| v5_2_invariants_check.csv | outputs/v5_2_docker_compose_shiny/ | created | dashboard invariants | PASS |
| v5_2_security_compose_check.csv | outputs/v5_2_docker_compose_shiny/ | created | security/cleanliness | PASS |
| v5_2_local_usage_notes.md | outputs/v5_2_docker_compose_shiny/ | created | Oscar local usage guide | PASS |
| v5_2_risk_register.csv | outputs/v5_2_docker_compose_shiny/ | created | risks/blockers | PASS |
| v5_2_validation.csv | outputs/v5_2_docker_compose_shiny/ | created | 32-check Definition of Done | PASS |
| v5_2_closure_summary.md | outputs/v5_2_docker_compose_shiny/ | created | this file | PASS |
| logs/*.log (5) | outputs/v5_2_docker_compose_shiny/logs/ | created | config/up/container/smoke/mount logs | PASS |
| Dockerfile / .dockerignore / docker/entrypoint.sh / scripts/docker_smoke_test.ps1 | V5/ | UNCHANGED | V5.1 integrity preserved | PASS |

## Table 2 — Compose service summary

| item | expected | observed | status | evidence |
|------|----------|----------|--------|----------|
| service name | shiny | shiny | PASS | compose config |
| single service | yes | 1 service | PASS | compose config |
| image | aegis-dashboard:v5.1 | aegis-dashboard:v5.1 | PASS | compose config |
| build context | . / Dockerfile | context=. dockerfile=Dockerfile | PASS | compose config |
| ports | 8080:3838 | 8080->3838 tcp | PASS | compose config |
| working_dir | /app | /app | PASS | compose config |
| processed mount | ./data/processed:...:ro | read_only:true | PASS | compose config |
| outputs mount | ./outputs:...:ro | read_only:true | PASS | compose config |
| data/raw mount | absent | absent | PASS | compose config |
| refresh/scheduler/sql/azure/llm service | absent | absent | PASS | compose config |
| restart | unless-stopped | unless-stopped | PASS | compose config |
| healthcheck | inherited | image HEALTHCHECK inherited | PASS | Dockerfile |
| relative paths | yes | ./ relative in source | PASS | docker-compose.yml |

## Table 3 — Runtime / smoke validation

| check | expected | observed | status | evidence |
|-------|----------|----------|--------|----------|
| container running | running | running | PASS | docker compose ps |
| container healthy | healthy | healthy | PASS | docker inspect |
| external port | 8080 | 0.0.0.0:8080->3838 | PASS | docker compose ps |
| internal port | 3838 | Listening on 3838 | PASS | container logs |
| http_200 | 200 | 200 (LEN 303385) | PASS | Invoke-WebRequest |
| assistants | 10 | Generate explanation x10 | PASS | smoke test |
| champion | ETS Explicit | found | PASS | smoke test |
| scope | 15 models | found | PASS | smoke test |
| horizons | 30/60/180 | all found | PASS | smoke test |
| no python | NO_PYTHON | NO_PYTHON | PASS | smoke test |
| no data/raw baked | NO_RAW | NO_RAW | PASS | smoke test |
| no secrets in history | none | none | PASS | smoke test |
| logs no critical error | benign | dplyr/vroom/Inter only | PASS | container logs |

## Table 4 — Mounts / security validation

| check | expected | observed | status | evidence |
|-------|----------|----------|--------|----------|
| /app/data/processed exists | yes | yes (24 csv) | PASS | docker exec |
| /app/outputs exists | yes | yes | PASS | docker exec |
| /app/data/raw in container | absent | raw_exists=no | PASS | docker exec |
| write to processed | blocked | Read-only file system | PASS | docker exec touch |
| write to outputs | blocked | Read-only file system | PASS | docker exec touch |
| host leak (processed) | none | False | PASS | Test-Path host |
| host leak (outputs) | none | False | PASS | Test-Path host |
| dashboard after write | 200 | 200 | PASS | Invoke-WebRequest |
| no .env / secrets / credentials | none | none | PASS | compose config |
| no Azure env vars | none | none | PASS | compose config |
| relative paths only | yes | no absolute paths in source | PASS | docker-compose.yml |

## Table 5 — Riesgos / blockers

| risk_id | area | risk | severity | blocker_yes_no | mitigation | status |
|---------|------|------|----------|----------------|-----------|--------|
| R1 | port_collision | 8080 may be busy on another machine | low | no | switch to 8081:3838, documented | open_documented |
| R2 | path_portability | relative mounts resolve vs compose dir | low | no | run compose from V5 folder | mitigated |
| R3 | image_dependency | image must exist or build on clean machine | low | no | build: context . included | mitigated |
| R4 | highcharts_license | Highcharts commercial license (inherited R6) | medium | no | legal review flagged; unchanged | carried_forward |
| R5 | runtime_font_download | bslib downloads Inter font (inherited R8) | low | no | offline bundle future | carried_forward |
| R6 | restart_policy | unless-stopped keeps container up | low | no | `docker compose down` to stop | accepted |
| R7 | pdf_docx_validation | full export validation (inherited R9) | low | no | gated to V5.4 | carried_forward |
| R8 | refresh_headless_mfa | refresh MFA/headless (inherited) | medium | no | refresh deferred to V5.5/V5.6 | carried_forward |

**Blockers: NONE.**

## Table 6 — Estado global V5

| stage | status | notes | next_step |
|-------|--------|-------|-----------|
| V5.0A | V5_0A_BASELINE_CLONE_COMPLETED | clone from V4 | done |
| V5.0B | V5_0B_DOCKER_READINESS_REPRODUCIBILITY_COMPLETED | audit + decisions | done |
| V5.1 | V5_1_DOCKERFILE_DASHBOARD_IMAGE_COMPLETED | R-only image built | done |
| V5.2 | V5_2_DOCKER_COMPOSE_SHINY_SERVICE_COMPLETED | compose shiny service | **current** |
| V5.3 | pending | external volumes / artifact mounts | needs authorization |
| V5.4 | pending | dockerized downloads validation | gated |
| V5.5 | pending | refresh service dry-run/validate | gated |
| V5.6 | deferred | controlled refresh in container | MFA/headless gate |
| V5.7 | pending | docker runbook / internal docs | pending |
| V5.8 | pending | final docker closure | pending |

---

**Do NOT advance to V5.3 without explicit Oscar authorization.**

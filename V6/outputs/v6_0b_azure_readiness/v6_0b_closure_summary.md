# AEGIS V6.0B — Closure Summary

**Stage:** V6.0B — Azure Readiness + Architecture Decisions (Track A)
**Status:** `V6_0B_AZURE_READINESS_DECISIONS_COMPLETED`
**Date:** 2026-07-03
**Nature:** DECISIONS ONLY — no Azure resources, no deployment, no SQL, no refresh,
no mutation. No blockers (one prerequisite open for V6.1: Azure permissions).

---

## Tabla 1 — Artifacts creados/modificados

| artifact | path | created_or_modified | purpose | status |
|----------|------|---------------------|---------|--------|
| v6_0b_architecture_decision.md | V6/outputs/v6_0b_azure_readiness/ | created | ADR maestro | PASS |
| v6_0b_azure_target_options.csv | " | created | opciones de hosting | PASS |
| v6_0b_auth_strategy_options.md | " | created | estrategia de auth | PASS |
| v6_0b_storage_strategy.md | " | created | storage / artifact sourcing | PASS |
| v6_0b_registry_strategy.md | " | created | ACR | PASS |
| v6_0b_identity_rbac_keyvault_plan.md | " | created | identidad/RBAC/KV (V6.1) | PASS |
| v6_0b_networking_requirements.md | " | created | networking | PASS |
| v6_0b_cost_risk_assessment.csv | " | created | costo cualitativo | PASS |
| v6_0b_security_risk_register.csv | " | created | 12 riesgos | PASS |
| v6_0b_permissions_checklist.md | " | created | permisos Azure | PASS |
| v6_0b_track_gate_plan.md | " | created | tracks + gate duro | PASS |
| v6_0b_governance_invariants_check.csv | " | created | invariantes | PASS |
| v6_0b_validation.csv | " | created | DoD 24 checks | PASS |
| v6_0b_closure_summary.md | " | created | este archivo | PASS |
| VERSION_INFO.md | V6/ | modified | current_status=V6.0B, next=V6.1 | PASS |
| shiny_app / data / outputs | V6/ | UNCHANGED | sin mutación | PASS |

## Tabla 2 — Azure target options

| option | fit_for_dashboard | fit_for_refresh_job | complexity | cost_risk | recommendation | rationale |
|--------|-------------------|---------------------|------------|-----------|----------------|-----------|
| Azure Container Apps | high | high | medium | low-medium | **PREFERRED** | dashboard app + refresh Job + MI + internal ingress + KV + logs, cleanest split |
| App Service for Containers | high | low | low | low-medium | alt (dashboard only) | easy dashboard, not natural for jobs |
| ACI + external scheduler | medium | medium | medium | low | fallback | simple containers, more glue for ingress/identity/scheduler |
| AKS | high | high | high | medium-high | rejected | too heavy for this MVP |

## Tabla 3 — Auth strategy options

| strategy | headless_ready | secrets_required | scheduler_ready | sql_fit | recommendation | notes |
|----------|----------------|------------------|-----------------|---------|----------------|-------|
| Managed Identity | Yes | No | Yes | Yes | **PRIMARY** | no secrets; ACR/KV/Storage/(B)SQL |
| Service Principal | Yes | Yes (KV) | Yes | Yes | fallback | secret/cert only in Key Vault |
| Device Code | No | No | No | Yes | tests only | interactive one-off |
| Manual local refresh | n/a | No | No | Yes | operational fallback | proven V3/V4 |
| ADInteractive + MFA | No | No | No | Yes | **DISCARDED** | headless-incompatible (V5.6 blocker) |

## Tabla 4 — Storage / registry / networking decision

| area | decision | rationale | applies_to | status |
|------|----------|-----------|-----------|--------|
| storage (Track A) | Azure Files read-only mount | closest analog to V5 mounts; no app change | V6.3 | DECIDED |
| storage (Track B) | Blob: staging/productive/backups | separated governed layout produced by refresh | V6.6 | DECIDED |
| data/raw | never shared/mounted | producer-only; not a dashboard dependency | all | DECIDED |
| registry | ACR, versioned tags + digest pinning | reproducible, private | V6.2 | DECIDED |
| registry pull | Managed Identity (AcrPull) | no registry secrets | V6.2 | DECIDED |
| images | separate dashboard (R-only) + refresh (py-slim) | no contamination | all | DECIDED |
| networking (A) | internal/private ingress, Entra-gated | no public exposure; mitigates Highcharts | V6.3 | DECIDED |
| networking (B) | Private Link/VNet to SQL | private SQL path | V6.5 | DECIDED |

## Tabla 5 — Permissions checklist

| permission_area | required_for | needed_in_stage | available_now | blocker | notes |
|-----------------|--------------|-----------------|---------------|---------|-------|
| Create ACR | image registry | V6.2 | TBD | yes_for_v6_1 | confirm before creating |
| Create ACA env+app | hosting | V6.3 | TBD | yes_for_v6_1 | confirm |
| Create Managed Identity | auth | V6.1 | TBD | yes_for_v6_1 | confirm |
| Create Key Vault | secrets/config | V6.1 | TBD | yes_for_v6_1 | confirm |
| Create Storage + Azure Files | artifacts | V6.3 | TBD | yes_for_v6_1 | confirm |
| Assign RBAC (UAA/Owner) | role assignment | V6.1 | TBD | yes_for_v6_1 | needs elevated rights |
| Internal ingress config | private endpoint | V6.3 | TBD | no | policy dependent |
| VNet/Private Link | SQL private path | V6.5 (B) | TBD | no (Track B) | gated |
| SQL DB Reader | refresh source | V6.5 (B) | TBD | no (Track B) | gated |
| Log Analytics | observability | V6.9 (B) | TBD | no | later |

## Tabla 6 — Risks / blockers

| risk_id | area | risk | severity | blocker | mitigation | status |
|---------|------|------|----------|---------|-----------|--------|
| R1 | azure_permissions | cannot create resources without confirmed perms | high | yes_for_v6_1 | confirm checklist before V6.1 | open_for_v6_1 |
| R2 | auth_headless | real refresh needs non-interactive auth | high | no | MI primary; SPN fallback; gated | gated_open |
| R3 | sql_private_networking | SQL needs private connectivity | medium | no | Track B only | gated_open |
| R4 | highcharts_license | Highcharts commercial license | medium | no | private endpoint + legal | carried_forward |
| R5 | inter_font_egress | Inter font runtime download | low | no | offline bundle / allow-list | carried_forward |
| R6 | secrets_management | accidental secret leak | medium | no | KV only; MI zero-secret; scans | mitigated |
| R7 | public_exposure | accidental public endpoint | medium | no | internal ingress default | mitigated |
| R8 | cost_growth | logs/storage cost | low | no | retention limits; scale-to-zero | accepted |
| R9 | rbac_assignment_rights | lack UAA/Owner to assign roles | medium | yes_for_v6_1 | in permissions checklist | open_for_v6_1 |
| R10 | artifact_drift | cloud artifacts diverge | medium | no | Azure Files RO same governed set | mitigated |
| R11 | track_b_scope_creep | SQL/refresh before gate | high | no | explicit hard gate | mitigated |
| R12 | repo_relocation | V6 moved | low | no | cloud uses ACR/Files not local | mitigated |

**Blockers for V6.0B closure: NONE.** (R1/R9 are prerequisites to be confirmed
before V6.1, not blockers of this audit stage.)

## Tabla 7 — Governance invariants

| invariant | expected | observed_or_decision | status |
|-----------|----------|----------------------|--------|
| champion_frozen | ETS Explicit | kept frozen; no promote in Track A | PASS |
| scope_15_models | 15 | unchanged | PASS |
| horizons | 30/60/180 | unchanged | PASS |
| prohibited_models_absent | NBEATS/NHITS/FastNeuralAR_MLP | absent | PASS |
| shiny_read_only | yes | read-only mounts; no SQL/models/promote | PASS |
| refresh_separated | yes | separate ACA Job (Track B) | PASS |
| no_update_button | none | none | PASS |
| data_raw_not_exposed | absent | never shared/mounted | PASS |
| no_secrets | none | KV only; MI preferred | PASS |
| llm_explains_not_decides | mock/explain | mock in Track A; azure_openai gated V6.8 | PASS |
| no_promote_without_gates | gated | staging→32 gates→promote→rollback + human | PASS |
| no_azure_created / no_sql / no_mutation (V6.0B) | none | confirmed | PASS |
| v1_v5_intact | frozen | only V6 docs | PASS |

## Tabla 8 — Estado global V6

| stage | status | notes | next_step |
|-------|--------|-------|-----------|
| V6.0A | V6_0A_BASELINE_CLONE_COMPLETED | clone + parity + smoke | done |
| V6.0B | V6_0B_AZURE_READINESS_DECISIONS_COMPLETED | hosting=ACA, auth=MI, storage=Azure Files/Blob, ACR, internal ingress | **current** |
| V6.1 | pending | Identity/RBAC/Key Vault (needs perms + authorization) | needs authorization |
| V6.2–V6.4 | pending | ACR/push → deploy → cloud downloads (Track A) | needs authorization |
| GATE V6.4→V6.5 | pending | hard gate review | needs authorization |
| V6.5–V6.10 | pending/gated | Track B | gated |

---

**Do NOT advance to V6.1 without explicit Oscar authorization** (and confirmed
Azure permissions).

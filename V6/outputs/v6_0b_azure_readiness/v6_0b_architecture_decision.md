# AEGIS V6.0B — Architecture Decision Record (audit + decisions only)

**Stage:** V6.0B — Azure Readiness + Architecture Decisions (Track A)
**Status target:** `V6_0B_AZURE_READINESS_DECISIONS_COMPLETED`
**Date:** 2026-07-03
**Nature:** DECISIONS ONLY. No Azure resources created, no deployment, no SQL, no
refresh, no mutation. This record is the reference for V6.1–V6.10.

## 1. Hosting decision — Azure Container Apps (ACA)
**DECISION:** target **Azure Container Apps** (confirm against permissions/cost in
V6.1). ACA cleanly separates the **dashboard container** (long-running app,
internal ingress) from the **refresh Job** (one-shot/scheduled), with built-in
**managed identity**, Key Vault references, env config, Log Analytics and
internal-only ingress. App Service for Containers is the dashboard-only
alternative; ACI+external scheduler is the fallback; AKS is rejected (too heavy
for this MVP). See `v6_0b_azure_target_options.csv`.

## 2. Track A deployment architecture (read-only consumer)
```
Azure Container Apps Environment (internal / VNet)
  └── app: aegis-dashboard  (image from ACR, internal ingress :3838 -> HTTPS)
         mounts (read-only):
           /app/data/processed   <- Azure Files share (RO)
           /app/outputs          <- Azure Files share (RO)
         NOT mounted: data/raw   (never)
         identity: user-assigned Managed Identity (ACR pull, Key Vault, Storage)
```
- Dashboard stays **R-only, read-only**; no SQL from Shiny; no Python required in
  the dashboard image; **no "Update data" button**; no `data/raw`; no secrets.
- Endpoint = **internal/private by default** (Entra-gated). No public exposure.

## 3. Auth strategy
**DECISION:** **Managed Identity primary** → Service Principal fallback (secret/cert
**only in Key Vault**) → device-code (tests only) → manual local refresh
(operational fallback). `ActiveDirectoryInteractive + MFA` **discarded** for
headless. Track A (dashboard) needs identity only for **ACR pull + Storage(Files)
+ Key Vault**; **no SQL identity** in Track A. See `v6_0b_auth_strategy_options.md`.

## 4. Artifact sourcing / storage
**DECISION:** V6.3 = **Azure Files share mounted read-only** (closest analog to the
V5 bind-mount pattern — minimal change). Track B introduces **Blob Storage** for a
separated **staging / productive / backups** layout produced by the refresh Job.
Baked-in-image artifacts kept only as a demo/fallback. See `v6_0b_storage_strategy.md`.

## 5. Registry
**DECISION:** **Azure Container Registry (ACR)**, images pushed with **versioned
tags + digest pinning**, **pull via managed identity** (AcrPull), keeping
`aegis-dashboard` and (future) `aegis-refresh` as **separate images**. See
`v6_0b_registry_strategy.md`.

## 6. Identity / RBAC / Key Vault (V6.1 plan)
User-assigned Managed Identity with **least-privilege** roles: AcrPull, Key Vault
Secrets User, Storage File Data SMB Share Reader (Track A). **SQL DB reader only
in Track B**, never Track A. See `v6_0b_identity_rbac_keyvault_plan.md`.

## 7. Networking
Internal/private ingress for the dashboard; VNet integration if required; **Private
Link to SQL only in Track B**; no public exposure by default. See
`v6_0b_networking_requirements.md`.

## 8–9. Highcharts license + cost
Highcharts (via highcharter) commercial license = carried-forward risk; mitigated
in Track A by **private/internal endpoint** + legal review before any public
exposure. Cost = qualitative low/medium (see `v6_0b_cost_risk_assessment.csv`).

## 10. Track B gating (hard gate V6.4→V6.5)
Before the gate: **no real SQL, no productive auth, no real refresh, no scheduler,
no Azure OpenAI, no controlled promote.** See `v6_0b_track_gate_plan.md`.

## 11. Permissions (prerequisite)
Azure permissions to create ACA/ACR/Key Vault/Managed Identity/Storage(Azure
Files)/Log Analytics (+ VNet/Private Link and RBAC assignment for Track B) must be
confirmed before V6.1 creates anything. See `v6_0b_permissions_checklist.md`.

## 12. Governance preservation
The proposed architecture preserves every invariant (champion ETS Explicit frozen,
15 models, 30/60/180, prohibited models absent, Shiny read-only, refresh separated,
no update button, data/raw not exposed, no secrets in repo/image, LLM
explains-not-decides, no promote without gates). See
`v6_0b_governance_invariants_check.csv`.

## What V6.0B did NOT do
No Azure resources, no ACR/Key Vault/Managed Identity, no SQL/`SELECT 1`/pyodbc,
no refresh, no models, no promote, no mutation of data/processed, no data/raw, no
secrets, no changes to V1–V5.

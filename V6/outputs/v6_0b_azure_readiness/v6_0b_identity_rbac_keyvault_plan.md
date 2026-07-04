# AEGIS V6.0B — Identity / RBAC / Key Vault Plan (for V6.1)

> Plan only. Nothing is created in V6.0B. Least-privilege throughout.

## Identity
- **User-assigned Managed Identity** (single, attached to the ACA app and, later,
  the refresh Job). Preferred over system-assigned so it can be reused across
  app + job and pre-assigned roles.
- Service Principal only as documented fallback (secret/cert in Key Vault).

## RBAC (least privilege)

| Role | Scope | Needed by | Track | Justification |
|------|-------|-----------|-------|---------------|
| AcrPull | ACR | dashboard app (+ refresh job) | A | pull images by identity, no registry secrets |
| Key Vault Secrets User | Key Vault | app / job | A | read config refs (no secrets in repo/image) |
| Storage File Data SMB Share Reader | Azure Files share | dashboard app | A | read-only artifact mount |
| Storage Blob Data Contributor | Blob (staging/backups) | refresh job | **B** | write staging/backups (gated) |
| Storage Blob Data Reader | Blob (productive) | dashboard app | **B** | read promoted artifacts (if Blob used) |
| SQL DB Reader (or minimum) | Azure SQL | refresh job | **B** | read source for ingestion (gated) |

- **Track A uses NO SQL role.** SQL access is added **only in Track B**, after the
  hard gate.
- RBAC assignment itself requires **User Access Administrator / Owner** on the
  target scope (see permissions checklist).

## Key Vault
- Holds only what is strictly needed (e.g., Service Principal secret **if** the MI
  fallback is used; any non-identity config that must not live in the image).
- **No secrets in repo / image / compose.** App reads via Key Vault references
  resolved by the Managed Identity at runtime.
- If Managed Identity fully covers auth, Key Vault may hold **zero** credentials
  (preferred outcome).

## Deliverable for V6.1
A concrete `az` / Bicep plan (not executed) that: creates the MI, assigns the
Track A roles (AcrPull, KV Secrets User, Files Reader), creates the Key Vault, and
validates the identity can pull + read — **without SQL**.

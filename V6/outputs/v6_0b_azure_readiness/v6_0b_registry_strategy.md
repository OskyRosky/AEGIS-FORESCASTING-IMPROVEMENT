# AEGIS V6.0B — Registry Strategy

## Decision: Azure Container Registry (ACR)

| Item | Decision | Rationale |
|------|----------|-----------|
| Registry | **Azure Container Registry (ACR)** | Private, integrates with Managed Identity (AcrPull), same tenant. |
| Images | **separate** `aegis-dashboard` and (future) `aegis-refresh` | Dashboard stays R-only; refresh is Python-slim. Never merge. |
| Tags | **versioned tags** (e.g. `aegis-dashboard:v6.3`) | Traceable, reproducible; avoid `latest` for deploys. |
| Pinning | **digest pinning** for deploys | Immutable, reproducible rollout. |
| Pull auth | **Managed Identity (AcrPull)** | No registry credentials/secrets in the app or compose. |
| Build source | the **unmodified** V5.1/V5.4 Dockerfile (dashboard) + V5.5 Dockerfile.refresh | No functional image change in Track A; only tag/registry. |

## Push flow (planned for V6.2, not executed here)
1. `az acr login` (or MI) → push `aegis-dashboard:<v6 tag>` (+ digest recorded).
2. Optionally push `aegis-refresh:<v6 tag>` (Track B prep).
3. Validate **pull by identity** (AcrPull) from ACA.

## Governance
- No secrets baked into images; no `data/raw`; no productive artifacts baked
  (they come from Azure Files / Blob).
- Dashboard image remains **R-only** (no Python contamination).

# AEGIS V6.0B — Auth Strategy Options

**Decision:** Managed Identity **primary**; Service Principal **fallback** (secrets
only in Key Vault); Device Code **tests only**; Manual local refresh
**operational fallback**. `ActiveDirectoryInteractive + MFA` **discarded** for
headless containers.

## Options evaluated

| Strategy | Headless-ready | Secrets required | Scheduler-ready | SQL fit | Recommendation | Notes |
|----------|----------------|------------------|-----------------|---------|----------------|-------|
| Managed Identity | Yes | No | Yes | Yes (Azure SQL supports MI) | **PRIMARY** | No secrets to store/rotate; works for ACR pull, Key Vault, Storage, and (Track B) SQL. Requires the workload to run in Azure. |
| Service Principal | Yes | Yes (client secret/cert) | Yes | Yes | fallback (authorized) | Only if MI cannot cover a pattern. Secret/cert **must** live in Key Vault, never in repo/image/compose. Rotation required. |
| Device Code | No (interactive) | No | No | Yes (interactive) | tests only | Good for a one-off human-driven connectivity test; not for recurring/headless operation. |
| Manual local refresh | n/a (human) | No | No | Yes (via VPN+Entra locally) | operational fallback | Already proven in V3/V4; used if cloud auth is not approved. Produces artifacts locally that are then published. |
| ActiveDirectoryInteractive + MFA | **No** | No | No | Yes (interactive) | **DISCARDED** | Pops browser/MFA; incompatible with headless container. This was the V5.6 blocker. |

## Track-specific use
- **Track A (dashboard, V6.1–V6.4):** identity needs **ACR pull + Storage(Files) +
  Key Vault** only. **No SQL identity.**
- **Track B (refresh, V6.5+):** adds **SQL DB reader** (or the minimum needed) via
  the same Managed Identity, only after the hard gate.

## Decision to confirm in V6.1
Whether Azure SQL + the tenant policy allow **Managed Identity** for the refresh
workload. If not, escalate to **Service Principal in Key Vault** (documented).

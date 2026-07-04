# AEGIS V6.0B — Networking Requirements

## Principles
- **Internal / private by default.** The dashboard must NOT be publicly exposed
  unless explicitly authorized (also mitigates the Highcharts license risk).
- Access gated by **Entra** (internal users only).
- **Private Link to SQL only in Track B** (never Track A).

## Track A (dashboard) — requirements
| Requirement | Decision | Notes |
|-------------|----------|-------|
| Ingress | **internal** ACA ingress (not external) | HTTPS; reachable inside the corp network only |
| Public exposure | **none by default** | requires explicit authorization + legal (Highcharts) |
| VNet integration | as required by internal ingress policy | ACA environment can be VNet-injected |
| Access control | Entra-gated | internal users |
| Egress | minimal | first render fetches Inter font (R8) — consider offline bundle or allow-list |
| SQL access | **none** | dashboard never connects to SQL |

## Track B (refresh) — requirements (design only, gated)
| Requirement | Decision | Notes |
|-------------|----------|-------|
| SQL connectivity | **Private Link / VNet integration / VPN** | private path to Azure SQL |
| Firewall / allowed networks | restrict to the refresh workload subnet | no broad public access |
| Auth | Managed Identity (or SPN fallback) | non-interactive only |
| Test | minimal authorized `SELECT 1` **only if authorized** at V6.5 | handshake/connectivity proof, no data query |

## Carried-forward
- **Highcharts license (R6):** private/internal endpoint in V6.3 + legal review
  before any public exposure.
- **Inter font runtime download (R8):** consider bundling offline for restricted
  egress environments.

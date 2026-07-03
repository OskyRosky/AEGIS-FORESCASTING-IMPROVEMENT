# AEGIS V5.2 — Compose Up Report

**Command:** `docker compose up -d shiny`
**Container:** `aegis-dashboard-v5-2`
**Image:** `aegis-dashboard:v5.1` (id `ed86271fff04`)

## Result

| Item | Observed | Status |
|------|----------|--------|
| Network | `v5_default` created | OK |
| Container | `aegis-dashboard-v5-2` created + started | RUNNING |
| Health | `healthy` (after `starting`) | PASS |
| External port | `0.0.0.0:8080->3838/tcp` | PASS |
| Internal port | `Listening on http://0.0.0.0:3838` | PASS |
| HTTP | `200`, LEN `303385` (= V5.1 baseline) | PASS |
| Rebuild | image reused; no build step in `up` | PASS |

## Container logs (benign only)

- `dplyr` masking messages (base/stats) — expected package attach noise.
- `vroom` / `readr` parsing warning — pre-existing, benign (carried from V3+).
- `Downloading google font Inter to local cache` — known risk **R8/R5**
  (bslib fetches the Inter font at first render; requires network on first run;
  dashboard renders correctly). No offline bundling in V5.2 scope.

No critical errors. No SQL, no model runs, no refresh, no Azure, no real LLM.

## Logs captured

- `logs/v5_2_compose_up.log`
- `logs/v5_2_compose_container_logs.log`
- `logs/v5_2_compose_config.log`

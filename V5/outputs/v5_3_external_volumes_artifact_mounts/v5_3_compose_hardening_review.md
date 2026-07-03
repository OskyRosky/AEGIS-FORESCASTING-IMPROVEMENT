# AEGIS V5.3 — Compose Hardening Review

**Decision: No functional changes required to `docker-compose.yml`.**

The V5.2 Compose file already satisfies the V5.3 volume/artifact contract:
single `shiny` service, `data/processed` + `outputs` mounted **read-only**,
`data/raw` not mounted, no secrets/.env, relative paths, fixed container name,
inherited healthcheck, `restart: unless-stopped`.

## Options considered and rejected (with rationale)

| Option | Decision | Rationale |
|--------|----------|-----------|
| `read_only: true` on the container root filesystem | **Rejected** | The dashboard writes to `/tmp` (rmarkdown/report tempfiles) and `/root/.cache/R/sass` (bslib downloads the Inter font at first render). A read-only root fs would break rendering. The **governance requirement is RO on the artifact mounts**, which is already enforced. |
| `tmpfs: /tmp` | **Not required** | `/tmp` is already writable inside the container; no evidence of a leak or need. Adding tmpfs is optional and would only matter if root fs were made read-only (rejected above). |
| Add `labels` | **Not required** | Cosmetic; no operational benefit for a single local-demo service. |
| Add explicit `container_name` | **Already present** | `aegis-dashboard-v5-2`. |
| Add `refresh` service | **Forbidden** | Out of scope; deferred to V5.5/V5.6. |
| Add secrets / `.env` | **Forbidden** | Governance: no secrets. |
| Mount `data/raw` | **Forbidden** | Governance: raw not mounted. |

## Outcome

`docker-compose.yml` is **unchanged** in V5.3 (git: untracked new file from V5.2,
no modification). Therefore no `docker compose config` re-validation, no service
restart, and no diff were required. V5.2 Compose integrity is preserved.

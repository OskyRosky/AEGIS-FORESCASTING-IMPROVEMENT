# AEGIS V6.0B — Storage / Artifact Sourcing Strategy

## Decision
- **Track A (V6.3):** governed artifacts served from an **Azure Files share
  mounted read-only** into the dashboard container. This is the closest analog to
  the V5 bind-mount pattern (`data/processed` + `outputs` read-only), so the app
  needs **no code change** — it keeps consuming `/app/data/processed` and
  `/app/outputs` as read-only mounts.
- **Track B (V6.5+):** introduce **Blob Storage** with a separated layout for the
  real refresh, produced by the refresh Job (never by the dashboard).

## Track A — Azure Files (read-only)
| Item | Decision |
|------|----------|
| Share content | `data/processed` + `outputs` (governed artifacts only) |
| Mount mode | **read-only** into `/app/data/processed` and `/app/outputs` |
| data/raw | **NOT** shared, **NOT** mounted |
| Secrets | none on the share |
| Write path | app writes only to container `/tmp` (downloads), never to the share |
| Identity | Managed Identity with Storage File Data SMB Share **Reader** |

## Track B — Blob Storage (refresh, gated)
Separated containers/paths (design only; not created in V6.0B):
| Layer | Purpose | Access |
|-------|---------|--------|
| `staging/` | candidate artifacts from a refresh run (pre-gates) | refresh job read/write |
| `productive/` | promoted governed artifacts consumed by the dashboard | dashboard read-only; promote writes |
| `backups/` | pre-promote backups for rollback | refresh job read/write |
- Controlled promote (staging → productive) stays governed: **32 gates + backup +
  rollback**, champion frozen, **no Shiny mutation**, human approval.

## Fallback / demo
Artifacts **baked into the image** remain a demo/fallback option (fully offline)
but are NOT the default (breaks the "no rebuild to update artifacts" contract).

## Governance
- `data/raw` never leaves the producer side; never mounted/exposed.
- Dashboard remains a **read-only consumer**; only the refresh Job (Track B) writes
  to productive storage, and only through the governed promote path.

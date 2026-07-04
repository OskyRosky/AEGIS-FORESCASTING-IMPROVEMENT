# AEGIS V6.0B — Track / Gate Plan

## Two tracks split by a HARD GATE

```
TRACK A — Consumidor read-only (SAFE, no SQL)
  V6.0A Clone ✓ → V6.0B Readiness (this) → V6.1 Identity/RBAC/KeyVault
  → V6.2 ACR/push → V6.3 Dashboard deploy → V6.4 Cloud downloads
        ══════════ GATE DURO V6.4→V6.5 (review + explicit authorization) ══════════
TRACK B — Productor real (SENSIBLE)
  V6.5 Private SQL connectivity → V6.6 Real refresh governed → V6.7 Scheduler
  → V6.8 Azure OpenAI (optional) → V6.9 Observability → V6.10 Final closure
```

## What is FORBIDDEN before the hard gate (V6.4→V6.5)
- ❌ No real SQL / no SQL connection / no `SELECT 1` / no pyodbc.
- ❌ No productive/non-interactive auth exercised against SQL.
- ❌ No real refresh / no full pipeline.
- ❌ No scheduler.
- ❌ No Azure OpenAI real.
- ❌ No controlled promote / no champion change.

## The hard gate (V6.4→V6.5) — `V6_4_TO_V6_5_HARD_GATE_REVIEW_COMPLETED`
A formal review + **explicit authorization** deciding whether to cross into
Track B. Reviews: permissions, security, cost, networking, Managed Identity
readiness, risks. If not authorized, **V6 can close at Track A** as a
cloud read-only demo (analogous to V5 closing without V5.6).

## Track B stays governed
When (and only when) authorized: real refresh must follow
**staging → 32 gates → controlled promote → rollback**, champion frozen, **no
Shiny mutation**, human approval. Scheduler only after V6.6 is validated. Azure
OpenAI optional and isolated (V6.8).

## Closure options for V6
- **Minimum viable close:** Track A complete (V6.0A–V6.4) + V6.9 hardening →
  cloud read-only demo.
- **Full close:** Track B complete through V6.10.

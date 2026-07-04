# AEGIS V5.3 — No-Rebuild External Reflection Test

**Goal:** prove that a controlled external change to a mounted artifact appears
inside the running container **without any image rebuild**.

## Method (validation-only probe, not productive data)

Probe files live under `outputs/v5_3_external_mount_probe/` — clearly namespaced
V5.3 validation evidence, **not** part of the governed artifact set and **not** in
the loader registry. `data/processed`, `data/raw` and governed artifacts were
**not** modified.

## Steps & results

1. Captured `image_id_before` = `ed86271fff04`.
2. Created on host: `outputs/v5_3_external_mount_probe/host_probe.txt` (Version 1).
3. Read inside container (no rebuild, no restart):
   `docker exec aegis-dashboard-v5-2 cat /app/outputs/v5_3_external_mount_probe/host_probe.txt`
   → **"... Version 1."** ✅ visible.
4. Updated the same file on host to **Version 2**.
5. Re-read inside container → **"... Version 2 (reflection confirmed)."** ✅
   new content visible **without rebuild and without restart**.
6. Captured `image_id_after` = `ed86271fff04` → **unchanged**.
7. No `docker build`, no `docker compose build` executed.
8. Dashboard after probe: **HTTP 200**, LEN 303385.

## Conclusion

| Property | Result |
|----------|--------|
| External change visible in container | YES |
| Update visible without rebuild | YES |
| Update visible without restart | YES |
| Image ID before == after | YES (`ed86271fff04`) |
| Any docker/compose build run | NO |
| Dashboard still HTTP 200 | YES |

Artifacts can be replaced on the host and the running container serves them
immediately. **Rebuilds are only for code/dependency changes, never for data.**

Evidence retained: `outputs/v5_3_external_mount_probe/host_probe.txt` (final =
Version 2), `logs/v5_3_no_rebuild_reflection_test.log`.

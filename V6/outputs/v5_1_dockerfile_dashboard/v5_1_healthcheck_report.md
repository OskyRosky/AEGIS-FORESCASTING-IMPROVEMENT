# V5.1 — HEALTHCHECK (Task)

## Configuración
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3838/ >/dev/null || exit 1
```

## Racional
- Sonda HTTP contra el **puerto interno fijo 3838** (no el externo 8080).
- `--start-period=45s`: la app Shiny + carga del loader gobernado tardan unos segundos en el primer arranque.
- `curl` instalado vía apt expresamente para esto (y para httr).

## Resultado observado
- `docker ps` → `Up (healthy)` a los ~20 s del arranque.
- `docker inspect .State.Health.Status` → `healthy`.
- Smoke-test `container_health` → **PASS**.

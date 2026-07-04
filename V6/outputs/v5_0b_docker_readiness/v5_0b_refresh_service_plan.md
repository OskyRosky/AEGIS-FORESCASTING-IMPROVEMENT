# V5.0B — Plan del servicio de refresh (propuesta, NO operativo, GATED)

## Decisión
- **Imagen separada** `aegis-refresh` (no se mezcla con el dashboard R-only).
- **Diferida a V5.5**; **refresh real gated a V5.6**.

## Composición propuesta (V5.5)
- Base: `python:3.x-slim` (Debian).
- Deps: `pandas`, `pyodbc`, `python-dotenv` (de `requirements.txt`) + `msodbcsql18` + `unixodbc`.
- Código: solo `python/ingestion`, `python/transform`, `python/orchestration` (no `model_lab` pesado).
- Config de conexión vía **env/secret en runtime**, nunca baked.

## Bloqueador crítico (R2)
`ingestion/config.py` usa `Authentication=ActiveDirectoryInteractive` → abre **navegador + MFA**. Un contenedor **headless no puede** completar MFA interactivo.
→ Para refresh real (V5.6) se requiere **rediseño de auth**: device-code flow, service principal, o managed identity. Hasta entonces:
- **V5.5:** solo **dry-run / validate** (construir connection string, validar imports, validar esquema de salida) **sin** conectar realmente ni mutar datos.
- **V5.6:** estado `CONTROLLED_REFRESH_DEFERRED_GATED` — requiere autorización explícita de Oscar y decisión de modelo de auth no interactivo.

## Invariante
El refresh **no** cambia el campeón (ETS Explicit FROZEN) ni la gobernanza; solo materializa datos. Cualquier ejecución real queda gated.

> Solo plan. No se construye imagen ni se ejecuta refresh en V5.0B.

# V5.1 — .dockerignore agresivo (Task D)

## Contexto antes / después
| Métrica | Valor |
|---|---|
| Árbol V5 completo | **1414.3 MB** |
| Contexto retenido tras .dockerignore | **0.95 MB** |
| Factor de reducción | **~1488x** |
| Realmente transferido al builder | 1.63 kB / 4.43 kB (logs `transferring context`) |

## Qué se excluye (heavy/innecesario)
- `outputs/` (1255 MB) y `data/` (155 MB) → **mounts externos read-only**, NO horneados.
- `data/raw/` → nunca horneado.
- `python/`, `MassiveForecasting-V3/`, `BACKUP/`, `notebooks/`, `docs/`, `tests/`, `scripts/`.
- Cachés Python: `.venv`, `__pycache__`, `*.pyc`, `.ipynb_checkpoints`.
- VCS/IDE/estado local: `.git/`, `.vscode/`, `*.Rproj`, `.Rproj.user/`, `.Rhistory`, `.RData`.
- Logs/runtime/temp/cachés: `**/logs/`, `**/*.log`, `**/runtime/`, `**/tmp/`, `**/*.cache`, `**/transcripts/`.
- Ruido de SO: `.DS_Store`, `Thumbs.db`.

## Qué se conserva (necesario para el build)
- `shiny_app/` (incluye `R/`, `ui/`, `server/`, `modules/`, `www/`) — código del dashboard.
- `config/` — configuración (sin secretos).
- `ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md` — marcadores de raíz.
- `docker/entrypoint.sh` — entrypoint.
- (No se excluye renv.lock; en esta etapa no se creó.)

## Nota de diseño
`data/processed` queda **fuera del build** (recomendación V5.0B) y se provee como **volumen read-only** en runtime. No se horneó snapshot demo: los datos gobernados se montan, manteniendo la imagen pequeña y read-only.

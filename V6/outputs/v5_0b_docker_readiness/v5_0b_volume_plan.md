# V5.0B — Plan de volúmenes (propuesta, NO operativo)

**Hallazgo de escritura (Task J):** `shiny_app/` solo escribe a destinos de descarga (`downloadHandler`) y `tempfile()`/`tempdir()`. **No muta `data/processed`** (el `file.copy` copia el CSV canónico al destino temporal de descarga). → Datos montables **read-only**.

## Decisión
- **Datos gobernados = montaje read-only.** El dashboard lee artefactos desde `outputs/` (p.ej. `outputs/model_lab`) y `data/processed/` vía el loader gobernado y el resolver relativo (`find_project_root` busca `outputs/model_lab` + `shiny_app`).
- **No baked por defecto:** la imagen contiene solo código; los datos llegan por volumen → imagen reproducible y desacoplada del dataset.
- **`/tmp` escribible:** el contenedor necesita un tmp escribible (descargas, render rmarkdown). Usar tmpfs o el filesystem efímero del contenedor (no volumen persistente).
- **Snapshot embebido (opcional):** solo si se requiere demo 100% offline sin volumen; entonces copiar una subcarpeta **curada** de artefactos gobernados (read-only en runtime). Justificación obligatoria por escrito en V5.3.

## Montajes propuestos (V5.3, a validar)
| Host (V5) | Contenedor | Modo |
|---|---|---|
| `outputs/` (curado a artefactos gobernados) | `/app/outputs` | ro |
| `data/processed/` | `/app/data/processed` | ro |
| (efímero) | `/tmp` | rw (tmpfs) |

## Pendiente para V5.3
- Construir el **manifiesto de artefactos** que el loader realmente abre, para curar el montaje RO (riesgo R5).
- Confirmar que con datos RO + `/tmp` rw el export de artefactos (CSV/MD/TXT/HTML/PDF) funciona.

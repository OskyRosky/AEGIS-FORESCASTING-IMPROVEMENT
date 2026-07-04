# V5.1 — Build report (Task H)

## Comando
```
docker build -t aegis-dashboard:v5.1 -f Dockerfile .
```
(primer build con `--no-cache`; rebuild posterior tras agregar `libuv1`.)

## Resultado
- **Build EXIT: 0** (PASS) en ambos builds.
- Gate de paquetes R: `ALL_R_PKGS_OK`.
- TinyTeX: `TINYTEX_INSTALLED`.
- Tag creado: `aegis-dashboard:v5.1`.

## Tamaño e capas
| Métrica | Valor |
|---|---|
| Tamaño (docker image inspect .Size) | **526.2 MB** |
| Tamaño (docker images) | 2.1 GB (incluye manifiesto de attestation/provenance de BuildKit) |
| Capas (RootFS) | 19 |

> Nota: el valor "2.1 GB" de `docker images` refleja el manifest list de BuildKit con attestation; el tamaño funcional de la imagen single-platform es **~526 MB**.

## Contexto de build
- Árbol V5: 1414.3 MB → contexto retenido 0.95 MB → transferido ~1.63–4.43 kB.
- Confirmado: **NO** se incluyó `data/raw`, **NO** outputs pesados, **NO** Python.

## Logs
- `logs/v5_1_docker_build.log` — salida completa del build.

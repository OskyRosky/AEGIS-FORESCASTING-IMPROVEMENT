# V5.1 — Verificación de imagen base (Task B)

## Decisión final
**Base image:** `rocker/r-ver:4.6.0` **pinneada por digest**.

```
FROM rocker/r-ver:4.6.0@sha256:a3c049a16b67a01f893c106a1c8e7c878f739a541bda1fa01e42c3507aa232e9
```

## Evidencia de verificación
| Tag candidato | Disponibilidad | Digest |
|---|---|---|
| rocker/r-ver:4.6.0 | **AVAILABLE** | sha256:a3c049a16b67a01f893c106a1c8e7c878f739a541bda1fa01e42c3507aa232e9 |
| rocker/r-ver:4.5.1 | AVAILABLE (fallback) | sha256:55be3ae296dd21b6f2da705be44804ba7eb2ab2233a7050730506d7e64e8feda |
| rocker/r-ver:4.5.0 | AVAILABLE (fallback) | sha256:5e8963d73b87865e0ad779df4202555fb1b436ee95dc7d7442450308b8ea77f3 |
| rocker/r-ver:4.4.2 | AVAILABLE (fallback) | sha256:585ece96943ec010a870f9c569bb441ba262c5f93cb6d2c669f8ddd50db59d16 |
| rocker/r-ver:latest | AVAILABLE | sha256:671316c5a258728933e1becd48aa9b20f78b037b43db0b0f66b2ba789e16ae93 |

Comando: `docker manifest inspect <tag>` (no se inventó ningún digest).

## Características de la base verificadas (en runtime)
- **OS:** Ubuntu 24.04.4 LTS (noble)
- **R:** 4.6.0 (2026-04-24) "Because it was There"
- **Repo R por defecto:** `https://p3m.dev/cran/__linux__/noble/2026-06-23` (Posit P3M, **snapshot fechado**, paquetes **binarios** para noble)
- **pandoc:** NO presente en la base → se instala vía apt

## Resolución de riesgo
- **Riesgo R1 (V5.0B: disponibilidad de tag 4.6.0, severidad alta):** **RESUELTO** — el tag existe y se pinnea por digest.
- No se requirió fallback. Los fallbacks quedan documentados arriba por si el digest cambiara en el futuro.

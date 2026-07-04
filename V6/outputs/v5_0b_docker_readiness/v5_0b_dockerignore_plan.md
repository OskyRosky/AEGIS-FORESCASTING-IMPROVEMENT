# V5.0B — Plan de .dockerignore (propuesta, NO operativo)

Contexto total = 1414 MB; `outputs/` (1255 MB) + `data/` (155 MB) dominan. Sin `.dockerignore` el build sería lento y la imagen pesada. **Propuesta** de `.dockerignore` (a crear en V5.1, no ahora):

```
# Datos y artefactos (se montan read-only, no van en la imagen)
outputs/**
data/raw/**
data/processed/**          # montado RO en runtime
data/sample/**

# Histórico / legacy / docs
BACKUP/**
MassiveForecasting-V3/**
docs/**
notebooks/**
tests/**

# Control de versiones y temporales
.git/**
**/.venv/**
**/__pycache__/**
*.log
*.pdf
*.rds

# Python (excluido de la imagen del DASHBOARD; va solo en la imagen de refresh)
python/**
```

Notas:
- Si en V5.3 se decide **embeber un snapshot offline** de los artefactos gobernados para demo, se exceptúa una subcarpeta curada (`!outputs/<curated_governed>/**`) en vez de `data/processed`.
- La imagen de refresh tendrá su **propio** `.dockerignore` que SÍ incluye `python/` y excluye `shiny_app/`.
- Resultado esperado: contexto de build del dashboard ≈ 3 MB (código) + capas de paquetes R.

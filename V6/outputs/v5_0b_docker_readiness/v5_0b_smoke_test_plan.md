# V5.0B — Plan de smoke-test del contenedor (propuesta, NO operativo)

Reutiliza la lógica de validación de V5.0A pero contra el contenedor. **Propuesta** de script reutilizable (a crear en V5.2, no ahora): `scripts/docker_smoke_test.ps1` (y/o `.py`).

## Checks propuestos (paridad con V5.0A)
1. **HTTP 200** en `http://127.0.0.1:<host_port>/` tras `start-period`.
2. **Tamaño de payload** razonable (HTML de la home no vacío; baseline V5.0A LEN ≈ 303501).
3. **Marcadores de gobernanza presentes** en el HTML:
   - `ETS Explicit` (campeón FROZEN) presente.
   - `15 governed models` / `15 models`.
   - Horizontes `30/60/180 days`.
   - Botón `Generate explanation` (capa LLM mock).
4. **Tabs de navegación** presentes (todas las secciones).
5. **Logs del contenedor sin errores críticos** (`docker logs`).
6. **Exit/health = healthy** vía `docker inspect --format '{{.State.Health.Status}}'`.

## Forma de uso (propuesta)
```
# Pseudo: docker run -d -p 8080:3838 ... ; esperar healthy ; correr smoke ; reportar tabla
scripts\docker_smoke_test.ps1 -Url http://127.0.0.1:8080 -ExpectChampion "ETS Explicit"
```

Salida: una tabla check/expected/observed/status + código de salida ≠0 si falla algún check de gobernanza.

> Solo propuesta. No se crea el script operativo en V5.0B.

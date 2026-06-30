# V5.0B — Decisión: Locale + fuentes

**Decisión:** `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`; instalar `locales`, `fontconfig`, `fonts-dejavu-core`, `fonts-liberation`.

**Rechazadas:**
- Dejar locale por defecto (POSIX/C sin UTF-8) — rompe acentos del español (Costa Rica, métricas, textos del dashboard y explicaciones LLM).
- `en_US.UTF-8` — válido, pero `C.UTF-8` evita generar locale específico y es suficiente para UTF-8.

**Rationale:** El contenido es en español con acentos; UTF-8 es obligatorio para CSV, render HTML/PDF y texto del LLM. Las fuentes DejaVu/Liberation garantizan glifos en export PDF/DOCX vía TeX/pandoc. fontconfig resuelve fuentes en render.

**Impacto en V5.1:**
- `ENV LANG=C.UTF-8 LC_ALL=C.UTF-8`.
- `apt-get install -y locales fontconfig fonts-dejavu-core fonts-liberation` + `locale-gen C.UTF-8` (si aplica al base).

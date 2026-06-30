# V5.0B — Decisión: TeX + pandoc (export de artefactos)

**Decisión:** Incluir **pandoc** (paquete del sistema) + **TinyTeX** (instalado vía R `tinytex::install_tinytex()`) en la imagen del dashboard.

**Rechazadas:**
- `texlive-full` — varios GB; desproporcionado para los pocos artefactos PDF.
- `texlive-base`/`texlive-latex-recommended` solos — riesgo de paquetes LaTeX faltantes en render; gestión manual.
- Diferir PDF a V5.4 — posible, pero la app ya ofrece export PDF; mantenerlo evita regresión funcional.

**Rationale:** TinyTeX es la opción que **ya usa el host** (paridad), es ligera y `tinytex` resuelve paquetes LaTeX bajo demanda. pandoc es requerido por `rmarkdown` para HTML/DOCX.

**Impacto en V5.1/V5.4:**
- Capa Docker: `apt-get install -y pandoc` + `R -e "tinytex::install_tinytex()"`.
- Cachear la capa de TinyTeX para no reinstalar en cada build.
- Validar en V5.4 que el export PDF de un artefacto gobernado renderiza dentro del contenedor.

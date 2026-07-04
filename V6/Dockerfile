# =====================================================================
# AEGIS V5.1 | Dockerfile | Dashboard Image (R-only, dashboard-first)
# ---------------------------------------------------------------------
# Governance (V5.0A / V5.0B sources of truth):
#   - R-only image. NO Python. NO torch/darts/lightgbm/xgboost/sklearn.
#   - NO SQL, NO models, NO refresh, NO Azure, NO real LLM.
#   - Image = dashboard code + R runtime dependencies ONLY.
#   - data/processed and outputs are EXTERNAL read-only mounts.
#   - NO data/raw, NO secrets, NO heavy outputs baked into the image.
#   - Internal port fixed = 3838 (no port-hunting). Healthcheck on 3838.
#
# Base image (verified V5.1 Task B):
#   rocker/r-ver:4.6.0  ->  Ubuntu 24.04 (noble), R 4.6.0 (2026-04-24)
#   Pinned by digest. The base already pins a Posit P3M dated snapshot
#   (https://p3m.dev/cran/__linux__/noble/2026-06-23) serving Linux
#   BINARY packages -> reproducible R pinning per the V5.0B decision.
# =====================================================================
FROM rocker/r-ver:4.6.0@sha256:a3c049a16b67a01f893c106a1c8e7c878f739a541bda1fa01e42c3507aa232e9

# --- Locale (UTF-8, deterministic) -----------------------------------
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# --- System dependencies ---------------------------------------------
# curl        -> HEALTHCHECK probe + httr runtime
# pandoc      -> rmarkdown / DOCX / HTML / MD rendering (PDF via TinyTeX)
# lib*-dev    -> shared libs for httr/curl, xml2, fonts, image/text shaping
# fonts-*     -> UTF-8 / accented glyph rendering for plots and reports
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        pandoc \
        locales \
        libcurl4-openssl-dev \
        libssl-dev \
        libxml2-dev \
        libuv1 \
        libfontconfig1-dev \
        libfreetype6-dev \
        libpng-dev \
        libjpeg-dev \
        libtiff5-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        fonts-dejavu-core \
        fonts-liberation \
        wget \
        perl \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# --- R packages (dashboard-only, pinned via base P3M dated snapshot) --
# Dependencies (scales, stringr, lubridate, etc.) are resolved
# automatically by install.packages. Binary packages -> no compilation.
RUN R -q -e "install.packages(c(\
        'shiny','bslib','DT','plotly','highcharter',\
        'dplyr','readr','tidyr','htmltools','jsonlite',\
        'rmarkdown','tinytex','httr','pandoc'\
      ), Ncpus = max(1L, parallel::detectCores()))"

# Build-time gate: fail the build if any required dashboard package is missing.
RUN R -q -e "pkgs <- c('shiny','bslib','DT','plotly','highcharter','dplyr','readr','tidyr','htmltools','jsonlite','rmarkdown','tinytex','httr','pandoc'); miss <- pkgs[!pkgs %in% rownames(installed.packages())]; if (length(miss)) stop('MISSING_R_PACKAGES: ', paste(miss, collapse=', ')) else cat('ALL_R_PKGS_OK\n')"

# --- TinyTeX (LaTeX engine for PDF export) — V5.4: reliable + FATAL ---
# V5.0B decision: TeX = pandoc + TinyTeX. In V5.1 this step was non-fatal and
# did not persist (no pdflatex on PATH), so PDF export was gated to V5.4.
# V5.4 makes it deterministic: install TinyTeX, symlink its binaries onto PATH
# (tlmgr path add -> /usr/local/bin), pre-install the LaTeX packages pandoc's
# default template + Markdown tables need (so runtime PDF is OFFLINE, no CTAN
# fetch at run time), and FAIL the build if pdflatex is absent or a real
# pandoc Markdown->PDF conversion (with a table + a UTF-8 accent) does not
# produce a %PDF. Needs wget + perl + xz-utils (added to apt above).
ENV PATH=/root/.TinyTeX/bin/x86_64-linux:$PATH
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh \
    && /root/.TinyTeX/bin/*/tlmgr path add \
    && R -q -e "tinytex::tlmgr_install(c('iftex','lm','amsmath','booktabs','etoolbox','xcolor','geometry','hyperref','bookmark','xurl','ulem','upquote','microtype','parskip','footnotehyper','mdwtools','fancyvrb','framed'))" \
    && R -q -e "if (!nzchar(Sys.which('pdflatex'))) stop('NO_PDFLATEX_ON_PATH') else cat('PDFLATEX_OK:', Sys.which('pdflatex'), '\n')" \
    && printf '# AEGIS PDF build check\n\nETS Explicit champion.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n' > /tmp/_pdfcheck.md \
    && R -q -e "rmarkdown::pandoc_convert(input=normalizePath('/tmp/_pdfcheck.md'), to='latex', output='/tmp/_pdfcheck.tex', options='--standalone'); tinytex::latexmk('/tmp/_pdfcheck.tex'); if (!file.exists('/tmp/_pdfcheck.pdf') || file.info('/tmp/_pdfcheck.pdf')\$size < 500) stop('PDF_BUILD_VERIFY_FAILED') else cat('PDF_BUILD_VERIFY_OK\n')" \
    && rm -f /tmp/_pdfcheck.md /tmp/_pdfcheck.tex /tmp/_pdfcheck.pdf

# --- Application code (R-only; NO Python, NO data/raw, NO secrets) -----
WORKDIR /app
COPY shiny_app/ /app/shiny_app/
COPY config/ /app/config/
COPY ACTIVE_PROJECT_ROOT.md /app/ACTIVE_PROJECT_ROOT.md
COPY VERSION_INFO.md /app/VERSION_INFO.md

# Mount points for EXTERNAL read-only volumes (data/processed + outputs).
# Created empty so the container is well-formed even before mounts; the
# governed dashboard data is supplied at runtime via -v ...:ro mounts.
RUN mkdir -p /app/outputs /app/data/processed

# --- Entrypoint ------------------------------------------------------
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
# Normalize potential CRLF (Windows host) so the shebang parses on Linux.
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh

# Internal port fixed = 3838 (no port-hunting).
EXPOSE 3838

# Healthcheck: HTTP probe against the fixed internal Shiny port.
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3838/ >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

#!/usr/bin/env bash
# =====================================================================
# AEGIS V5.1 | docker/entrypoint.sh | Dashboard container entrypoint
# ---------------------------------------------------------------------
# Simple, deterministic launcher. NO port-hunting, NO PowerShell,
# NO robocopy, NO SQL, NO refresh, NO models. Fixed internal port 3838.
# runApp() sets the working directory to the app dir, so the app's
# relative source() calls and the governed read-only data loader resolve
# correctly (project root = /app when outputs/ + data/processed are
# mounted as external read-only volumes).
# =====================================================================
set -euo pipefail

exec Rscript -e "shiny::runApp('/app/shiny_app', host = '0.0.0.0', port = 3838)"

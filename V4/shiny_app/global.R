# TESSERACT v2 | global.R | governed shared startup sources
source("R/libraries.R")
source("R/constants.R")
source("R/helpers.R")
source("R/ttl_provider.R")   # Phase 0 | TTL data-provider seam (mock | api)
source("R/llm_client.R")

# Block 7.0E | governed, read-only data loader (no recompute, never stops app)
source("R/data_loader.R")
tess_init_governed_loader()

# V4.6 | Shiny Local On-Demand LLM explanation panel (mock, read-only)
source("R/llm_explain.R")

# V4.6R2 | Local deterministic composition engine (generates answers from
# the governed evidence by question intent; no real LLM, no Azure).
source("R/llm_compose.R")

# V4.7 | Make a locally-installed pandoc / TinyTeX discoverable so the
# explanation download modal can export PDF / Word. No network, no Azure;
# purely points rmarkdown at the local binaries. Safe no-op if absent.
try(.llm_ensure_pandoc(), silent = TRUE)

# TESSERACT v2 | global.R | governed shared startup sources
source("R/libraries.R")
source("R/constants.R")
source("R/helpers.R")
source("R/ttl_provider.R")   # Phase 0 | TTL data-provider seam (mock | api)
source("R/llm_client.R")

# Block 7.0E | governed, read-only data loader (no recompute, never stops app)
source("R/data_loader.R")
tess_init_governed_loader()

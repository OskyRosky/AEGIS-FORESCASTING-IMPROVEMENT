# V5.3 runtime artifact presence probe (read-only). Runs inside the container.
# Prints pipe-separated presence rows to stdout (captured on host).
setwd('/app/shiny_app')
source('R/data_loader.R')
reg <- build_artifact_registry()
root <- '/app'
for (i in seq_len(nrow(reg))) {
  p  <- file.path(root, reg$rel_path[i])
  ex <- file.exists(p)
  sz <- if (ex) as.numeric(file.info(p)$size) else 0
  cat(paste('ROW', reg$artifact_key[i], reg$category[i], reg$requirement[i],
            reg$rel_path[i], ex, sz, sep = '|'), '\n', sep = '')
}
lp <- 'outputs/v4_4_mock_provider/v4_4_mock_responses.json'
cat(paste('ROW', 'LLM_JSON', 'llm', 'required', lp,
          file.exists(file.path(root, lp)),
          if (file.exists(file.path(root, lp))) as.numeric(file.info(file.path(root, lp))$size) else 0,
          sep = '|'), '\n', sep = '')

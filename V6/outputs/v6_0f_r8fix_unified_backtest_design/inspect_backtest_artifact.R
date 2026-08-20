suppressMessages(library(data.table))
p <- "V6/data/processed/forecast_viewer_model_outputs.csv"
d <- fread(p, showProgress = FALSE)

cat("rows:", nrow(d), " cols:", ncol(d), "\n")
cat("columns:\n"); print(names(d))
cat("\n--- cardinalities ---\n")
for (c in names(d)) {
  u <- unique(d[[c]])
  cat(sprintf("%-28s n_unique=%6d  class=%-10s sample: %s\n", c, length(u),
              class(d[[c]])[1], paste(utils::head(u, 4), collapse = " | ")))
}
cat("\n--- models ---\n")
mcol <- grep("model", names(d), value = TRUE, ignore.case = TRUE)
for (m in mcol) { cat(m, ":\n"); print(sort(unique(d[[m]]))) }
cat("\n--- horizon ---\n")
hcol <- grep("horizon", names(d), value = TRUE, ignore.case = TRUE)
for (h in hcol) print(sort(unique(d[[h]])))
cat("\n--- rows per series x model x horizon (sample) ---\n")
gcols <- intersect(c("entity_key", "series", "key", "model_name", "horizon"), names(d))
cat("grouping by:", paste(gcols, collapse = " + "), "\n")
print(head(d[, .N, by = gcols][order(-N)], 5))
cat("\n--- date range ---\n")
dcol <- grep("date|time", names(d), value = TRUE, ignore.case = TRUE)
for (x in dcol) cat(sprintf("%-16s %s .. %s\n", x, min(d[[x]], na.rm = TRUE),
                            max(d[[x]], na.rm = TRUE)))
cat("\n--- first 2 rows ---\n"); print(head(d, 2))

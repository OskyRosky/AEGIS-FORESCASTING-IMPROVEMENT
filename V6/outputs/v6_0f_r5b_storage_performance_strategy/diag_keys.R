suppressMessages(library(data.table))
d <- fread("V6/outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_viewer_hdd.csv",
           showProgress = FALSE)

for (m in c("HDD - Basilisk", "HDD - EDB")) {
  s <- d[metric == m & granularity == "Forest"]
  cs <- sum(grepl("NAMPRD07", s$key))
  ci <- sum(grepl("NAMPRD07", s$key, ignore.case = TRUE))
  cat(sprintf("%-16s rows=%7d  case-sensitive=%5d  case-insensitive=%5d\n", m, nrow(s), cs, ci))
  cat("   matching keys: ",
      paste(unique(s$key[grepl("NAMPRD07", s$key, ignore.case = TRUE)]), collapse = " | "), "\n")
}

b <- d[metric == "HDD - Basilisk" & granularity == "Forest"]
cat("\nsample Basilisk keys:\n")
print(head(sort(unique(b$key)), 8))
cat("\nBasilisk model types:", paste(unique(b$model_type), collapse = " | "), "\n")

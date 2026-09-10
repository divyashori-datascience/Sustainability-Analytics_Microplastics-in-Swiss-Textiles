# =============================================================================
# 02_aggregate_by_year.R
#
# Aggregates the filtered textile/apparel import file (output of
# 01_filter_textile_imports.R) into yearly totals, and applies the
# Textile Exchange global synthetic-fiber share to estimate the
# synthetic-fiber portion of Swiss imports per year.
#
# Input:  data/processed/textile_apparel_imports.csv
# Output: data/processed/textile_imports_by_year.csv
#
# Requires: install.packages(c("readr", "dplyr"))
# =============================================================================

library(readr)
library(dplyr)

INPUT_FILE  <- "data/processed/textile_apparel_imports.csv"
OUTPUT_FILE <- "data/processed/textile_imports_by_year.csv"

# Share of global fiber production that is synthetic (Textile Exchange).
# Update if the team finds a more precise/recent figure.
synthetic_share <- 0.69

data <- read_csv(INPUT_FILE, show_col_types = FALSE)

yearly <- data %>%
  group_by(year) %>%
  summarise(
    total_imported_kg = sum(Total_quantity_kg, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    estimated_synthetic_kg = total_imported_kg * synthetic_share
  ) %>%
  arrange(year)

write_csv(yearly, OUTPUT_FILE)

cat("Done. Wrote", nrow(yearly), "yearly rows ->", OUTPUT_FILE, "\n")
cat("Note: 2026 should be excluded from headline figures — partial year only.\n")

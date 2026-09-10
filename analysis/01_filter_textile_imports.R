# =============================================================================
# 01_filter_textile_imports.R
#
# Filters the large Swiss customs (BAZG/SwissImpex) import file down to
# textiles and apparel rows only.
#
# Source file is large (~1.5-1.9 GB), so this reads it in chunks rather
# than loading it all into memory at once.
#
# CPA2 codes are letter-prefixed by section (e.g. "A01" = Agriculture),
# so textiles/apparel are matched as "C13" / "C14" — not the bare
# digits "13"/"14".
#
# Usage:
#   1. Download a CPA6_IMP CSV from:
#      https://opendata.swiss/en/dataset/waren-aussenhandel-nach-cpa6-land
#   2. Place it in data/raw/ and update INPUT_FILE below if the filename differs.
#   3. Run this script from the repo root: Rscript R/01_filter_textile_imports.R
#
# Output:
#   data/processed/textile_apparel_imports.csv
#
# Requires: install.packages(c("readr", "dplyr"))
# =============================================================================

library(readr)
library(dplyr)

INPUT_FILE  <- "data/raw/CPA6_IMP.csv"
OUTPUT_FILE <- "data/processed/textile_apparel_imports.csv"
CHUNK_SIZE  <- 200000  # rows per chunk; lower if memory is tight

# CPA2-level codes for textiles (C13) and apparel (C14)
target_prefixes <- c("C13", "C14")

# --- Step 1: peek at column names / code format before filtering ---
preview <- read_delim(INPUT_FILE, delim = ";", n_max = 5, show_col_types = FALSE)
print(names(preview))
print(unique(preview$CPA2))

cpa_column <- "CPA2"

# --- Step 2: read and filter in chunks, writing matches as we go ---
first_chunk <- TRUE
total_rows_kept <- 0

filter_chunk <- function(chunk, pos) {
  matches <- chunk %>%
    filter(.data[[cpa_column]] %in% target_prefixes)

  if (nrow(matches) > 0) {
    write_csv(matches, OUTPUT_FILE, append = !first_chunk)
    first_chunk <<- FALSE
    total_rows_kept <<- total_rows_kept + nrow(matches)
  }
}

read_delim_chunked(
  INPUT_FILE,
  delim = ";",
  callback = SideEffectChunkCallback$new(filter_chunk),
  chunk_size = CHUNK_SIZE,
  col_types = cols(.default = "c"),  # read everything as text, safest for filtering
  show_col_types = FALSE
)

cat("Done. Kept", total_rows_kept, "rows ->", OUTPUT_FILE, "\n")

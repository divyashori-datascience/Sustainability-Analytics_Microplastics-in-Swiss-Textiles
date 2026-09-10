# =============================================================================
# 04_sensitivity_analysis.R
#
# One-at-a-time sensitivity (tornado) analysis on the bottom-up pollution
# formula:
#
#   microplastic reaching environment (t/yr) =
#       synthetic_imports_kg * washes_per_kg_per_yr * shedding_rate_g_per_kg_per_wash
#       * (1 - wwtp_capture_rate) / 1e6
#
# Each parameter is varied across its literature-sourced range while the
# others are held at baseline, and the resulting swing in the output is
# used to rank parameter influence (a standard tornado-chart approach).
#
# NOTE: parameter ranges below are literature mid-points/bounds as used in
# the team's original analysis (synthetic_wardrobe.Rmd). Re-check against
# that script's Section 10 values before citing exact figures in slides —
# this script reproduces the *method* and *ranking*, not a replacement
# source of truth for the final numbers.
#
# Output: data/processed/sensitivity_results.csv, printed ranking, and a
#         simple tornado plot.
# =============================================================================

library(dplyr)

# --- Baseline inputs -------------------------------------------------------

synthetic_imports_kg <- 190e6   # latest full-year estimated synthetic import mass (kg)

params <- list(
  wwtp_capture_rate = list(baseline = 0.90,  low = 0.75,  high = 0.95,
                            source = "Conley et al.; Kaegi et al."),
  washes_per_kg_yr   = list(baseline = 25,    low = 15,    high = 52,
                            source = "Internal laundry-behaviour estimate (unsourced for Swiss context)"),
  shedding_rate_g_kg = list(baseline = 0.02,  low = 0.01,  high = 0.04,
                            source = "De Falco et al. (2021)"),
  synthetic_share    = list(baseline = 0.69,  low = 0.55,  high = 0.80,
                            source = "Textile Exchange")
)

# --- Model function ----------------------------------------------------

run_model <- function(wwtp_capture_rate, washes_per_kg_yr, shedding_rate_g_kg, synthetic_share) {
  synth_kg <- synthetic_imports_kg * synthetic_share
  grams_shed <- synth_kg * washes_per_kg_yr * shedding_rate_g_kg
  tonnes_to_environment <- grams_shed * (1 - wwtp_capture_rate) / 1e6
  tonnes_to_environment
}

baseline_output <- run_model(
  params$wwtp_capture_rate$baseline,
  params$washes_per_kg_yr$baseline,
  params$shedding_rate_g_kg$baseline,
  params$synthetic_share$baseline
)

# --- One-at-a-time sensitivity sweep ---------------------------------------

sweep_param <- function(name) {
  p <- params[[name]]
  baseline_args <- lapply(params, function(x) x$baseline)

  low_args <- baseline_args
  low_args[[name]] <- p$low
  low_output <- do.call(run_model, low_args)

  high_args <- baseline_args
  high_args[[name]] <- p$high
  high_output <- do.call(run_model, high_args)

  data.frame(
    parameter = name,
    source = p$source,
    low_value = p$low,
    high_value = p$high,
    output_at_low = low_output,
    output_at_high = high_output,
    swing = abs(high_output - low_output)
  )
}

results <- bind_rows(lapply(names(params), sweep_param)) %>%
  arrange(desc(swing))

cat("Baseline output:", round(baseline_output, 2), "t/yr\n\n")
cat("Parameter ranking by influence (largest swing first):\n")
print(results %>% select(parameter, swing))

dir.create("data/processed", showWarnings = FALSE, recursive = TRUE)
write.csv(results, "data/processed/sensitivity_results.csv", row.names = FALSE)

# --- Simple tornado plot -----------------------------------------------

results_ord <- results %>% arrange(swing)
par(mar = c(5, 12, 4, 2))
barplot(
  results_ord$swing,
  names.arg = results_ord$parameter,
  horiz = TRUE, las = 1,
  col = "#3F7D4E",
  xlab = "Swing in output (t/yr)",
  main = "Sensitivity (Tornado) Analysis"
)

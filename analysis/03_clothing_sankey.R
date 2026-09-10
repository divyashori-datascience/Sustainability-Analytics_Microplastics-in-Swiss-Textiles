# =============================================================================
# 03_clothing_sankey.R
#
# Draws the clothing -> wastewater -> environment pathway diagram (PET only)
# using the digitized Empa dataset (Kawecki & Nowack, 2019).
#
# Input:  data/raw/Plastics-by-Type_EMPA.csv (or the pre-extracted
#         data/processed/PET_clothing_sankey_data.csv)
# Output: interactive HTML widget rendered in the R viewer / RStudio
#
# Requires: install.packages("networkD3")
# =============================================================================

library(networkD3)

# --- Step 1: pathway stages, using the real digitized Empa PET numbers ---
# (values = tonnes/year, PET clothing pathway)
links <- data.frame(
  source = c("Clothing",         "Clothing",           "Clothing",
             "Waste water (MP)", "WWTP (MP)",          "Primary WWT (MP)",
             "Sludge (MP)",      "Outdoor air (MP)",   "Outdoor air (MP)"),
  target = c("Waste water (MP)", "Outdoor air (MP)",   "Indoor air (MP)",
             "WWTP (MP)",        "Primary WWT (MP)",   "Sludge (MP)",
             "Incineration",     "Natural soil (MP)",  "Surface water (MP)"),
  value  = c(0.0499,             0.0101,               0.0324,
             0.0610,             0.0595,               0.0560,
             0.0599,             0.0164,               0.0015)
)

# --- Step 2: build the node list networkD3 needs ---
nodes <- data.frame(
  name = unique(c(as.character(links$source), as.character(links$target)))
)
links$IDsource <- match(links$source, nodes$name) - 1
links$IDtarget <- match(links$target, nodes$name) - 1

# --- Step 3: draw it ---
sankeyNetwork(
  Links = links, Nodes = nodes,
  Source = "IDsource", Target = "IDtarget",
  Value = "value", NodeID = "name",
  fontSize = 14, nodeWidth = 25,
  sinksRight = FALSE
)

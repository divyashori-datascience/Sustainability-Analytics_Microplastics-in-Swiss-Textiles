# The Synthetic Wardrobe
### Microplastic Pollution from Synthetic Textiles in Switzerland

HSLU Sustainability Analytics — block-week group project (Prof. Salomon)

## Research questions
1. What share of Swiss plastic pollution comes from synthetic clothing?
2. How much of that could be avoided through fiber choice and extended garment lifespan?

## Team
| Member | Focus |
|---|---|
| Hanieh Jebeli | Intro/storyline, data sourcing, structural model |
| Divya Shori   | Agentic AI Assessment — RAG chatbot for brand sustainability verification (GOTS, OEKO-TEX, RCS, Fair Trade) |
| Rana          |  

## Repository structure
```
.
├── R/                  Data pipeline, diagram, and sensitivity analysis (Hanieh's section)
│   ├── 01_filter_textile_imports.R
│   ├── 02_aggregate_by_year.R
│   ├── 03_clothing_sankey.R
│   └── 04_sensitivity_analysis.R
├── data/
│   ├── raw/             Source datasets (SwissImpex, Empa)
│   └── processed/       Pipeline outputs used by the model and slides
├── python/              Agentic AI Assessment (Hanieh, Divya) — RAG-style brand verification tool
├── time-series/         Time-series analysis (Divya)
├── figures/             Diagrams and exported charts
├── reports/             Deck notes / methodology write-ups
└── README.md
```

## Data pipeline (R)
Source: SwissImpex / BAZG customs data (opendata.swiss)

1. `01_filter_textile_imports.R` — streams the large CPA6 import file in chunks and keeps only textile (`CPA2 = C13`) and apparel (`CPA2 = C14`) rows → `data/processed/textile_apparel_imports.csv`
2. `02_aggregate_by_year.R` — aggregates to yearly totals and applies the Textile Exchange synthetic-fiber share (69%) → `data/processed/textile_imports_by_year.csv`
3. `03_clothing_sankey.R` — draws the clothing → wastewater → environment pathway diagram from the digitized Empa (Kawecki & Nowack, 2019) dataset
4. `04_sensitivity_analysis.R` — tornado/sensitivity analysis on the bottom-up pollution formula

## Headline figures
- **Bottom-up estimate:** ~95–98 t/yr (synthetic imports × washes/yr × shedding rate × (1 − WWTP capture rate)). *Not used as the headline slide figure* — the washing-frequency input (25 washes/kg/yr) lacks a real Swiss data source.
- **Headline figure used on slides:** Empa's validated top-down estimate of **4.6 t/yr** (PET+PP only, reproducing the source paper's 4.8 t figure), presented as a conservative lower bound.
- **Most influential parameter (sensitivity analysis):** WWTP capture rate.

## Key sources
- SwissImpex / BAZG customs data — opendata.swiss
- Kawecki & Nowack (2019) — Empa material-flow model
- De Falco et al. (2021) — fiber shedding rates
- Conley et al.; Kaegi et al. — WWTP capture rates
- Resortecs, *From Waste to Profit* (2023) — Design for Disassembly

## Setup
**R** (pipeline, diagrams, sensitivity analysis)
```r
install.packages(c("readr", "dplyr", "networkD3"))
```

**Python** (Agentic AI Assessment)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r python/requirements.txt
```

# ai-spain-hvac

HVAC (and solar) propensity modelling for Homeserve Spain.

## Setup

```bash
poetry install
poetry run jupyter lab
```

## Data sources

Three complementary sources, each answering a different question about a census tract (sección censal). See **[DATA_SOURCES.md](DATA_SOURCES.md)** for the full overview.

### 1. INE ADRH — income atlas (annual, 2015–2023)

Tract-level income, poverty thresholds, inequality (Gini, P80/P20), and income source mix. Fused from AEAT tax records, Social Security, and Padrón. Latest vintage: **2023**. Stored on S3.

**[INE_ADRH_DATA_DOCUMENTATION.md](INE_ADRH_DATA_DOCUMENTATION.md)**

### 2. INE Census 2021 — raw indicator file

Tract-level housing tenure, household size, age structure, employment and education indicators. Decennial snapshot — **2021**, next 2031. t-code column names require dictionary (`indicadores_seccen_c2021.xlsx`).

**[INE_CENSUS_2021_DOCUMENTATION.md](INE_CENSUS_2021_DOCUMENTATION.md)**

### 3. ineAtlas (pablogguz) — processed Census 2021

Third-party reprocessing of Source 2 with English column names. Single CSV covering all 36,333 tracts. The working version used in the pipeline.

**[INEATLAS_DOCUMENTATION.md](INEATLAS_DOCUMENTATION.md)**

## Generated data

Parquet files produced from the three sources — inventory, S3 upload map, full INE t-code mapping, and customer join guide.

**[GENERATED_DATA.md](GENERATED_DATA.md)**

## Joining with customer data

How to link a HomeServe customer record to census tract features via address geocoding and spatial join. Includes fallback options (postal code → municipio), GeoPandas implementation sketch, and GDPR note.

**[CUSTOMER_DATA_JOIN.md](CUSTOMER_DATA_JOIN.md)**

## EDA findings

Regional heatmap analysis, Basque Country NaN root cause, and cross-validation against INE Census 2021 Nota de Prensa.

**[EDA_REGIONAL_FINDINGS.md](EDA_REGIONAL_FINDINGS.md)**

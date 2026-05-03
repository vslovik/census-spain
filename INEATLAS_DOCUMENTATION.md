# ineAtlas (pablogguz) — Census 2021 Tract-Level Data Documentation

**Dataset:** Spanish Population and Housing Census 2021 — sección censal indicators (English-named repackaging)
**Original source:** Instituto Nacional de Estadística (INE), Censo de Población y Viviendas 2021
**Processed by:** Pablo Guggenbühl — [`pablogguz/ineAtlas.data`](https://github.com/pablogguz/ineAtlas.data)
**Package docs:** [`pablogguz.github.io/ineAtlas.data`](https://pablogguz.github.io/ineAtlas.data/)
**Local file:** `data/input/ineatlas/census_2021_tract.csv` (8.4 MB, downloaded November 2024)
**S3:** `s3://hsf-group-ai-spain-hvac/ineatlas/raw/census_2021_tract.csv`
**Raw INE source:** See `INE_CENSUS_2021_DOCUMENTATION.md`
**EDA notebook:** [`eda_ineatlas.ipynb`](eda_ineatlas.ipynb)

---

## What this dataset is

The Spanish Census (*Censo de Población y Viviendas*) is a full enumeration of the population conducted every 10 years. The 2021 edition covers reference date 1 November 2021. The **next census is expected in 2031** — this data will not be updated annually.

This is **distinct from the ADRH data** (see `INE_ADRH_DATA_DOCUMENTATION.md`):

| | Census 2021 | ADRH |
|--|-------------|------|
| Source | Population survey (INE) | Tax records (AEAT) + register |
| Frequency | Decennial (2021, next 2031) | Annual (2015–2023) |
| Coverage | Housing, demographics, education, employment | Income, poverty, inequality |
| Finest grain | Sección censal | Sección censal |
| Vintage in repo | 2021 | 2023 (latest) |

The file `census_2021_tract.csv` was produced by the `ineAtlas.data` R package, which downloads raw INE Census 2021 indicator files and re-publishes them as clean, English-named CSVs with all values expressed as ratios or counts. It is **not downloaded directly from INE** — it is a third-party curated version.

---

## File structure

**36,333 rows × 41 columns.** One row per sección censal.

### Geographic key columns

| Column | Description | Notes |
|--------|-------------|-------|
| `tract_code` | Sección censal identifier | **9-digit integer** — INE standard is 10-digit string; leading zero dropped for provinces 01–09 (e.g. `400101001` = `0400101001`). Zero-pad to 10 chars to join with ADRH data: `str(tract_code).zfill(10)` |
| `district_code` | Distrito censal | 7-digit |
| `mun_code` | Municipality code | 5-digit (prov 2 + mun 3) |
| `prov_code` | Province code | 2-digit |
| `prov_name` | Province name (Spanish) | e.g. `"Almería"` |

### Population & demographics

| Column | Description |
|--------|-------------|
| `total_pop` | Total resident population |
| `pct_female` / `pct_male` | Share female / male |
| `mean_age` | Mean age of population |
| `pct_under16` | Share aged under 16 |
| `pct_16to64` | Share aged 16–64 |
| `pct_over64` | Share aged 65+ ← key HVAC feature |
| `pct_foreign` | Share of foreign nationals |
| `pct_foreign_born` | Share born outside Spain |

### Education & labour market

| Column | Description |
|--------|-------------|
| `pct_higher_ed_enrolled` | Share enrolled in higher education |
| `pct_university_enrolled` | Share enrolled in university |
| `pct_higher_ed_completed` | Share who completed higher education |
| `unemployment_rate` | Unemployment rate |
| `employment_rate` | Employment rate ← proxy for economic activity |
| `activity_rate` | Economic activity rate |
| `pct_disability_pension` | Share receiving disability pension |
| `pct_retirement_pension` | Share receiving retirement pension ← pensioner proxy |
| `pct_other_inactive` | Share economically inactive (other) |
| `pct_student` | Share who are students |

### Civil status

| Column | Description |
|--------|-------------|
| `pct_single` | Share single |
| `pct_married` | Share married |
| `pct_widowed` | Share widowed |
| `pct_divorced_separated` | Share divorced or separated |
| `pct_marital_unknown` | Share with unknown marital status |

### Housing & dwellings

| Column | Description | HVAC relevance |
|--------|-------------|----------------|
| `total_dwellings` | Total dwellings in tract | |
| `primary_dwellings` | Main-residence dwellings | |
| `secondary_dwellings` | Secondary/vacation dwellings | Low HVAC demand |
| `owned_dwellings` | Owner-occupied dwellings | **HIGH** — ownership prerequisite for HVAC/solar install |
| `rented_dwellings` | Rented dwellings | Lower install propensity |
| `other_tenure_dwellings` | Other tenure | |

### Households

| Column | Description | HVAC relevance |
|--------|-------------|----------------|
| `total_households` | Total household count | |
| `hh_size1` | 1-person households | Single-person = smaller HVAC unit |
| `hh_size2` | 2-person households | |
| `hh_size3` | 3-person households | |
| `hh_size4` | 4-person households | |
| `hh_size5plus` | 5+ person households | Larger unit, higher capacity demand |

---

## Key HVAC-relevant features

From this dataset, the primary features for HVAC propensity modelling are:

```python
HVAC_FEATURES = [
    "owned_dwellings",        # ownership rate = install prerequisite
    "pct_over64",             # elderly = replacement demand, comfort priority
    "pct_retirement_pension", # pension income = stable but fixed budget
    "employment_rate",        # economic activity proxy
    "hh_size1",               # single-person = smaller systems
    "hh_size4", "hh_size5plus",  # family households = higher capacity
    "secondary_dwellings",    # vacation homes = seasonal demand
]
```

---

## Joining with ADRH data

The `tract_code` in this dataset is a 9-digit integer. The ADRH `cod_seccion` is a 10-digit zero-padded string. To join:

```python
import pandas as pd

census = pd.read_csv("data/input/ineatlas/census_2021_tract.csv")
adrh   = pd.read_parquet("processed_data/spain_secciones_2023_features.parquet")

# Normalise the key
census["cod_seccion"] = census["tract_code"].astype(str).str.zfill(10)

merged = census.merge(adrh, on="cod_seccion", how="inner")
print(f"Merged: {len(merged):,} tracts")
```

---

## Important caveats

1. **2021 vintage** — housing tenure, household size and population structure reflect the 2021 snapshot. Use ADRH 2023 data for current income indicators.

2. **Third-party processing** — this CSV was produced by `ineAtlas.data`, not downloaded directly from INE. If columns need verification, cross-check against the raw INE file at `data/C2021_Indicadores.csv` (also in this repo) or the original source at `https://www.ine.es/censos2021/C2021_Indicadores.csv`.

3. **9-digit tract code** — leading zero is dropped for provinces 01–09. Always zero-pad to 10 characters before joining with any INE-sourced dataset.

4. **Ratios, not counts** — all `pct_*` columns are proportions in [0, 1], not percentages. Multiply by 100 for display.

---

## Notebook

`eda_census.ipynb` — full exploratory analysis of this dataset. Covers:
- Data quality and geographic completeness (52 provinces, 8,131 municipalities, 36,333 tracts)
- Age structure distribution across tracts
- Household size mix and correlation with senior share
- Owner-occupation vs age
- Province and CCAA-level heatmaps (age / employment / retirement pension)
- Mean annual temperature by province and region (from Open-Meteo reference values, hardcoded)

Temperature data in the notebook is **not from INE** — it uses province-level reference climatological averages from [Open-Meteo](https://open-meteo.com/), hardcoded as a lookup table in Cell 34.

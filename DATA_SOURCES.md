# Data Sources — Overview

This project uses three independent data sources to build HVAC propensity features at the **sección censal** (census tract) level across Spain. They are complementary: each answers a different question about a tract.

---

## The three sources at a glance

| | INE ADRH | INE Census 2021 | ineAtlas (pablogguz) |
|--|----------|----------------|----------------------|
| **Full name** | Atlas de Distribución de Renta de los Hogares | Censo de Población y Viviendas 2021 | ineAtlas.data R package |
| **Producer** | INE (official) | INE (official) | Pablo Guggenbühl (third-party) |
| **Type** | Administrative data fusion | Decennial population survey | Processed re-publication of INE Census 2021 |
| **Covers** | Income, poverty, inequality | Housing, population, households | Same as Census 2021, with English column names |
| **Finest grain** | Sección censal | Sección censal | Sección censal |
| **Vintage** | Annual — latest **2023** | Once per decade — **2021** (next: 2031) | 2021 (follows Census vintage) |
| **Local file** | S3 only (see below) | `data/input/ine_census_2021/C2021_Indicadores.csv` + dictionaries | `data/input/ineatlas/census_2021_tract.csv` |
| **Documentation** | `INE_ADRH_DATA_DOCUMENTATION.md` | `INE_CENSUS_2021_DOCUMENTATION.md` | `INEATLAS_DOCUMENTATION.md` |

---

## Source 1 — INE ADRH (income atlas)

INE produces the ADRH annually by fusing three administrative registers:
- **AEAT** tax records — earned income, pensions, capital income
- **Social Security** — unemployment benefits, disability pensions
- **Padrón municipal** — population register, used to assign income to a geographic location

This produces tract-level indicators of **how much money households have and where it comes from**: net/gross income per person and per household, income source mix, poverty thresholds (fixed and relative), and inequality (Gini, P80/P20).

**Why it matters for HVAC:** Income is the primary affordability filter. A tract with high median household income and low poverty rate is a stronger HVAC prospect than one with low income, regardless of housing stock.

**Vintage:** Updated every autumn for the prior year. Latest available: **2023**.
**S3:** `s3://hsf-group-ai-spain-hvac/ine-adrh/raw/`
**Detail:** `INE_ADRH_DATA_DOCUMENTATION.md`

---

## Source 2 — INE Census 2021 (housing & population)

The *Censo de Población y Viviendas* is a full enumeration of every person and dwelling in Spain. Reference date: **1 November 2021**. It is conducted every ten years (previous: 2011; next: **2031**). The 2021 figures are frozen — they will not be updated until the next census.

The census captures what ADRH cannot: the **physical characteristics of the housing stock** and the **demographic composition of households**.

Key variables for HVAC:
- **Ownership vs rental** — only owners make HVAC investment decisions
- **Building age and type** — old buildings and single-family houses = highest replacement demand
- **Household size** — determines system capacity requirements
- **Age structure** — elderly share signals comfort-driven demand and replacement cycles

INE publishes the raw indicator file (`C2021_Indicadores.csv`) with cryptic t-code column names (e.g. `t1_1`, `t4_2`). A separate dictionary file (`indicadores_seccen_c2021.xlsx`) maps codes to descriptions.

**Vintage:** 2021 — static until 2031.
**S3:** `s3://hsf-group-ai-spain-hvac/ine-census-2021/`
**Detail:** `INE_CENSUS_2021_DOCUMENTATION.md`

---

## Source 3 — ineAtlas by Pablo Guggenbühl (processed Census 2021 tract file)

[`pablogguz/ineAtlas.data`](https://github.com/pablogguz/ineAtlas.data) is a third-party R package that re-processes the INE Census 2021 indicator file and republishes it as a clean, English-named CSV. It is **derived from Source 2** — same underlying data, different packaging.

We use this rather than the raw INE file because:
- Column names are human-readable English (`pct_over64`, `owned_dwellings`, `employment_rate`) instead of t-codes (`t4_3`, `t17_1`, `t11_1`)
- All values are pre-computed as proportions/counts — no further transformation needed
- A single file covers all 36,333 tracts for all of Spain

The trade-off: it is a third-party product. If columns change between package versions, or if the package is discontinued, the raw INE file (`C2021_Indicadores.csv`) is the authoritative fallback.

**Vintage:** 2021 (follows Census vintage).
**S3:** `s3://hsf-group-ai-spain-hvac/ineatlas/`
**Detail:** `INEATLAS_DOCUMENTATION.md`

---

## How the three sources relate

```
INE ADRH (annual tax data)          →  income, poverty, inequality
    └─ 2023 vintage, ~36k secciones

INE Census 2021 (decennial survey)  →  housing, households, demographics
    └─ 2021 vintage, ~36k secciones
    └─ pablogguz repackages this as English-named CSV (ineAtlas)

Join key: cod_seccion (10-digit string)
    ADRH:     cod_seccion as string, zero-padded, e.g. "0100101001"
    Census:   cod_seccion built from ccaa+cpro+cmun+dist+secc components
    ineAtlas: tract_code as 9-digit integer (leading zero dropped for prov 01–09)
              → zero-pad to join: str(tract_code).zfill(10)
```

---

## S3 bucket layout

```
s3://hsf-group-ai-spain-hvac/
├── ine-adrh/
│   └── raw/               ← 20 × .zst compressed files (CSV + JSON), ~527 MB
├── ine-census-2021/
│   ├── raw/               ← C2021_Indicadores.csv, CensoPersonas_2021.zip
│   └── dictionaries/      ← indicator dictionary, lookup tables, data dictionary
└── ineatlas/
    └── raw/               ← census_2021_tract.csv (pablogguz processed)
```

---

## Local project layout

```
data/
├── input/
│   ├── ine_census_2021/   ← raw INE Census 2021 files (mirrors S3 ine-census-2021/)
│   └── ineatlas/          ← pablogguz tract CSV (mirrors S3 ineatlas/)
│   (ine-adrh has no local copy — data volume too large, use S3)
└── generated/
    ├── adrh/              ← pipeline outputs derived from ADRH source
    └── census_2021/       ← pipeline outputs derived from Census 2021 / ineAtlas
```

See `GENERATED_DATA.md` for a full inventory of generated files and which script produced each one.

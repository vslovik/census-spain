# INE Census 2021 — Documentation

**Dataset:** Censo de Población y Viviendas 2021 — indicator file at sección censal level
**Producer:** Instituto Nacional de Estadística (INE)
**Reference date:** 1 November 2021
**Frequency:** Decennial — previous 2011, next **2031**
**S3:** `s3://hsf-group-ai-spain-hvac/ine-census-2021/`
**Processed version:** See `INEATLAS_DOCUMENTATION.md` (`pablogguz/ineAtlas.data`)

---

## What this dataset is

The *Censo de Población y Viviendas* is a full enumeration of every person and dwelling in Spain. The 2021 edition — conducted via administrative records and a short-form survey — covers **47.4 million residents** and **25.2 million dwellings** across **36,333 secciones censales**.

Unlike ADRH (which is updated annually from tax records), Census data is a **snapshot frozen at 2021**. The 2021 figures will not be refreshed until the 2031 census.

The Census answers a different question from ADRH:

| | Census 2021 | ADRH |
|--|-------------|------|
| Source | Population survey (INE) | Tax records (AEAT) + Social Security + Padrón |
| Frequency | Decennial (2021, next 2031) | Annual (2015–2023) |
| Coverage | Housing stock, demographics, education, employment | Income, poverty, inequality |
| Finest grain | Sección censal | Sección censal |
| Vintage in use | 2021 | 2023 (latest) |

---

## Files on S3

The persons microdata is **not stored as the original ZIP** — it is extracted and each relevant file is compressed individually with zstd so notebooks can stream files directly from S3 without local extraction. See `compress_and_upload_censo_personas.sh`.

```
s3://hsf-group-ai-spain-hvac/ine-census-2021/
├── raw/
│   ├── C2021_Indicadores.csv              ← tract-level aggregate indicators (7.7 MB)
│   ├── CensoPersonas_2021.tab.zst         ← person microdata CSV, zstd-compressed (~167 MB)
│   ├── md_CensoPersonas_2021.txt.zst      ← machine-readable metadata, zstd-compressed (~150 MB)
│   ├── dr_CensoPersonas_2021.xlsx.zst     ← variable dictionary, zstd-compressed
│   └── Leeme.txt.zst                      ← INE readme, zstd-compressed
└── dictionaries/
    ├── indicadores_seccen_c2021.xlsx      ← t-code → description mapping (26 KB)
    ├── indicadores_seccen_rejilla.xls     ← indicator grid layout (61 KB)
    ├── codccaa.xls                        ← CCAA codes (16 KB)
    └── codprov.xls                        ← province codes (17 KB)
```

**Local copies** are in `data/input/ine_census_2021/` — the original `CensoPersonas_2021.zip` is kept locally as the authoritative archive; individual files are only on S3.

---

## File 1 — `C2021_Indicadores.csv`

The primary aggregate file. **36,333 rows × 41 columns** — one row per sección censal.

Downloaded from: `https://www.ine.es/censos2021/C2021_Indicadores.csv`

### Geographic key columns

| Column | Description |
|--------|-------------|
| `ccaa` | Comunidad autónoma code (2 digits) |
| `cpro` | Province code (2 digits) |
| `cmun` | Municipality code within province (3 digits) |
| `dist` | Census district code (2 digits) |
| `secc` | Section code within district (3 digits) |

The full `cod_seccion` join key (10-digit string) is constructed as: `cpro + cmun + dist + secc`.

```python
df["cod_seccion"] = (
    df["cpro"].astype(str).str.zfill(2)
    + df["cmun"].astype(str).str.zfill(3)
    + df["dist"].astype(str).str.zfill(2)
    + df["secc"].astype(str).str.zfill(3)
)
```

### Indicator columns (t-codes)

All values are either **counts** (T1, T18, T21) or **proportions in [0, 1]** (all others).

| Column(s) | Table | Description | HVAC relevance |
|-----------|-------|-------------|----------------|
| `t1_1` | T1 | Total resident population | |
| `t2_1`, `t2_2` | T2 | Share female, share male | |
| `t3_1` | T3 | Mean age | |
| `t4_1`, `t4_2`, `t4_3` | T4 | Share aged <16, 16–64, 65+ | **HIGH** — elderly share |
| `t5_1` | T5 | Share with foreign nationality | |
| `t6_1` | T6 | Share born outside Spain | |
| `t7_1` | T7 | Share enrolled in higher education (16+) | |
| `t8_1` | T8 | Share enrolled in university (16+) | |
| `t9_1` | T9 | Share with completed higher education (16+) | |
| `t10_1` | T10 | Unemployment rate (unemployed / active population) | |
| `t11_1` | T11 | Employment rate (employed / pop 16+) | **proxy for economic activity** |
| `t12_1` | T12 | Activity rate (active / pop 16+) | |
| `t13_1` | T13 | Share receiving disability pension (16+) | |
| `t14_1` | T14 | Share receiving retirement pension (16+) | **pensioner proxy** |
| `t15_1` | T15 | Share in other inactivity (16+) | |
| `t16_1` | T16 | Share who are students (16+) | |
| `t17_1`–`t17_5` | T17 | Civil status: single, married, widowed, separated/divorced, unknown | |
| `t18_1` | T18 | Total dwellings (count) | |
| `t19_1`, `t19_2` | T19 | Primary dwellings, non-primary dwellings | |
| `t20_1`, `t20_2`, `t20_3` | T20 | Primary dwellings: owned, rented, other tenure | **HIGH** — owned = install prerequisite |
| `t21_1` | T21 | Total households (count) | |
| `t22_1`–`t22_5` | T22 | Households by size: 1, 2, 3, 4, 5+ persons | |

### Reading the file

```python
import pandas as pd

df = pd.read_csv(
    "data/input/ine_census_2021/C2021_Indicadores.csv",
    sep=",",
    dtype={"ccaa": str, "cpro": str, "cmun": str, "dist": str, "secc": str},
)

# Build the 10-digit join key
df["cod_seccion"] = df["cpro"].str.zfill(2) + df["cmun"].str.zfill(3) + df["dist"].str.zfill(2) + df["secc"].str.zfill(3)

print(df.shape)       # (36333, 42)
print(df["cod_seccion"].str.len().unique())   # [10]
```

> **Separator:** comma (`,`), not semicolon. The file is straightforward UTF-8 with no BOM. Values are already decimals in [0, 1] — no European number formatting to handle.

### Reading from S3

```python
import io, boto3, pandas as pd

s3 = boto3.client("s3")
obj = s3.get_object(Bucket="hsf-group-ai-spain-hvac", Key="ine-census-2021/raw/C2021_Indicadores.csv")
df = pd.read_csv(
    io.BytesIO(obj["Body"].read()),
    sep=",",
    dtype={"ccaa": str, "cpro": str, "cmun": str, "dist": str, "secc": str},
)
df["cod_seccion"] = df["cpro"].str.zfill(2) + df["cmun"].str.zfill(3) + df["dist"].str.zfill(2) + df["secc"].str.zfill(3)
```

---

## File 2 — `CensoPersonas_2021.tab` (person microdata)

**Person-level microdata** for the 2021 census — **one row per person**, covering ~4.7 million
person records. This is the maximum detail available for public download from INE.

### Critical: this is a 10% public micro-sample

INE does not publish 100% individual-level census microdata publicly. `CensoPersonas_2021.tab`
is a **10% systematic random sample of households** — every person in the selected households
is included (household composition is fully preserved), but only 1 in 10 households was selected.

#### How Spain's 2021 census worked — two steps

**Step 1 — 100% enumeration via administrative registers**
INE combined existing records (Padrón municipal, Social Security, tax registry, civil register)
to count and characterise *every* person and dwelling in Spain. This produces
`C2021_Indicadores.csv` — it covers all 47.4M residents and all 36,333 secciones censales
with no sampling at all.

**Step 2 — 10% detailed questionnaire (random sample)**
For richer individual-level variables (kinship, detailed education, employment situation,
dwelling characteristics at person level), INE sent a longer questionnaire to 1 in 10
households, **selected randomly and proportionally across all regions, provinces, municipalities,
and city sizes**. Within each selected household, every person answered. This produces
`CensoPersonas_2021.tab`.

#### What "10% sample" does and does not mean

**It is NOT geographic** — it does not mean only some cities or regions were covered.
Every region, every province, every city, and every village is represented. Madrid has
sampled households. A village of 200 people in rural Extremadura has sampled households.
The sampling is at household level, spread uniformly across the whole country.

**It IS a statistical sample** — you see roughly 1 in 10 households from each neighbourhood.
This means the file is representative at national and regional level, adequate at
municipality level, but less reliable for very small secciones censales (~70 sampled persons
per sección on average — small secciones may have fewer).

The closest analogy is the **US Census long-form / American Community Survey**: the short-form
counts everyone (100%), while the long-form goes to a rotating sample of households for
detailed socioeconomic variables. Spain's CensoPersonas follows the same logic.

| Dimension | Value |
|---|---|
| Persons in file | ~4.7 million (10% of 47.4M residents) |
| Households in file | ~10% of all Spanish households, sampled uniformly across all areas |
| Geographic coverage | All regions, provinces, municipalities — no area excluded |
| Survey weight | **None** — INE treats the proportional random sample as self-weighting |
| Full data available? | Not publicly — INE restricted access only (see §Full data access below) |

This contrasts with the other two data sources in this project, neither of which is sampled:
- `C2021_Indicadores.csv` / IneAtlas: **100% aggregate** — all 36,333 secciones censales, from Step 1 above
- ADRH: **100% administrative records** — all ~37,034 secciones censales, annual tax/social security data

### Variable structure (from `dr_CensoPersonas_2021.xlsx`)

Each row contains three types of information simultaneously:

**Geography + household linkage**

| Variable | Description | Notes |
|---|---|---|
| `CPRO` | Province code (2 chars) | |
| `CMUN` | Municipality code (3 chars) or size class for small municipalities | Privacy: small municipalities get a size-band code, not the real code |
| `NVIV` | Dwelling/household identifier | Links all persons in the same household |
| `NORDEN` | Person's order within the household | |

**Individual person data**

| Variable | Description | Key values |
|---|---|---|
| `VAREDAD` | Age | 0–100+ |
| `SEXO` | Sex | |
| `ECIVIL` | Civil status | Married/single/widowed/divorced |
| `ESREAL_CNEDA` | Education level (detailed) | Socioeconomic proxy |
| `RELA` | Main labour activity | `1`=employed, `2`=unemployed, `4`=disability pension, `5`=retirement pension ← key HVAC signal, `6`=other inactive, `7`=student |
| `OCU63` | Occupation (2-digit CNO code) | |
| `SITU` | Employment situation | Self-employed/permanent/temporary/other |
| `VARANORES` | Year arrived at current dwelling | Stability signal — long-term residents invest in HVAC |

**Dwelling data (attached to every person row)**

| Variable | Description | Key values |
|---|---|---|
| `TIPO_EDIF_VIV` | Building type | `2`=individual house, `3`=2-dwelling building, `4`=apartment block (3+), `5`=non-residential building |
| `TENEN_VIV` | Tenure | `2`=owner-occupied ← install prerequisite, `3`=rented, `4`=other (social/free), `9`=unknown |
| `SUP_VIV` | Floor area (banded) | `02`=<30m², `03`=30–45, `04`=46–60, `05`=61–75, `06`=76–90, `07`=91–105, `08`=106–120, `09`=121–150, `10`=151–180, `11`=>180m² |
| `ANO_CONS` | Construction year (detailed) | |
| `NPLANTAS_SOBRE_EDIF` | Floors above ground | |

**Kinship linkage** — unique to this dataset, not available in France RP2022

| Variable | Description |
|---|---|
| `NORDEN_MAD` | Row order of parent 1 in this household (links to their row via `NVIV`+`NORDEN`) |
| `NORDEN_PAD` | Row order of parent 2 |
| `NORDEN_CON` | Row order of spouse/partner |
| `NORDEN_OPA` | Row order of other relative |
| `TIPOPER` | Role within family nucleus (head, spouse, child, other relative, non-relative) |
| `FAMILIA` / `NUCLEO` | Family and nucleus identifiers within household |

**Denormalized parent and spouse summaries** — INE pre-joins key attributes of relatives:

| Variable group | Content |
|---|---|
| `VAREDAD_MAD`, `RELA_MAD`, `ESREAL_MAD_GR5`, `SITU_MAD` | Age, activity, education, employment of parent 1 |
| `VAREDAD_PAD`, `RELA_PAD`, `ESREAL_PAD_GR5`, `SITU_PAD` | Same for parent 2 |
| `VAREDAD_CON`, `RELA_CON`, `ESREAL_CON_GR5`, `SITU_CON` | Same for spouse/partner |

**Household summary**

| Variable | Description |
|---|---|
| `TAM_HOG` | Household size |
| `ESTRUC_HOG` | Household structure |
| `TIPO_HOG` | Household type |
| `TIPO_NUC` | Nucleus type |
| `NHIJOS_NUC` | Number of children in nucleus |

### Why person-level opens new modelling possibilities

Unlike the aggregate `C2021_Indicadores.csv` (which gives zone-level summaries), CensoPersonas
allows **cross-person household analysis**. Key use cases for HVAC/solar propensity:

- **Intergenerational purchase**: identify households where an elderly person (`RELA=5`, retired)
  lives with a working-age family member (`RELA=1`, employed) — the younger member often drives
  the HVAC/solar purchase decision on behalf of the household.
- **Multi-generation households**: `TIPO_HOG` + `NHIJOS_NUC` reveal complex household structures
  where purchasing power is pooled.
- **Age gap within household**: link parent ages (`VAREDAD_MAD`, `VAREDAD_PAD`) to child ages
  (`VAREDAD`) — a household where the head is 35 and parents are 65+ is a prime target.
- **Tenure + age combination**: owner-occupied (`TENEN_VIV=2`) household where someone is
  approaching retirement — a signal not recoverable from aggregate data alone.

### Geographic grain limitation

CensoPersonas exposes only province (`CPRO`) and municipality (`CMUN`). The sección censal
code is **not present** in the individual microdata — INE suppresses it for privacy (same
rationale as France's IRIS masking for small communes). This limits geographic joins:

| Join | Possible? | Resulting grain |
|---|---|---|
| CensoPersonas × `adrh_secciones_latest.parquet` | No direct join | — |
| CensoPersonas × `adrh_municipios_latest.parquet` | **Yes** — join on `CPRO+CMUN` → `cod_municipio` | Municipality |
| CensoPersonas × `C2021_Indicadores.csv` | No — C2021 has sección grain not in CensoPersonas | — |
| `C2021_Indicadores` × `adrh_secciones_latest` | **Yes** — join on `cod_seccion` | Sección censal |

**Practical strategy:** attach municipality-level ADRH income features to each CensoPersonas
row (using `adrh_municipios_latest.parquet`). This loses within-city income variation but is
entirely adequate in rural areas and adds meaningful signal nationally.

### S3 files

**Origin:** extracted from `CensoPersonas_2021.zip` downloaded from
`https://www.ine.es/censos2021/CensoPersonas_2021.zip` (April 2024).

| S3 file | Uncompressed | Notes |
|---------|-------------|-------|
| `ine-census-2021/raw/CensoPersonas_2021.tab.zst` | 1.3 GB | Primary data — tab-delimited, one row per person |
| `ine-census-2021/raw/md_CensoPersonas_2021.txt.zst` | 1.0 GB | Machine-readable metadata |
| `ine-census-2021/raw/dr_CensoPersonas_2021.xlsx.zst` | 60 KB | Variable dictionary (codebook) |
| `ine-census-2021/raw/Leeme.txt.zst` | 2 KB | INE readme |

All files are zstd-compressed (level 15). SHA256 hashes in `censo_personas_checksums.sha256`.

**Local download:** `data/input/ine_census_2021/CensoPersonas_2021.tab.zst` (downloaded from S3,
129.5 MB compressed).

**Stage-0 parquet:** see `0_censo_personas_to_parquet.ipynb` — filters to commercial population
(`TENEN_VIV IN ('2','3')`), selects modelling-relevant columns, saves to
`data/generated/ine_census_2021/censo_personas.parquet`.

### Full Census 2021 data — access plan

The 100% census microdata is not publicly available. INE provides restricted access through:

**INE SREA (Servicio de Acceso Remoto a los Datos)**
- Secure remote desktop environment on INE servers — data cannot be extracted, only results
- Requires: institutional affiliation, formal research project proposal, data protection agreement
- Intended for academic/public-interest research — **commercial propensity modelling likely does
  not qualify without framing as a research study**
- Application: `https://www.ine.es/dyngs/SDMX/es/oper.htm?c=ACCESO_INVESTIGADORES`
- Timeline: 2–4 months for approval

**Pragmatic assessment — is 10% sufficient?**

For our use cases, the 10% sample is likely adequate:

| Use case | Assessment |
|---|---|
| National-level propensity scoring | 4.7M records — fully robust |
| Municipality-level aggregation | Adequate — large municipalities have thousands of sampled persons |
| Sección censal aggregation | Marginal — ~70 sampled persons per sección on average; small secciones unreliable |
| Household-graph modelling | Household composition is fully preserved (all persons in selected households included) |

**Recommendation:** proceed with the 10% sample. Apply for SREA access as a long-term goal if
the modelling team needs sección-level individual-level features. For the near term, combine
CensoPersonas (person graph) with `adrh_municipios_latest.parquet` (income context) at
municipality grain.

---

## Dictionary files

### `indicadores_seccen_c2021.xlsx`

Maps t-codes to human-readable descriptions. The full table listing:

| t-code prefix | Description |
|--------------|-------------|
| T1 | Total population (1 value) |
| T2 | % by sex — female, male (2 values) |
| T3 | Mean age (1 value) |
| T4 | % by broad age group — <16, 16–64, 65+ (3 values) |
| T5 | % with foreign nationality (1 value) |
| T6 | % born outside Spain (1 value) |
| T7 | % enrolled in higher education, pop 16+ (1 value) |
| T8 | % enrolled in university, pop 16+ (1 value) |
| T9 | % with completed higher education, pop 16+ (1 value) |
| T10 | Unemployment rate = unemployed / active (1 value) |
| T11 | Employment rate = employed / pop 16+ (1 value) |
| T12 | Activity rate = active / pop 16+ (1 value) |
| T13 | % disability pension recipients, pop 16+ (1 value) |
| T14 | % retirement pension recipients, pop 16+ (1 value) |
| T15 | % other economically inactive, pop 16+ (1 value) |
| T16 | % students, pop 16+ (1 value) |
| T17 | Civil status — single, married, widowed, divorced/sep, unknown (5 values) |
| T18 | Total dwellings count (1 value) |
| T19 | Dwellings by type — primary, non-primary (2 values) |
| T20 | Primary dwellings by tenure — owned, rented, other (3 values) |
| T21 | Total households count (1 value) |
| T22 | Households by size — 1, 2, 3, 4, 5+ persons (5 values) |

The `pablogguz/ineAtlas.data` R package uses this dictionary to map t-codes to English column names. See `INEATLAS_DOCUMENTATION.md` for the English-named equivalent.

### `indicadores_seccen_rejilla.xls`

Grid layout document showing how indicators are organised across the census questionnaire. Reference use only.

### `codccaa.xls` / `codprov.xls`

Lookup tables: numeric code → name for comunidades autónomas and provinces. Useful for adding readable labels to the 2-digit `ccaa` and `cpro` columns.

---

## Spain vs France census — fundamental data model difference

The Spain and France census projects use **structurally different microdata formats**. This has
direct consequences for what kinds of models are possible in each country.

| Dimension | Spain — CensoPersonas 2021 | France — RP2022 logement |
|---|---|---|
| **Unit of observation** | Person (one row per person) | Dwelling (one row per dwelling) |
| **Coverage** | 10% sample of households | Full rolling census (survey-weighted) |
| **Records (public)** | ~4.7M person records | 17.1M dwelling records (after commercial filter) |
| **Survey weight** | None (uniform 10% sample) | `IPONDL` (corrects for large-city undersampling) |
| **Finest geographic grain** | Province + municipality | IRIS zone (9-char) or commune |
| **Household linkage** | Yes — `NVIV` links persons | No — each dwelling is independent |
| **Kinship structure** | Yes — parent/spouse rows linked | No |
| **Parent/spouse attributes** | Yes — denormalized into each row | No |
| **Heating fuel** | **No** — not collected | Yes — `CMBL` (gas/oil/electric/other) |
| **Reference date** | 1 November 2021 (fixed) | 1 January 2022 (rolling 5-year) |
| **Next edition** | 2031 (decennial) | RP2023 expected autumn 2026 |

**What Spain can do that France cannot:**
- Model intergenerational purchase patterns (young family member buys for elderly parent)
- Cross-person features within a household (age gap, employment mix)
- Detect multi-family households where HVAC decisions involve multiple adults

**What France can do that Spain cannot:**
- Heating fuel segmentation at dwelling level (oil vs gas vs electric — the strongest HVAC signal)
- IRIS-level geographic precision (finer than Spanish municipality)
- Full population coverage with survey weights

## How this source relates to the other two

```
Three Spain data sources — coverage comparison:

CensoPersonas_2021.tab   → 10% sample, person-level, ~4.7M rows
                                   ↓
                         municipality grain only (CPRO+CMUN)
                                   ↓
                    join to adrh_municipios_latest.parquet
                    (income context, municipality level)

C2021_Indicadores.csv    → 100% aggregate, 36,333 secciones
  │                               ↓
  └─ pablogguz/IneAtlas   English-named version (census_2021_tract.csv)
                                   ↓
                         join on cod_seccion to ADRH secciones
                         → full sección-level enrichment

ADRH (tax records)       → 100% admin records, 37,034 secciones
                         → income, inequality, income sources
                         → documented in INE_ADRH_DATA_DOCUMENTATION.md
```

---

## Key HVAC-relevant indicators

From `C2021_Indicadores.csv`, the columns most predictive of HVAC propensity are:

| t-code | Description | Why |
|--------|-------------|-----|
| `t4_3` | Share 65+ | Elderly prioritise comfort, trigger replacement cycles |
| `t14_1` | Share retirement pension | Pension income = stable but fixed budget |
| `t11_1` | Employment rate | Economic activity proxy |
| `t20_1` | Owned dwellings (primary) | Ownership is prerequisite for installation |
| `t19_2` | Non-primary dwellings | Holiday homes = seasonal demand |
| `t22_4`, `t22_5` | Households of 4+ persons | Larger family = larger system capacity |

---

## Where the data was obtained

All Census 2021 files are published by INE at:
- Indicator file: `https://www.ine.es/censos2021/C2021_Indicadores.csv`
- Microdata (persons): `https://www.ine.es/censos2021/CensoPersonas_2021.zip`
- Dictionaries: `https://www.ine.es/censos2021/`

These are permanent direct-download URLs (no API key required). Files were downloaded with `wget` in April 2024.

---

## Caveats

1. **2021 vintage** — this is a snapshot. Building age, tenure, household structure reflect 2021 and are not updated until 2031.
2. **t-code columns** — opaque names require the dictionary file to interpret. The `pablogguz` version (`INEATLAS_DOCUMENTATION.md`) provides human-readable alternatives.
3. **Proportions vs counts** — T1, T18, T21 are raw counts; all others are proportions in [0, 1]. Do not mix without normalising.
4. **Census suppression** — very small secciones may have suppressed values (blank cells) to protect privacy.

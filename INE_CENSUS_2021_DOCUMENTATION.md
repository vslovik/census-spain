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

Full **person-level microdata** for the 2021 census. Not used in the current pipeline — archived on S3 for potential future use (individual-level modelling, custom aggregations).

**Origin:** extracted from `CensoPersonas_2021.zip` downloaded from `https://www.ine.es/censos2021/CensoPersonas_2021.zip` (April 2024). The ZIP contains 6 format variants; only the CSV/tab and metadata files are kept on S3 — R/SAS/SPSS/Stata formats were discarded.

| S3 file | Origin (inside zip) | Uncompressed | Notes |
|---------|---------------------|-------------|-------|
| `CensoPersonas_2021.tab.zst` | `CSV/CensoPersonas_2021.tab` | 1.3 GB | Primary data — one row per person |
| `md_CensoPersonas_2021.txt.zst` | `md_CensoPersonas_2021.txt` | 1.0 GB | Machine-readable metadata |
| `dr_CensoPersonas_2021.xlsx.zst` | `dr_CensoPersonas_2021.xlsx` | 60 KB | Variable dictionary |
| `Leeme.txt.zst` | `Leeme.txt` | 2 KB | INE readme |

All files are zstd-compressed (level 15). SHA256 of the compressed file is stored in S3 object metadata (`sha256` key) and in `censo_personas_checksums.sha256` in the project root. Use `verify_ine_adrh_s3.sh` as a reference for the verification pattern.

**Reading from S3:**

```python
import io, zstd, boto3, pandas as pd

BUCKET = "hsf-group-ai-spain-hvac"
s3 = boto3.client("s3")

obj = s3.get_object(Bucket=BUCKET, Key="ine-census-2021/raw/CensoPersonas_2021.tab.zst")
raw = zstd.decompress(obj["Body"].read())
df = pd.read_csv(io.BytesIO(raw), sep="\t", nrows=1000)   # sample first — 1.3 GB uncompressed
```

**Reading from local zip** (if S3 access is unavailable):

```python
import zipfile, pandas as pd

with zipfile.ZipFile("data/input/ine_census_2021/CensoPersonas_2021.zip") as z:
    with z.open("CSV/CensoPersonas_2021.tab") as f:
        df = pd.read_csv(f, sep="\t", nrows=1000)
```

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

## How this source relates to the other two

```
INE Census 2021 (this file)
    └─ C2021_Indicadores.csv   (raw t-code columns)
          │
          └─ pablogguz reprocesses → census_2021_tract.csv
                (English column names, proportions, all 36,333 tracts)
                → documented in INEATLAS_DOCUMENTATION.md

INE Census 2021 (this file)
    └─ join with ADRH on cod_seccion
          → ADRH covers income; Census covers housing and demographics
          → see DATA_SOURCES.md for the full 3-source picture
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

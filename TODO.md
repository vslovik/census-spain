# TODO — ADRH / eda_adrh.ipynb

## Current priority: other pending items (see below)

---

## After new wide parquets — Section 5: regional heatmaps (SUPERSEDED — see above)

Add a Section 5 to `eda_adrh.ipynb`:
- Extract `prov_code` from first 2 chars of `cod_seccion`
- Map to CCAA using `prov_code → region` dict (same as in `eda_ineatlas.ipynb`)
- Province-level heatmap: `renta_neta_media_por_hogar`, pension share, Gini
- CCAA-level heatmap with annotations
- Aggregate only from high-coverage columns (>50% secciones); label partial-coverage cols clearly

---

## Other pending items

- **Folder reorganisation**: move raw input files to `data/input/{source}/` and generated
  files to `data/generated/{source}/` — pipeline scripts still reference old paths.

- [x] **S3 upload of generated files**: all 9 parquets uploaded to `s3://hsf-group-ai-spain-hvac/` (account 268271485741) — see upload map in `GENERATED_DATA.md`

- [x] **INE Census 2021 EDA (third data source)**: `eda_censo2021.ipynb` created and executed — 7 sections covering demographics, labour market & pensions, housing tenure, household composition, CCAA heatmap, and ADRH merge/correlations

---

## Completed

- [x] Decoded all `t1_1`–`t22_5` INE C2021 indicator codes via `indicadores_seccen_c2021.xlsx`
  — t15/t16 are NOT heating/AC (they are % otra inactividad / % estudiantes); t14_1 = % retirement pension (KEY HVAC signal); t20_1 = viviendas en propiedad (KEY for HVAC)
  — Full mapping documented in `GENERATED_DATA.md`
- [x] Fixed `censo2021_secciones.parquet`: rebuilt from IneAtlas CSV (36,333 × 41) with correct column names and values; old parquet had wrong INDICATOR_MAP (column values were shifted)
- [x] Fixed `download_censo2021.py`: corrected `sep=";"` → `sep=","`, replaced entire INDICATOR_MAP with verified t-codes from xlsx, added `cod_seccion` construction from `cpro+cmun+dist+secc`

- [x] Verified CSV vs JSON geographic granularity empirically (table 37677)
  - CSV: 37,072 secciones; JSON: 37,071; one CSV-only: `1103205003` (Cádiz)
  - CSV is full grid; JSON is sparse (omits unpublished observations)
  - Updated `INE_ADRH_DATA_DOCUMENTATION.md` with verified findings
- [x] Built `eda_adrh.ipynb` with S3 reader, cache, generated file inspection, HVAC distribution plots
- [x] Built `adrh_secciones_2023_wide.parquet` (36,395 × 21, strict 2023, tables 30824/30825/30826/31097)
  — will be superseded by `adrh_secciones_latest.parquet`
- [x] Built `adrh_{secciones,distritos,municipios}_latest.parquet` (most-recent-available, all 6 tables, 29 indicators + vintage year cols)
- [x] Added Section 6 to `eda_adrh.ipynb` — province heatmap (3 key indicators) + CCAA heatmap (8 HVAC-relevant indicators, annotated)
- [x] Documented regional findings in `EDA_REGIONAL_FINDINGS.md` (heatmap analysis, Basque NaN root cause, Census 2021 PDF cross-validation)
- [x] Fixed `eda_ineatlas.ipynb` file path: both cell 0 and cell 8 now use `data/input/ineatlas/census_2021_tract.csv`; cell 8 uses `DATA_PATH` variable
- [x] Created `GENERATED_DATA.md` — full inventory of all generated parquet files
- [x] `select_dtypes("object")` TODO: N/A — no such usage exists in project code; only `select_dtypes("float64")` is used

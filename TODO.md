# TODO — Spain Census

---

## Pending

- **CensoPersonas pre-aggregation parquet** ← *next up*: Run `0_censo_personas_to_parquet.ipynb`.
  File already downloaded locally (`data/input/ine_census_2021/CensoPersonas_2021.tab.zst`, 129.5 MB).
  Commercial filter confirmed from codebook: `TENEN_VIV IN ('2', '3')` (owner-occupied + private
  rented; excludes social/other housing). Column selection: keep geography+linkage (CPRO, CMUN,
  NVIV, NORDEN), person demographics (VAREDAD, SEXO, ECIVIL, ESREAL_CNEDA, RELA, OCU63, SITU,
  VARANORES), dwelling (TIPO_EDIF_VIV, SUP_VIV, TENEN_VIV, NPLANTAS_SOBRE_EDIF, ANO_CONS),
  kinship linkage (NORDEN_MAD, NORDEN_PAD, NORDEN_CON, NORDEN_OPA, FAMILIA, NUCLEO, TIPOPER),
  parent/spouse summaries (VAREDAD_MAD/PAD/CON, RELA_MAD/PAD/CON, ESREAL_MAD/PAD/CON_GR5,
  SITU_MAD/PAD/CON), household (TAM_HOG, ESTRUC_HOG, TIPO_HOG), nucleus (TIPO_NUC, TAM_NUC,
  NHIJOS_NUC). Drop all `_MI` imputation flag columns and mobility/migration columns.
  Update Cell 4 in the notebook with this filter and column list, then run.

- **INE Census 2021 shapefile**: needed for customer address → `cod_seccion` spatial join. Not yet in S3 (`ine-census-2021/dictionaries/` only has xlsx/xls code tables). Download from INE cartography portal and upload. Required before building the geocoding pipeline (`CUSTOMER_DATA_JOIN.md`).

- **Customer address data**: send `letter_to_sales.md` to sales/CRM team. Address data is the prerequisite for the customer enrichment pipeline.

---

## Completed

- [x] Built `eda_adrh.ipynb` — S3 reader, cache, HVAC distributions, province + CCAA heatmaps (Sections 1–6)
- [x] Built `adrh_{secciones,distritos,municipios}_latest.parquet` (37,034 × 59, 29 indicators + vintage cols)
- [x] Documented regional findings in `EDA_REGIONAL_FINDINGS.md` (heatmaps, Basque NaN root cause, Census 2021 PDF cross-validation)
- [x] Decoded all `t1_1`–`t22_5` INE C2021 t-codes via `indicadores_seccen_c2021.xlsx` — full mapping in `GENERATED_DATA.md`
- [x] Rebuilt `censo2021_secciones.parquet` (36,333 × 41) from IneAtlas CSV with correct column names
- [x] Fixed `download_censo2021.py`: `sep=","`, correct INDICATOR_MAP, `cod_seccion` construction
- [x] Created `eda_censo2021.ipynb` — 8 sections: demographics, pensions, housing tenure, CCAA heatmap, ADRH merge, temperature reference
- [x] Uploaded all 9 generated parquets to S3 (`ine-adrh/generated/`, `ineatlas/generated/`) — map in `GENERATED_DATA.md`
- [x] Created `GENERATED_DATA.md` — parquet inventory, S3 map, t-code mapping, customer join guide, notebook comparison
- [x] Created `CUSTOMER_DATA_JOIN.md` — full technical guide for geocoding + spatial join pipeline
- [x] Created `letter_to_sales.md` — data request for service addresses with HVAC motivation
- [x] Replaced all OpenClaw paths with in-project equivalents (`data/input/ine_adrh/`, `data/browser_profile/`) across 6 files
- [x] Deleted 35 GB ADRH raw files from `~/.openclaw/workspace/downloads/ine_5650/` (all on S3)
- [x] Deleted `CensoPersonas_2021.zip` (1.2 GB) — content on S3 as `.tab.zst`
- [x] Created `data/input/ine_adrh/` directory for ADRH re-download scripts

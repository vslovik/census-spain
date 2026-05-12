# Generated Data Inventory

All files in `data/generated/`. Last updated: 2026-05-12.

S3 bucket: `s3://hsf-group-ai-spain-hvac/` (account 268271485741, profile `AWSAdministratorAccess-268271485741`, region `eu-west-2`)

## S3 upload map

| Local path | S3 path |
|---|---|
| `data/generated/adrh/adrh_secciones_latest.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/adrh_secciones_latest.parquet` |
| `data/generated/adrh/adrh_distritos_latest.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/adrh_distritos_latest.parquet` |
| `data/generated/adrh/adrh_municipios_latest.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/adrh_municipios_latest.parquet` |
| `data/generated/adrh/adrh_secciones_2023_wide.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/adrh_secciones_2023_wide.parquet` |
| `data/generated/adrh/adrh_secciones_renta.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/adrh_secciones_renta.parquet` |
| `data/generated/adrh/30824_secciones.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/30824_secciones.parquet` |
| `data/generated/adrh/30825_secciones.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/30825_secciones.parquet` |
| `data/generated/adrh/30826_secciones.parquet` | `s3://hsf-group-ai-spain-hvac/ine-adrh/generated/30826_secciones.parquet` |
| `data/generated/ineatlas/censo2021_secciones.parquet` | `s3://hsf-group-ai-spain-hvac/ineatlas/generated/censo2021_secciones.parquet` |
| `data/generated/ine_census_2021/censo_personas.parquet` | `s3://hsf-group-ai-spain-hvac/ine-census-2021/generated/censo_personas.parquet` |

---

## ADRH (`data/generated/adrh/`)

### Intermediate long-format extracts (produced by `download_adrh_remaining.py`)

These are raw CSV extracts filtered to sección censal level, in long format. They are **intermediate files** — the canonical features come from `adrh_secciones_latest.parquet`.

| File | Shape | Size | Years | Key |
|---|---|---|---|---|
| `30824_secciones.parquet` | 1,879,892 × 5 | 4.6 MB | 2015–2023 | `cod_seccion` |
| `30825_secciones.parquet` | 1,507,392 × 5 | 2.3 MB | 2015–2023 | `cod_seccion` |
| `30826_secciones.parquet` | 2,524,050 × 5 | 3.7 MB | 2015–2023 | `cod_seccion` |

Columns (all three): `cod_seccion`, `año`, `indicador`, `valor`, `unidad`

| Table | Content | Unique secciones |
|---|---|---|
| 30824 | Income: renta neta/bruta media por hogar/persona, media/mediana de la renta por UC | 36,994 |
| 30825 | Income sources (%): salary, pension, unemployment, other benefits, other income | 35,782 |
| 30826 | Poverty thresholds: % population with income below 5k/7.5k/10k € (by sex, Total) | 32,881 |

---

### `adrh_secciones_renta.parquet`
**Producer:** `adrh_secciones.py`  
**Source:** ADRH table 31097 (renta media y mediana por unidad de consumo) — CSV  
**Shape:** 39,689 × 11  **Size:** 1.0 MB  
**Format:** one row per (sección × year), years 2015–2023  
**Note:** Only 4,537 unique secciones — table 31097 has much lower geographic coverage than 30824. Superseded by `adrh_secciones_latest.parquet` for modelling purposes.

Columns:
```
cod_seccion, cod_provincia, cod_municipio, municipio, periodo,
renta_media_uc, renta_mediana_uc, renta_bruta_media_hogar,
renta_bruta_media_persona, renta_neta_media_hogar, renta_neta_media_persona
```

---

### `adrh_secciones_2023_wide.parquet`
**Producer:** `eda_adrh.ipynb` (Section 4)  
**Source:** tables 30824, 30825, 30826, 31097 — CSV, strict 2023 filter  
**Shape:** 36,395 × 21  **Size:** 1.4 MB  
**Format:** wide, one row per sección censal, 2023 vintage only  
**Note:** Superseded by `adrh_secciones_latest.parquet` which covers more secciones (37,034 vs 36,395), more indicators (29 vs 20), and has year vintage columns.

Columns:
```
cod_seccion,
media_de_la_renta_por_unidad_de_consumo, mediana_de_la_renta_por_unidad_de_consumo,
renta_bruta_media_por_hogar, renta_bruta_media_por_persona,
renta_neta_media_por_hogar, renta_neta_media_por_persona,
fuente_de_ingreso_otras_prestaciones, fuente_de_ingreso_otros_ingresos,
fuente_de_ingreso_pensiones, fuente_de_ingreso_prestaciones_por_desempleo,
fuente_de_ingreso_salario,
poblacion_con_ingresos_por_unidad_de_consumo_por_debajo_de_10_000_euros,
poblacion_con_ingresos_por_unidad_de_consumo_por_debajo_de_5_000_euros,
poblacion_con_ingresos_por_unidad_de_consumo_por_debajo_de_7_500_euros,
renta_media_uc, renta_mediana_uc, renta_bruta_media_hogar,
renta_bruta_media_persona, renta_neta_media_hogar, renta_neta_media_persona
```

---

### `adrh_secciones_latest.parquet` ← primary ADRH sección feature file
**Producer:** `eda_adrh.ipynb` (Section 5)  
**Source:** ADRH JSON, tables 30824/30825/30826/30829/30832/37677 — most-recent-available per (sección × indicator)  
**Shape:** 37,034 × 59  **Size:** 2.1 MB  
**Format:** wide, one row per sección censal; each indicator has a companion `{col}_year` vintage column (Int16)  
**Key:** `cod_seccion` (10 chars, zero-padded, e.g. `"0100101001"`)  
**Year range:** 2015–2023 (most secciones have 2023; some have earlier years for indicators with lower coverage)

29 value columns + 29 year columns:

| Group | Columns | Source table | Coverage |
|---|---|---|---|
| Income | `renta_neta_media_por_hogar`, `renta_neta_media_por_persona`, `renta_bruta_media_por_hogar`, `renta_bruta_media_por_persona`, `media_de_la_renta_por_unidad_de_consumo`, `mediana_de_la_renta_por_unidad_de_consumo` | 30824 | ~99.9% |
| Income sources (%) | `fuente_de_ingreso_salario`, `fuente_de_ingreso_pensiones`, `fuente_de_ingreso_prestaciones_por_desempleo`, `fuente_de_ingreso_otras_prestaciones`, `fuente_de_ingreso_otros_ingresos` | 30825 | ~92–96.6% — **NaN for Basque Country (prov 01/20/48): INE suppression due to Haciendas Forales** |
| Absolute poverty thresholds (%) | `poblacion_con_ingresos_por_unidad_de_consumo_por_debajo_de_5_000_euros`, `..._7_500_euros`, `..._10_000_euros` | 30826 | ~88.8% |
| Relative poverty thresholds (%) | `..._por_debajo_40_de_la_mediana`, `..._50_`, `..._60_`, `..._por_encima_140_`, `..._160_`, `..._200_` | 30829 | ~88.8% |
| Demographics | `poblacion`, `edad_media_de_la_poblacion`, `tamano_medio_del_hogar`, `porcentaje_de_hogares_unipersonales`, `porcentaje_de_poblacion_de_65_y_mas_anos`, `porcentaje_de_poblacion_menor_de_18_anos`, `porcentaje_de_poblacion_espanola` | 30832 | 100% |
| Inequality | `indice_de_gini`, `distribucion_de_la_renta_p80_p20` | 37677 | ~96.6% |

---

### `adrh_distritos_latest.parquet` ← primary ADRH distrito feature file
**Producer:** `eda_adrh.ipynb` (Section 5)  
**Shape:** 10,513 × 59  **Size:** 0.7 MB  
**Key:** `cod_distrito` (7 chars, e.g. `"0100101"`)  
Same 29 indicators + 29 year columns as `adrh_secciones_latest.parquet`.

---

### `adrh_municipios_latest.parquet` ← primary ADRH municipio feature file
**Producer:** `eda_adrh.ipynb` (Section 5)  
**Shape:** 8,134 × 59  **Size:** 0.5 MB  
**Key:** `cod_municipio` (5 chars, e.g. `"01001"`)  
Same 29 indicators + 29 year columns as `adrh_secciones_latest.parquet`.

---

## Census 2021 / IneAtlas (`data/generated/ineatlas/`)

### `censo2021_secciones.parquet` ← primary Census 2021 sección feature file
**Producer:** rebuilt from `data/input/ineatlas/census_2021_tract.csv` (IneAtlas processed version)  
**Source:** INE Census 2021 indicators (June 2023), processed by IneAtlas  
**Shape:** 36,333 × 41  **Size:** 2.8 MB  
**Format:** wide, one row per sección censal  
**Key:** `cod_seccion` (10 chars, zero-padded, e.g. `"0400101001"`)

Columns:

```
cod_seccion, cod_distrito, cod_municipio, cod_provincia, provincia,
poblacion_total,
pct_mujeres, pct_hombres, edad_media,
pct_menores_16, pct_16_64, pct_mayores_64,
pct_extranjeros, pct_nacidos_extranjero,
pct_cursando_estudios_superiores, pct_cursando_universidad,
pct_estudios_superiores_completados,
tasa_paro, tasa_empleo, tasa_actividad,
pct_pension_invalidez, pct_pension_jubilacion,   ← KEY HVAC signal (retirement share)
pct_otra_inactividad, pct_estudiantes,
pct_soltero, pct_casado, pct_viudo,
pct_estado_civil_desconocido, pct_separado_divorciado,
total_viviendas, viviendas_principales, viviendas_no_principales,
viviendas_en_propiedad,                          ← KEY HVAC signal (homeownership)
viviendas_en_alquiler, viviendas_otro_regimen,
total_hogares,
hogares_1_persona, hogares_2_personas, hogares_3_personas,
hogares_4_personas, hogares_5_mas_personas
```

Full INE C2021 t-code mapping (verified against `data/input/ine_census_2021/indicadores_seccen_c2021.xlsx`):

| t-code | Meaning | Notes |
|---|---|---|
| `t1_1` | Total personas | |
| `t2_1` | % mujeres | |
| `t2_2` | % hombres | |
| `t3_1` | Edad media | |
| `t4_1` | % menores de 16 | |
| `t4_2` | % 16–64 | |
| `t4_3` | % mayores de 64 | |
| `t5_1` | % extranjeros | |
| `t6_1` | % nacidos en el extranjero | |
| `t7_1` | % cursando estudios superiores (escur 08–12) | |
| `t8_1` | % cursando universidad (escur 09–12) | |
| `t9_1` | % con estudios superiores completados | |
| `t10_1` | % parados / activos (tasa de paro) | |
| `t11_1` | % ocupados / pob 16+ (tasa de empleo) | |
| `t12_1` | % activos / pob 16+ (tasa de actividad) | |
| `t13_1` | % pensionistas invalidez / pob 16+ | |
| `t14_1` | % pensionistas jubilación / pob 16+ | **KEY HVAC signal** — retirement pension share |
| `t15_1` | % otra inactividad / pob 16+ | NOT heating system |
| `t16_1` | % estudiantes / pob 16+ | NOT air conditioning |
| `t17_1` | % soltero | |
| `t17_2` | % casado | |
| `t17_3` | % viudo | |
| `t17_4` | % estado civil no consta | |
| `t17_5` | % separado o divorciado | |
| `t18_1` | Total viviendas | |
| `t19_1` | Viviendas principales | |
| `t19_2` | Viviendas no principales (vacancy signal) | |
| `t20_1` | Viviendas en propiedad | **KEY for HVAC** — homeownership |
| `t20_2` | Viviendas en alquiler | |
| `t20_3` | Viviendas otro régimen | |
| `t21_1` | Total hogares | |
| `t22_1` | Hogares de 1 persona | |
| `t22_2` | Hogares de 2 personas | |
| `t22_3` | Hogares de 3 personas | |
| `t22_4` | Hogares de 4 personas | |
| `t22_5` | Hogares de 5 o más personas | |

---

## CensoPersonas 2021 (`data/generated/ine_census_2021/`)

### `censo_personas.parquet` ← primary person-level microdata file
**Producer:** `0_censo_personas_to_parquet.ipynb`  
**Source:** `CensoPersonas_2021.tab.zst` — INE Census 2021 person microdata (10% random sample)  
**Shape:** 4,348,375 rows × 45 columns  **Size:** 59 MB  
**Format:** one row per person; all columns stored as strings (all_varchar=true at read time)  
**Key:** `CPRO` + `CMUN` (province + municipality) — finest grain available in individual microdata  
**Filter applied:** `TENEN_VIV IN ('2', '3')` — owner-occupied and private rented only; social/free housing excluded

Column groups:

| Group | Columns | Purpose |
|---|---|---|
| Geography + linkage | `CPRO`, `CMUN`, `NVIV`, `NORDEN` | Geographic join + within-household person linkage |
| Person demographics | `ANAC`, `VAREDAD`, `SEXO`, `ECIVIL`, `ESREAL_CNEDA`, `RELA`, `OCU63`, `ACT89`, `SITU`, `VARANORES` | Age, sex, education, employment, stability |
| Dwelling | `TIPO_EDIF_VIV`, `SUP_VIV`, `TENEN_VIV`, `NPLANTAS_SOBRE_EDIF`, `ANO_CONS` | Building type, area, tenure, construction year |
| Kinship linkage | `NORDEN_PAD`, `NORDEN_MAD`, `NORDEN_CON`, `NORDEN_OPA`, `FAMILIA`, `NUCLEO`, `TIPOPER` | Links to parent/spouse rows; enables intergenerational modelling |
| Parent 1 summary | `VAREDAD_MAD`, `ESREAL_MAD_GR5`, `RELA_MAD`, `SITU_MAD` | Age, education, activity, employment of parent 1 |
| Parent 2 summary | `VAREDAD_PAD`, `ESREAL_PAD_GR5`, `RELA_PAD`, `SITU_PAD` | Same for parent 2 |
| Spouse summary | `VAREDAD_CON`, `ESREAL_CON_GR5`, `RELA_CON`, `SITU_CON` | Same for spouse/partner |
| Household | `TAM_HOG`, `ESTRUC_HOG`, `TIPO_HOG` | Household size and structure |
| Nucleus | `TIPO_NUC`, `TAM_NUC`, `NHIJOS_NUC`, `TIPO_PAR_NUC1` | Family nucleus type and size |

**Dropped columns:** all `_MI` imputation flag columns (~24), mobility/migration history columns (~18),
nationality/birthplace detail columns (~8), workplace/study location columns (~6), and columns
derivable from others (`SUP_OCU_VIV`, `NPLANTAS_BAJO_EDIF`, `FAM_HOG`, `NUC_HOG`, `TIPO_PAR_NUC2`).

**Join to ADRH:** municipality level only — sección censal code not present in individual microdata.
Use `adrh_municipios_latest.parquet` keyed on `CPRO.zfill(2) + CMUN.zfill(3)` = `cod_municipio`.

---

## Joining census data with customer data

See **`CUSTOMER_DATA_JOIN.md`** for full documentation: join options by data quality, implementation sketch (GeoPandas spatial join), feature inventory after enrichment, match rate expectations, and privacy note.

**Summary:** the recommended path is geocoding the service address → lat/lon → spatial join to INE sección censal shapefile → `cod_seccion`. Geographic key alignment:

| Dataset | Key | Format |
|---|---|---|
| `censo2021_secciones.parquet` | `cod_seccion` | 10 chars, e.g. `"2800101001"` |
| `adrh_secciones_latest.parquet` | `cod_seccion` | 10 chars |
| `adrh_distritos_latest.parquet` | `cod_distrito` | 7 chars |
| `adrh_municipios_latest.parquet` | `cod_municipio` | 5 chars |
| INE sección shapefile | `CUSEC` | 10 chars (exact match to `cod_seccion`) |

---

## EDA notebooks — Census 2021

Two notebooks cover the Census 2021 / IneAtlas data:

| Notebook | Data source | Focus | Unique content |
|---|---|---|---|
| `eda_ineatlas.ipynb` | `data/input/ineatlas/census_2021_tract.csv` (English column names) | Exploratory — age, household composition × age, province profiles | **Temperature reference data** (52 provinces, Open-Meteo); detailed hh-composition × age scatter grids |
| `eda_censo2021.ipynb` | `data/generated/ineatlas/censo2021_secciones.parquet` (Spanish column names) | Canonical analysis aligned with ADRH notebooks | Pension & homeownership as explicit HVAC signals; ADRH merge & correlation matrix; temperature section (extracted from `eda_ineatlas.ipynb`) |

`eda_censo2021.ipynb` is the forward-looking reference; `eda_ineatlas.ipynb` is the original exploratory scratch notebook kept for its detailed household × age cross-analysis.

---

## Input files (not generated — reference only)

| Path | Description |
|---|---|
| `data/input/ineatlas/census_2021_tract.csv` | Census 2021 tract-level demographics (IneAtlas processed version), 36,333 rows × 41 cols — used in `eda_ineatlas.ipynb` |
| `data/cache/adrh/*.json.zst` | ADRH raw JSON files, zstd-compressed, cached from S3 |
| `data/cache/adrh/37677.parquet` | Table 37677 CSV cached as parquet by `read_adrh_csv()` |

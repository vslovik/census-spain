# TODO — ADRH / eda_adrh.ipynb

## Immediate next step (start here)

### 1. Verify CSV vs JSON geographic granularity claim
`INE_ADRH_DATA_DOCUMENTATION.md` currently states CSV and JSON have "identical geographic
granularity". This has NOT been verified empirically.

**Task:** Add a notebook cell that:
- Reads `37677.csv.zst` from S3 (102 MB raw — smallest CSV, already cached JSON)
- Extracts sección-level rows and collects the set of unique `cod_seccion` values
- Reads `37677.json.zst` from cache, extracts sección `Codigo` values
- Compares the two sets: count, overlap, CSV-only, JSON-only
- Also checks the 243 value/suppressed discrepancy (values in CSV that are null in JSON)

Then update the documentation to reflect what is actually observed, not assumed.

---

## After verification — process missing tables

The current `adrh_secciones_2023_wide.parquet` is incomplete.
The HVAC feature extraction plan (bottom of `INE_ADRH_DATA_DOCUMENTATION.md`) requires:
**30824 ✓, 37677 ✗, 30832 ✗, 30825 ✓, 30829 ✗**

Three tables need sección-level parquets built from JSON (not CSV):

| Table | Content | Why JSON |
|-------|---------|----------|
| **37677** | Gini index + P80/P20 ratio | Clean `cod_seccion` from `MetaData[].Codigo`, no regex |
| **30832** | Demographics: mean age, % over 65, % single-person HH, household size | Mixed units (`T3_Unidad`) — essential to parse correctly |
| **30829** | % population below relative thresholds (40/50/60/80/120% of median) | Mixed sex/total breakdown — filter to Total rows via MetaData |

For each table, the processing cell should:
1. Call `read_adrh_json_raw(table_id)`
2. Filter to sección-level entries using `MetaData[].T3_Variable == "Secciones"`
3. Extract `cod_seccion` from `MetaData[].Codigo`
4. Extract indicator name from the relevant `MetaData` dimension
5. Extract `T3_Unidad`, `COD`, year (`Anyo`), value (`Valor`) from `Data`
6. Flatten to long format, filter to 2023, pivot to wide
7. Save as parquet in `data/generated/adrh/` with `COD` and `T3_Unidad` columns preserved

Then rebuild `adrh_secciones_2023_wide.parquet` to include all 5 tables.

---

## After new wide parquet — Section 5: regional heatmaps

Add a Section 5 to `eda_adrh.ipynb`:
- Extract `prov_code` from first 2 chars of `cod_seccion` (no hardcoded lookup needed)
- Map to CCAA using `prov_code → region` dict (same as in `eda_ineatlas.ipynb`)
- Province-level heatmap: `renta_neta_media_por_hogar`, pension share, Gini (once 37677 processed)
- CCAA-level heatmap with annotations

Note: aggregate only from high-coverage columns (>50% secciones). The 31097 renta columns
cover only 4,480 secciones (large urban municipalities) — label clearly if shown.

---

## Other pending items

- **Fix `eda_ineatlas.ipynb` file path**: still loads from `data/census/census_2021_tract.csv`
  (old path). Should be `data/input/ineatlas/census_2021_tract.csv`.

- **`GENERATED_DATA.md`**: inventory of all generated parquet files — what each contains,
  which script/notebook produced it, column list, row count.

- **`select_dtypes("object")` Pandas 4 warning**: fix in any `optimise_dtypes()` calls
  to use `include=["object", "string"]`.

- **Folder reorganisation**: move raw input files to `data/input/{source}/` and generated
  files to `data/generated/{source}/` — pipeline scripts still reference old paths.

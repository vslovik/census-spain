# INE ADRH Data — Documentation

**Dataset:** Atlas de Distribución de Renta de los Hogares (ADRH)
**Publisher:** Instituto Nacional de Estadística (INE), Spain
**Source URL:** `https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177088&menu=resultados&idp=1254735976608`
**S3 archive:** `s3://hsf-group-ai-spain-hvac/ine-adrh/raw/`
**Downloaded:** October 2022 (CSV), April 2025 (JSON)
**Archival date:** May 2026

---

## What this dataset is

The ADRH is Spain's household income distribution atlas produced annually by INE. It combines tax records (AEAT) with municipal population registers to produce income, poverty, and demographic indicators at three geographic levels:

- **Municipio** (municipality) — ~8,000 units
- **Distrito censal** (census district) — ~10,500 units
- **Sección censal** (census tract) — ~35,000 units

The **sección censal** is the primary join key for HVAC propensity modelling (`cod_seccion`: 10-digit code, structure `cpro(2) + cmun(3) + dist(2) + secc(3)`).

**Time coverage:** 2015–2023 (most sección-level data available from 2019 onward for smaller municipalities).

---

## Tables

| Table ID | Title | Dimensions | HVAC relevance |
|----------|-------|------------|----------------|
| **30824** | Indicadores de renta media y mediana | Geo × Indicator × Year | **HIGH** — net income per household/person, median UC income |
| **37677** | Índice de Gini y Distribución P80/P20 | Geo × Indicator × Year | **HIGH** — income inequality concentration |
| **30832** | Indicadores demográficos | Geo × Indicator × Year | **HIGH** — mean age, household size, % elderly, % single-person |
| **30825** | Distribución por fuente de ingresos | Geo × Source × Year | **MEDIUM** — % from salary, pensions, unemployment, transfers |
| **30829** | % población debajo/encima umbrales relativos, por sexo | Geo × Sex × Threshold × Year | **MEDIUM** — poverty/affluence proxy (40/50/60/80/120% median) |
| **30826** | % población debajo umbrales fijos, por sexo | Geo × Sex × Threshold × Year | **LOW-MEDIUM** — fixed thresholds (5k/7.5k/10k €), Total-sex rows useful |
| **30827** | % población debajo umbrales fijos, por sexo y edad | Geo × Sex × Age × Threshold × Year | **LOW** — highly granular, limited added value over 30826 |
| **30828** | % población debajo umbrales fijos, por sexo y nacionalidad | Geo × Sex × Nationality × Threshold × Year | **LOW** — granular, many suppressed cells |
| **30830** | % población debajo/encima umbrales relativos, por sexo y edad | Geo × Sex × Age × Threshold × Year | **LOW** |
| **30831** | % población debajo/encima umbrales relativos, por sexo y nacionalidad | Geo × Sex × Nationality × Threshold × Year | **LOW** — high suppression at sección level |

### Indicator values by table

**30824 — Income indicators:**
- Renta neta media por persona
- Renta neta media por hogar ← primary HVAC feature
- Renta bruta media por persona
- Renta bruta media por hogar
- Media de la renta por unidad de consumo
- Mediana de la renta por unidad de consumo

**37677 — Inequality:**
- Índice de Gini
- Distribución de la renta P80/P20

**30832 — Demographics:**
- Población
- Edad media de la población
- Tamaño medio del hogar
- Porcentaje de hogares unipersonales
- Porcentaje de población de 65 y más años
- Porcentaje de población menor de 18 años
- Porcentaje de población española

**30825 — Income sources:**
- Fuente de ingreso: salario
- Fuente de ingreso: pensiones
- Fuente de ingreso: prestaciones por desempleo
- Fuente de ingreso: otras prestaciones
- Fuente de ingreso: otros ingresos

---

## File formats: CSV vs JSON

Both formats contain data at **all three geographic levels** (municipio, distrito, sección). Their coverage and structure differ in two verified ways (table 37677, May 2026):

**1. Sección coverage — nearly but not fully identical**

| | CSV | JSON |
|-|-----|------|
| Unique secciones | 37,072 | 37,071 |
| In common | 37,071 | 37,071 |
| Format-only | 1 (`1103205003`, Cádiz) | 0 |

One sección (`1103205003`) appears in the CSV but not the JSON. Zero JSON-only secciones. For 2023 extraction this is negligible, but processing from JSON alone will miss this one Cádiz sección.

**2. Grid completeness — CSV is full, JSON is sparse**

CSV contains a **complete grid**: every sección × year × indicator combination is present as a row, even when INE published no data for that cell. JSON **omits observations where no data was published** — a sección with coverage only from 2019 onward will have 5 entries in JSON but 9 rows in CSV.

For table 37677 at sección level:
- CSV: 667,296 rows (= 37,072 × 2 indicators × 9 years — exact full grid)
- JSON: 643,520 data points (23,776 fewer — missing grid entries omitted)
- 54 observations classified as values in CSV but `null` in JSON (negligible reclassification)

**3. Metadata richness — JSON is richer per observation**

| Field | CSV | JSON |
|-------|-----|------|
| Value | ✓ value column | ✓ `Valor` in `Data` array |
| Year | ✓ integer | ✓ `Anyo` (int) + `Fecha` (ISO-8601 full timestamp) |
| Geographic code | ✗ must regex the label string | ✓ `MetaData[].Codigo` — clean code, no parsing |
| Unit | ✗ must infer from column name | ✓ `T3_Unidad` (e.g. `"Euros"`, `"Porcentaje"`, `"Años"`, `"Número"`) |
| Scale factor | ✗ | ✓ `T3_Escala` (`" "` = no scaling) |
| Series identifier | ✗ | ✓ `COD` — stable across annual updates, enables targeted re-fetch |
| Data quality flag | ✗ | ✓ `T3_TipoDato` (`"Definitivo"` = confirmed final value) |
| Periodicity flag | ✗ | ✓ `T3_Periodo` (`"A"` = annual) |
| Suppressed values | `.` string | `null` |

**For all new sección-level extractions, prefer the JSON**: `cod_seccion` comes clean from `MetaData[].Codigo`, units are explicit, `COD` enables incremental annual updates, and the sparse structure means fewer NaN rows to handle. The one CSV-only sección (`1103205003`) can be accepted as a known gap.

The existing parquets for tables 30824, 30825, 30826 were built from CSV and are missing `COD`, `T3_Unidad`, and `T3_TipoDato` columns.

---

## JSON series object — complete field reference

Observed structure (table 37677, verified May 2026):

```json
{
  "COD": "ADRH9292917",
  "Nombre": "Alegría-Dulantzi sección 01001. Dato base. Índice de Gini. ",
  "T3_Unidad": "Porcentaje",
  "T3_Escala": " ",
  "MetaData": [
    {
      "Id": 366836,
      "T3_Variable": "Secciones",
      "Nombre": "Alegría-Dulantzi sección 01001",
      "Codigo": "0100101001"
    },
    {
      "Id": 72,
      "T3_Variable": "Tipo de dato",
      "Nombre": "Dato base",
      "Codigo": ""
    },
    {
      "Id": 382445,
      "T3_Variable": "SALDOS CONTABLES",
      "Nombre": "Índice de Gini",
      "Codigo": ""
    }
  ],
  "Data": [
    {
      "Fecha": "2023-01-01T00:00:00.000+01:00",
      "T3_TipoDato": "Definitivo",
      "T3_Periodo": "A",
      "Anyo": 2023,
      "Valor": 26.8
    }
  ]
}
```

### Top-level series fields

| Field | Type | Description |
|-------|------|-------------|
| `COD` | string | Stable INE series identifier (e.g. `"ADRH9292917"`). Unique per series. Use for targeted re-fetch on annual update — no full-table re-download needed. |
| `Nombre` | string | Human-readable label encoding geography + indicator + tipo de dato. Trailing spaces and dots are present — strip before use. |
| `T3_Unidad` | string | Unit of all `Valor` values. Observed: `"Porcentaje"`, `"Número"`, `"Euros"`, `"Años"`. Essential for mixed-unit tables (30832 has all four). |
| `T3_Escala` | string | Scale factor. Observed as `" "` (single space) = no scaling. Treat `" "`, `""`, and `null` as scale 1. |
| `MetaData` | array | Dimension values for this series. See below. |
| `Data` | array | Annual time series. See below. |

### `MetaData` array

Each element describes one dimension of the series:

| Sub-field | Description |
|-----------|-------------|
| `Id` | Numeric dimension value ID in INE's internal system |
| `T3_Variable` | Dimension name — identifies geographic level and indicator type |
| `Nombre` | Human-readable label for this dimension value |
| `Codigo` | **Machine-readable code — use this, not `Nombre`** |

**Geographic level** is identified by `T3_Variable`:

| `T3_Variable` | Level | `Codigo` format | Example |
|---------------|-------|-----------------|---------|
| `"Municipios"` | Municipality | 5-digit | `"01001"` |
| `"Distritos"` | Census district | 7-digit | `"0100101"` |
| `"Secciones"` | **Sección censal** | **10-digit** | `"0100101001"` |

Extract `cod_seccion` without regex:

```python
def is_seccion(entry: dict) -> bool:
    return any(m["T3_Variable"] == "Secciones" for m in entry["MetaData"])

def get_cod_seccion(entry: dict) -> str | None:
    for m in entry["MetaData"]:
        if m["T3_Variable"] == "Secciones":
            return m["Codigo"]
    return None
```

### `Data` array

Each element is one annual observation:

| Sub-field | Type | Description |
|-----------|------|-------------|
| `Fecha` | string | ISO-8601 timestamp (e.g. `"2023-01-01T00:00:00.000+01:00"`) |
| `T3_TipoDato` | string | Data quality: `"Definitivo"` = confirmed final value |
| `T3_Periodo` | string | Periodicity: `"A"` = annual |
| `Anyo` | int | Year (e.g. `2023`) — use this, not `Fecha`, for year filtering |
| `Valor` | float \| null | The value. `null` = statistically suppressed (cell too small to publish) |

### Coverage for table 37677 (Gini + P80/P20)

Verified May 2026:

| Level | Series count |
|-------|-------------|
| Municipal | 16,278 |
| Distritos | 21,034 |
| Secciones | **74,142** |
| **Total** | **111,454** |

~74k sección series = 2 indicators (Índice de Gini, P80/P20) × ~37k secciones.

---

## File sizes

### Raw sizes

| File | Size |
|------|------|
| 30824.csv | 352 MB |
| 30824.json | 513 MB |
| 30825.csv | 279 MB |
| 30825.json | 427 MB |
| 30826.csv | 694 MB |
| 30826.json | 914 MB |
| 30827.csv | 2,280 MB |
| 30827.json | 3,199 MB |
| 30828.csv | 1,463 MB |
| 30828.json | 2,797 MB |
| 30829.csv | 1,415 MB |
| 30829.json | 1,835 MB |
| 30830.csv | 4,644 MB |
| 30830.json | 4,471 MB |
| 30831.csv | 2,981 MB |
| 30831.json | 5,609 MB |
| 30832.csv | 381 MB |
| 30832.json | 582 MB |
| 37677.csv | 102 MB |
| 37677.json | 165 MB |
| **Total** | **~36.8 GB** |

### Compressed sizes (zstd -15, ~35–45x ratio)

These files compress exceptionally well due to highly repetitive text (municipality names, indicator labels repeated millions of times).

| Scope | Raw | Compressed (zstd -15) |
|-------|-----|-----------------------|
| CSV only | 15.3 GB | ~0.52 GB |
| JSON only | 21.5 GB | ~0.48 GB |
| **Both** | **36.8 GB** | **~1.0 GB** |

---

## S3 archive layout

```
s3://hsf-group-ai-spain-hvac/
└── ine-adrh/
    └── raw/
        ├── 30824.csv.zst
        ├── 30824.json.zst
        ├── 30825.csv.zst
        ├── 30825.json.zst
        ├── 30826.csv.zst
        ├── 30826.json.zst
        ├── 30827.csv.zst
        ├── 30827.json.zst
        ├── 30828.csv.zst
        ├── 30828.json.zst
        ├── 30829.csv.zst
        ├── 30829.json.zst
        ├── 30830.csv.zst
        ├── 30830.json.zst
        ├── 30831.csv.zst
        ├── 30831.json.zst
        ├── 30832.csv.zst
        ├── 30832.json.zst
        ├── 37677.csv.zst
        ├── 37677.json.zst
        └── tables_with_links.json      ← original download manifest
```

---

## Working with the archived files

### Install zstd

The `zstd` Python package is already a project dependency — no extra install needed:

```bash
poetry install   # installs zstd along with all other dependencies
```

The system `zstd` CLI binary is also required for command-line use:

```bash
# macOS
brew install zstd

# Ubuntu / Debian
sudo apt install zstd
```

### Decompress on the command line

```bash
# Download .zst from S3 then decompress to disk
aws s3 cp s3://hsf-group-ai-spain-hvac/ine-adrh/raw/30824.csv.zst . \
    --profile AWSAdministratorAccess-268271485741
zstd -d 30824.csv.zst                   # produces 30824.csv (352 MB)

# Decompress an already-downloaded .zst file
zstd -d 30824.csv.zst -o myfile.csv     # explicit output name
zstd -d --rm 30824.csv.zst              # decompress and delete the .zst

# Stream: decompress without writing to disk
zstd -dc 30824.csv.zst | head -5

# Stream directly from S3 (no local .zst file at all)
aws s3 cp s3://hsf-group-ai-spain-hvac/ine-adrh/raw/30824.csv.zst - \
    --profile AWSAdministratorAccess-268271485741 \
    | zstd -dc \
    | head -5
```

### Read into pandas (Python)

**Option A — `zstd` package (project dependency, recommended)**

```python
import io
import zstd
import boto3
import pandas as pd

s3 = boto3.client("s3")
BUCKET = "hsf-group-ai-spain-hvac"

def read_ine_csv(table_id: str) -> pd.DataFrame:
    """Download and decompress an INE CSV from S3 into a DataFrame."""
    obj = s3.get_object(Bucket=BUCKET, Key=f"ine-adrh/raw/{table_id}.csv.zst")
    raw = zstd.decompress(obj["Body"].read())
    return pd.read_csv(
        io.BytesIO(raw),
        sep=";",
        encoding="utf-8-sig",    # strips BOM
        decimal=",",              # European decimal separator
        thousands=".",
    )

df = read_ine_csv("30824")
```

**Option B — subprocess pipe (streams without loading full file into memory)**

Useful for the largest files (30830: 64 MB compressed → 4.6 GB decompressed).

```python
import pandas as pd
import subprocess

def read_ine_csv_pipe(table_id: str) -> pd.DataFrame:
    s3_uri = f"s3://hsf-group-ai-spain-hvac/ine-adrh/raw/{table_id}.csv.zst"
    s3_proc = subprocess.Popen(
        ["aws", "s3", "cp", s3_uri, "-",
         "--profile", "AWSAdministratorAccess-268271485741"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    decomp = subprocess.Popen(
        ["zstd", "-dc"],
        stdin=s3_proc.stdout, stdout=subprocess.PIPE,
    )
    s3_proc.stdout.close()
    return pd.read_csv(
        decomp.stdout,
        sep=";",
        encoding="utf-8-sig",
        decimal=",",
        thousands=".",
    )

df = read_ine_csv_pipe("30824")
```

**Option C — local `.zst` file already on disk**

```python
import io, zstd, pandas as pd

with open("30824.csv.zst", "rb") as fh:
    raw = zstd.decompress(fh.read())
df = pd.read_csv(io.BytesIO(raw), sep=";", encoding="utf-8-sig", decimal=",", thousands=".")
```

### Read the JSON format

```python
import json, io, zstd, boto3

s3 = boto3.client("s3")
obj = s3.get_object(Bucket="hsf-group-ai-spain-hvac",
                    Key="ine-adrh/raw/30824.json.zst")
data = json.loads(zstd.decompress(obj["Body"].read()))
# data is a list of series dicts, each with MetaData + Data arrays
```

### Parsing notes

| Issue | Detail |
|-------|--------|
| BOM | CSV files start with a UTF-8 BOM (`﻿`). Use `encoding="utf-8-sig"` in pandas or `open(..., encoding="utf-8-sig")`. |
| Decimal separator | European format: `,` for decimals, `.` for thousands. Pass `decimal=","` and `thousands="."` to `pd.read_csv`. |
| Missing values | `.` means statistically suppressed (cell too small to publish). Empty string means no data for that geo/year combination. Map both to `NaN`. |
| Sección code | The `Secciones` column contains `"0100101001 Alegría-Dulantzi sección 01001"`. Extract the 10-digit `cod_seccion` with `str.split().str[0]`. |

---

## Integrity verification

### Why ETag is not sufficient for large files

AWS S3 computes an ETag for every object. For files uploaded in a single part (<8 MB), the ETag equals the MD5 of the content. For multipart uploads (all files here except very small ones), the ETag is `MD5(MD5(part1) || MD5(part2) || ...) + "-N"` — a composite that cannot be recomputed without knowing the exact part boundaries. This makes ETag-based post-hoc verification impossible for large files.

**Verified:** `37677.csv.zst` (4.1 MB, single-part) — local MD5 `0334eae7...` matched S3 ETag exactly.

### Verification strategy

Three independent checks are implemented in `verify_ine_adrh_s3.sh`:

| Check | How | What it catches | Speed |
|-------|-----|-----------------|-------|
| **SIZE** | Re-compress locally with same zstd level, compare byte count with `s3api head-object ContentLength` | Truncated uploads, wrong file uploaded | ~2 min (re-compresses all files) |
| **CHECKSUM** | SHA256 of compressed stream computed locally at upload time, stored in S3 object metadata (`x-amz-meta-sha256`) and as S3 checksum attribute (`--checksum-algorithm SHA256`) | Bit-flip corruption in transit or at rest | ~15 sec (metadata lookup only) |
| **ZSTD** | Stream each `.zst` from S3 through `zstd -t` (test mode, no decompression to disk) | Corrupt zstd frames, truncated archives | ~10 min (streams ~1 GB) |

### How checksums are stored

Each upload in `compress_and_upload_ine_adrh.sh`:
1. Compresses to a temp file
2. Computes `sha256sum` of the compressed file
3. Appends `<hash>  <filename>.zst` to `ine_adrh_checksums.sha256` (local manifest)
4. Uploads with `--checksum-algorithm SHA256` so S3 independently verifies on receipt and stores it
5. Embeds `sha256=<hash>` in S3 object metadata for retrieval without re-download

### Running verification

```bash
# Quick size check (re-compresses locally, ~2 min)
bash verify_ine_adrh_s3.sh size

# Checksum manifest check (~15 sec, requires ine_adrh_checksums.sha256)
bash verify_ine_adrh_s3.sh checksum

# Full zstd frame integrity test (streams from S3, ~10 min)
bash verify_ine_adrh_s3.sh zstd

# All three checks
bash verify_ine_adrh_s3.sh
```

Example output:
```
[15:43:00] === SIZE CHECK ===
  OK  30824.csv.zst — size 15914722 bytes
  OK  30824.json.zst — size 12474368 bytes
  ...
[15:45:00] === RESULT: 20 passed, 0 failed ===
```

### Note on files uploaded before checksum support

Files uploaded during the initial run of the upload script (before the `--checksum-algorithm` flag was added) do not have the SHA256 checksum attribute — the checksum check will fall back to size-only for those. The ZSTD frame check works for all files regardless.

---

## How the data was originally obtained

### The discovery problem

INE's table pages (`https://www.ine.es/jaxiT3/dlgExport.htm?t=<ID>&L=0`) are JavaScript-rendered. The download buttons and underlying API URLs are injected dynamically — `curl -I` on the export page returns HTML, not a direct download link. There is no public index of direct download URLs.

The `wstempus` JSON API URLs (e.g. `https://servicios.ine.es/wstempus/jsCache/es/DATOS_TABLA/30824?tip=AM&`) do work directly with `wget`/`curl` once you know them, but discovering them requires visiting the dlgExport page in a real browser.

### Scripts

Four scripts handle the full workflow. Run in order:

| Script | Purpose | Requires browser |
|--------|---------|-----------------|
| `ine_inspect_page.py` | One-off diagnostic — prints all links/buttons found on a dlgExport page. Used to reverse-engineer the page structure. | Yes (playwright) |
| `ine_find_links.py` | Visits all 10 dlgExport pages, extracts JSON API URL, xlsx URL, and CSV URL for each. Saves to `tables_with_links.json`. | Yes (playwright) |
| `ine_verify_links.py` | Downloads the first 1 MB of each JSON API URL and confirms it returns valid JSON. No full download. | No |
| `ine_download.py` | Streams each JSON file from its API URL to disk. Skips already-downloaded files unless `--all` is passed. | No |

All scripts use the `playwright` package (already in `pyproject.toml`) with a persistent Chromium profile at `~/.openclaw/browser/openclaw/user-data`.

### Alternative access methods (fallback if direct links break)

If the direct `wget`/`ine_download.py` pipeline stops working (e.g. INE restructures their URLs), two programmatic APIs can serve as alternatives.

#### 1. `censosine21` Python package

A third-party wrapper around the INE Census 2021 SOAP/REST interface. Gives clean access to aggregate Census 2021 data down to **municipality level** (not sección censal — that granularity is only available via the direct file download).

```bash
poetry add censosine21   # or: pip install censosine21
```

```python
from censosine21 import CensosINE21
import pandas as pd

client = CensosINE21()

# Signature: .post(table, metric, variables, language)
# Tables:    "per.ppal" = persons,  "hog" = households
# Metrics:   "SPERSONAS" = person count,  "SHOGARES" = household count
# Variables (geographic levels):
#   "ID_RESIDENCIA_N1" = CCAA (17 regions)
#   "ID_RESIDENCIA_N2" = province (52)
#   "ID_RESIDENCIA_N3" = municipality (8,131)  ← finest grain available
# Other variables: "ID_SEXO", "ID_NACIONALIDAD_N1"

# Population by province and sex
client.post("per.ppal", "SPERSONAS", ["ID_RESIDENCIA_N2", "ID_SEXO"], "EN")
df_province = pd.DataFrame(client.data)

# Households by municipality
client.post("hog", "SHOGARES", ["ID_RESIDENCIA_N3"], "EN")
df_municipalities = pd.DataFrame(client.data)

# Population by region and nationality
client.post("per.ppal", "SPERSONAS", ["ID_RESIDENCIA_N1", "ID_NACIONALIDAD_N1"], "EN")
df_nationality = pd.DataFrame(client.data)
```

**Limitation:** municipality is the finest geographic level. Sección-censal data is not accessible through this package.

#### 2. INE TEMPUS API

The underlying REST API powering the `wstempus` URLs used by `ine_download.py`. Can be queried directly to discover and fetch any INE table — including ADRH and Census tables — without needing a browser.

Base URL: `https://servicios.ine.es/wstempus/js/EN`

```python
import requests
import pandas as pd

TEMPUS = "https://servicios.ine.es/wstempus/js/EN"
headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}

# List all INE statistical operations
ops = requests.get(f"{TEMPUS}/operaciones", headers=headers).json()
# Operation ID 8 = Population and Housing Censuses (Censo 2021)
# Operation ID 30 = ADRH (Atlas de Distribución de Renta de los Hogares)

# List tables within an operation
tables = requests.get(f"{TEMPUS}/operacion/30/tablas", headers=headers).json()

# Fetch data for a specific table (e.g. ADRH table 30824)
# This is the same endpoint used by ine_download.py
url = "https://servicios.ine.es/wstempus/jsCache/es/DATOS_TABLA/30824?tip=AM&"
data = requests.get(url, headers=headers).json()
# Returns list of series, each with MetaData + Data arrays (see JSON format docs above)

# Fetch a single named series by its COD field
series = requests.get(f"{TEMPUS}/serie/ADRH7225950", headers=headers).json()
```

The `jsCache` variant (`/wstempus/jsCache/es/DATOS_TABLA/{id}?tip=AM&`) returns the full table in one response and is faster due to server-side caching — prefer it over `/js/` for bulk downloads.

#### 3. INE OpenAPI (newer, paginated)

A more recent REST interface with pagination support. Still maturing as of 2025.

Base URL: `https://www.ine.es/OpenAPI`

```python
# List operations
requests.get("https://www.ine.es/OpenAPI/operaciones", params={"page": 1, "limit": 500}).json()

# Tables for an operation
requests.get("https://www.ine.es/OpenAPI/operaciones/30/tablas", params={"page": 1}).json()

# Table data (paginated)
requests.get("https://www.ine.es/OpenAPI/tablas/30824/data", params={"page": 1}).json()
```

### Step-by-step

```bash
# 1. Discover all download URLs (browser required)
poetry run python ine_find_links.py
# → writes ~/.openclaw/workspace/downloads/ine_5650/tables_with_links.json

# 2. Verify all JSON API links are alive (~10 MB total, no full download)
poetry run python ine_verify_links.py

# 3a. Download JSON files (no browser, streams from API)
poetry run python ine_download.py           # skip already-downloaded
poetry run python ine_download.py 30829     # single table
poetry run python ine_download.py --all     # force re-download all

# 3b. Download CSV files directly (no browser needed, wget)
for id in 30824 30825 30826 30827 30828 30829 30830 30831 30832 37677; do
  wget -q --show-progress \
    "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/${id}.csv" \
    -O ~/.openclaw/workspace/downloads/ine_5650/${id}.csv
done
```

### Monitor download progress

```bash
watch -n 5 'ls -lh ~/.openclaw/workspace/downloads/ine_5650/'
```

### Encoding note

The INE server declares `Content-Type: text/plain;charset=ISO-8859-15` for CSV files. However, the files as downloaded are **UTF-8 with BOM** (`\xef\xbb\xbf` prefix). Read with `encoding="utf-8-sig"` in Python (the `-sig` variant strips the BOM automatically).

---

## HVAC feature extraction plan

For the Spain HVAC propensity model, the relevant extract is:

- **Geographic level:** sección censal only
- **Year:** 2023 (latest), 2022 as fallback for missing secciones
- **Tables to use:** 30824, 37677, 30832, 30825, 30829 (Total-sex rows only for 30829)
- **Output:** wide-format parquet keyed on `cod_seccion` (10-digit code extracted from the Secciones column)

See `eda_ine_adrh.ipynb` for extraction logic and feature selection rationale.

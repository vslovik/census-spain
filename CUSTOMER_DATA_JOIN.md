# Joining Customer Data with Census & ADRH Features

How to enrich HomeServe customer records with external demographic, income, and housing data at sección censal level.

---

## Why this matters

The Census 2021 and ADRH datasets provide ~70 variables per sección censal (census tract) — income, age structure, homeownership rate, pension share, household composition — that are strong predictors of HVAC demand. Linking these to customer records turns every policy into a feature-rich row for propensity modelling, without needing to survey customers individually.

---

## Geographic hierarchy

Spain's administrative geography, from coarsest to finest:

```
País (1)
  └── CCAA (17 + Ceuta + Melilla)
        └── Provincia (52)
              └── Municipio (~8,131)
                    └── Distrito (~10,500)
                          └── Sección censal (~36,000)   ← target resolution
```

A sección censal typically contains 1,000–2,500 inhabitants. At this resolution the census and ADRH features are specific enough to be meaningful for propensity scoring.

---

## What customer information is needed

| Customer field | Used for | Notes |
|---|---|---|
| **Service address** (street + number + city + province + CP) | Geocoding → lat/lon → spatial join | Best path — gives exact sección censal |
| **Postal code (CP)** | Fallback: CP → municipio | ~11,000 CPs vs ~36,000 secciones — CPs don't align with census boundaries |
| **Municipio name + province** | Fallback: fuzzy match to INE municipio code | Loses sección-level resolution |

**The minimum required for the full feature set is a geocodeable address** — i.e. the service address on the policy, which HomeServe already holds.

---

## Join options by data quality

### Option A — Full address (recommended)

```
Customer address
      │
      ▼  (Cartociudad — Spain's official geocoder, IGN)
  lat / lon  +  municipio code
      │
      ▼  (GeoPandas spatial join on INE sección censal shapefile)
  cod_seccion (10 chars)
      │
      ├──▶  censo2021_secciones.parquet        (demographics, housing, pensions)
      └──▶  adrh_secciones_latest.parquet      (income, inequality, income sources)
```

**Result:** ~70 features per customer at sección censal resolution.

**Recommended geocoder — Cartociudad (IGN)**

Cartociudad is Spain's official national geocoder, maintained by the Instituto Geográfico
Nacional (IGN) — the Spanish equivalent of France's BAN (Base Adresse Nationale). It is
free, requires no API key, and is the authoritative source for Spanish address geocoding.

| | Spain — Cartociudad | France — BAN |
|---|---|---|
| Operator | IGN (Instituto Geográfico Nacional) | IGN France + La Poste |
| API endpoint | `https://www.cartociudad.es/geocoder/api/geocoder/findJsonp` | `https://api-adresse.data.gouv.fr/csv/` |
| Returns | lat/lon + municipio code | lat/lon + commune code (and IRIS directly for some cases) |
| Sección censal | Not returned — spatial join always required | N/A (IRIS via spatial join) |
| Batch support | Via iterative calls or QGIS plugin | Native `/csv/` bulk endpoint (up to 50k rows) |
| Cost | Free, no key | Free, no key |

**Key difference from BAN:** France's BAN bulk endpoint natively returns the IRIS/commune
code, reducing the need for a spatial join in many cases. Cartociudad always returns only
lat/lon and municipio — the spatial join against the INE sección shapefile is always required
to reach sección censal resolution.

**Cartociudad usage (single address):**
```python
import requests

def cartociudad_geocode(address: str, municipio: str = "", provincia: str = ""):
    params = {
        "q": f"{address}, {municipio}, {provincia}",
        "limit": 1,
        "no_process": False,
    }
    resp = requests.get(
        "https://www.cartociudad.es/geocoder/api/geocoder/findJsonp",
        params=params, timeout=10,
    )
    # Response is JSONP — strip callback wrapper
    text = resp.text.strip()
    if text.startswith("callback("):
        text = text[9:-1]
    import json
    result = json.loads(text)
    if result and "lat" in result:
        return result["lat"], result["lng"], result.get("municipality", ""), result.get("id", "")
    return None, None, None, None
```

Fallback geocoders: `geopy` Nominatim (free, lower accuracy for Spanish addresses) or
Google Maps Geocoding API (paid, highest accuracy, requires key).

**Tools needed:**
- Geocoding: Cartociudad (recommended), Nominatim, or Google Maps Geocoding API
- Spatial join: `geopandas` + INE sección shapefile (see below)
- Join key: `CUSEC` in shapefile = `cod_seccion` in parquets (both 10 chars, zero-padded)

### Option B — Postal code only (fallback)

```
Postal code (CP)
      │
      ▼  (CP → municipio crosswalk)
  cod_municipio (5 chars)
      │
      └──▶  adrh_municipios_latest.parquet    (29 income/demographic indicators at municipio level)
```

**Result:** ~29 features per customer at municipio level. Loses within-municipio variation — adequate for rural areas where one CP ≈ one municipio, but loses signal in cities where income varies dramatically by neighbourhood.

**Crosswalk:** INE publishes a CP → municipio correspondence table. Postal codes are postal routes — one CP can span multiple municipios and one municipio can have multiple CPs.

### Option C — Province only (last resort)

Aggregate `adrh_secciones_latest.parquet` or `censo2021_secciones.parquet` to province level and join on `cod_provincia` (first 2 chars of the customer's province code). Useful only as a climate-zone feature (temperature by province), not for socioeconomic targeting.

---

## INE sección censal shapefile

The shapefile defining the geographic boundaries of all ~36,000 secciones censales is published by INE:

- **INE cartography portal:** Censos de Población y Viviendas 2021 → Cartografía
- **S3 (check):** `s3://hsf-group-ai-spain-hvac/ine-census-2021/dictionaries/` — may already contain shapefiles
- **Join key in shapefile:** `CUSEC` (10-char string, matches `cod_seccion` in all our parquets)
- **Format:** SHP or GeoJSON; coordinate system ETRS89 / UTM zone 30N (EPSG:25830)

---

## Implementation sketch

```python
import geopandas as gpd
import pandas as pd
import requests, json

# 1. Geocode customer addresses via Cartociudad (Spain's official IGN geocoder)
def cartociudad_geocode(address: str) -> tuple:
    try:
        resp = requests.get(
            "https://www.cartociudad.es/geocoder/api/geocoder/findJsonp",
            params={"q": address, "limit": 1},
            timeout=10,
        )
        text = resp.text.strip()
        if text.startswith("callback("):
            text = text[9:-1]
        result = json.loads(text)
        if result and "lat" in result:
            return result["lat"], result["lng"]
    except Exception:
        pass
    return None, None

customers["lat"], customers["lon"] = zip(*customers["full_address"].map(cartociudad_geocode))

# 2. Load INE sección shapefile
secciones = gpd.read_file("data/input/ine_census_2021/secciones_censales_2021.shp")
secciones = secciones.to_crs("EPSG:4326")   # reproject to WGS84 for lat/lon join

# 3. Convert customers to GeoDataFrame and spatial join
gdf = gpd.GeoDataFrame(
    customers,
    geometry=gpd.points_from_xy(customers["lon"], customers["lat"]),
    crs="EPSG:4326",
)
customers_geo = gpd.sjoin(gdf, secciones[["CUSEC", "geometry"]], how="left", predicate="within")
customers_geo = customers_geo.rename(columns={"CUSEC": "cod_seccion"})

# 4. Merge census and ADRH features
censo  = pd.read_parquet("data/generated/ineatlas/censo2021_secciones.parquet")
adrh   = pd.read_parquet("data/generated/adrh/adrh_secciones_latest.parquet")

enriched = (
    customers_geo
    .merge(censo,  on="cod_seccion", how="left")
    .merge(adrh[["cod_seccion","renta_neta_media_por_hogar","indice_de_gini",
                  "fuente_de_ingreso_pensiones","porcentaje_de_poblacion_de_65_y_mas_anos"]],
           on="cod_seccion", how="left")
)
```

---

## Features available after join

After a successful sección-level join, each customer row gains:

**From `censo2021_secciones.parquet` (Census 2021):**
- `edad_media`, `pct_mayores_64` — age profile of the neighbourhood
- `pct_pension_jubilacion` — share of retirement pensioners (high = elderly = high heating demand)
- `tasa_paro`, `tasa_empleo` — local employment context
- `pct_propiedad` (derived) — homeownership rate (owners invest in HVAC; renters don't)
- `viviendas_no_principales` — second-home density (seasonal demand signal)
- `total_hogares`, `hogares_1_persona` — household size distribution

**From `adrh_secciones_latest.parquet` (ADRH income):**
- `renta_neta_media_por_hogar` — net household income (affordability)
- `indice_de_gini` — income inequality (high Gini = polarised market, needs segmentation)
- `fuente_de_ingreso_pensiones` — pension as % of income (corroborates census pension signal)
- `fuente_de_ingreso_salario` — salary share (working-age households)
- `porcentaje_de_poblacion_de_65_y_mas_anos` — % over 65 (from ADRH demographics)

**Climate (from temperature reference in `eda_censo2021.ipynb`):**
- `mean_temp_c` — mean annual temperature at province level (heating vs AC demand orientation)

---

## Match rate expectations

Based on the parquet coverage:
- `adrh_secciones_latest.parquet`: 37,034 secciones (~99.9% of Spain)
- `censo2021_secciones.parquet`: 36,333 secciones (~97.9% of Spain)

A well-geocoded address should match in >95% of cases. Common failure modes:
- **Address not found by geocoder** — typos, non-standard formatting, rural addresses
- **Point falls outside any polygon** — coordinates on a road/border between secciones (use `predicate="nearest"` as fallback)
- **Basque Country pension data** — `fuente_de_ingreso_pensiones` is NaN for provinces 01/20/48 (Álava, Gipuzkoa, Bizkaia) due to INE suppression; use `pct_pension_jubilacion` from Census 2021 as proxy

---

## Privacy note

The join is performed at **aggregate level** — the census and ADRH data describe the neighbourhood, not the individual customer. No personal data is sent to any geocoding API beyond the service address (which HomeServe already processes for operations). The enriched features represent area-level statistics and do not constitute personal data under GDPR.
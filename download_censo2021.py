"""
Download and process the Censo de Población y Viviendas 2021
Indicator file for secciones censales — single file, all Spain.

Source: https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177108&menu=resultados
Direct: https://www.ine.es/censos2021/C2021_Indicadores.csv

Column codes verified against:
  data/input/ine_census_2021/indicadores_seccen_c2021.xlsx

NOTE: The raw CSV uses comma as separator (not semicolon) and has NO CUSEC column.
Geographic key (cod_seccion) is constructed from cpro + cmun + dist + secc.
"""

import requests
import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path("data/generated/ineatlas")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.ine.es/",
}

# ── Download ──────────────────────────────────────────────────────────────────
def download(url: str, dest: Path) -> Path:
    if dest.exists():
        print(f"Already downloaded: {dest}")
        return dest

    print(f"Downloading: {url}")
    with requests.get(url, headers=HEADERS, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=512 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = f" ({downloaded/total*100:.0f}%)" if total else ""
                    sys.stdout.write(f"\r  {downloaded/1e6:.1f} MB{pct}")
                    sys.stdout.flush()
    print(f"\n  Saved: {dest}  ({dest.stat().st_size/1e6:.1f} MB)")
    return dest


# ── Load ──────────────────────────────────────────────────────────────────────
def load_censo(path: Path) -> pd.DataFrame:
    # Comma-delimited (NOT semicolon); encoding utf-8-sig strips BOM
    df = pd.read_csv(path, sep=",", encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    print(f"\nLoaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    return df


# ── Indicator mapping (verified against indicadores_seccen_c2021.xlsx) ────────
# All t-codes map to proportions (0–1) except t1_1 (absolute count) and
# t18_1 / t19_1 / t19_2 / t20_1–t20_3 / t21_1 / t22_1–t22_5 (absolute counts).
INDICATOR_MAP = {
    # Population
    "t1_1":  "poblacion_total",

    # Sex
    "t2_1":  "pct_mujeres",
    "t2_2":  "pct_hombres",

    # Age
    "t3_1":  "edad_media",
    "t4_1":  "pct_menores_16",
    "t4_2":  "pct_16_64",
    "t4_3":  "pct_mayores_64",

    # Nationality / origin
    "t5_1":  "pct_extranjeros",
    "t6_1":  "pct_nacidos_extranjero",

    # Education (in progress / stock)
    "t7_1":  "pct_cursando_estudios_superiores",   # enrolled in HE (escur 08-12)
    "t8_1":  "pct_cursando_universidad",            # enrolled in university (escur 09-12)
    "t9_1":  "pct_estudios_superiores_completados", # completed HE

    # Labour market
    "t10_1": "tasa_paro",       # % parados / activos
    "t11_1": "tasa_empleo",     # % ocupados / pob 16+
    "t12_1": "tasa_actividad",  # % activos / pob 16+

    # Economic inactivity types
    "t13_1": "pct_pension_invalidez",   # disability pension / pob 16+
    "t14_1": "pct_pension_jubilacion",  # retirement pension / pob 16+ — KEY HVAC signal
    "t15_1": "pct_otra_inactividad",    # other inactivity / pob 16+ (NOT heating system)
    "t16_1": "pct_estudiantes",         # students / pob 16+ (NOT air conditioning)

    # Marital status
    "t17_1": "pct_soltero",
    "t17_2": "pct_casado",
    "t17_3": "pct_viudo",
    "t17_4": "pct_estado_civil_desconocido",
    "t17_5": "pct_separado_divorciado",

    # Dwellings (absolute counts)
    "t18_1": "total_viviendas",
    "t19_1": "viviendas_principales",
    "t19_2": "viviendas_no_principales",  # vacancy / second homes signal

    # Housing tenure (absolute counts)
    "t20_1": "viviendas_en_propiedad",    # KEY for HVAC — owner-occupied
    "t20_2": "viviendas_en_alquiler",
    "t20_3": "viviendas_otro_regimen",

    # Households (absolute counts)
    "t21_1": "total_hogares",
    "t22_1": "hogares_1_persona",
    "t22_2": "hogares_2_personas",
    "t22_3": "hogares_3_personas",
    "t22_4": "hogares_4_personas",
    "t22_5": "hogares_5_mas_personas",
}


def select_and_rename(df: pd.DataFrame) -> pd.DataFrame:
    available = {k: v for k, v in INDICATOR_MAP.items() if k in df.columns}
    missing   = [k for k in INDICATOR_MAP if k not in df.columns]
    if missing:
        print(f"\nWarning: {len(missing)} expected columns not found: {missing}")

    # Construct cod_seccion from geographic components (no CUSEC in raw file)
    geo_cols = ["ccaa", "cpro", "cmun", "dist", "secc"]
    for col in geo_cols:
        if col not in df.columns:
            raise ValueError(f"Missing geographic column: {col}")

    selected = df[geo_cols + list(available.keys())].copy()
    selected.rename(columns=available, inplace=True)

    selected["cod_seccion"] = (
        selected["cpro"].str.zfill(2)
        + selected["cmun"].str.zfill(3)
        + selected["dist"].str.zfill(2)
        + selected["secc"].str.zfill(3)
    )

    # Convert numeric columns
    numeric_cols = [v for v in available.values()]
    for col in numeric_cols:
        selected[col] = (
            selected[col]
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    col_order = ["cod_seccion", "ccaa", "cpro", "cmun", "dist", "secc"] + list(available.values())
    return selected[col_order]


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw_path = Path("data/input/ine_census_2021/C2021_Indicadores.csv")

    if not raw_path.exists():
        raw_path = download(
            "https://www.ine.es/censos2021/C2021_Indicadores.csv",
            raw_path,
        )

    df = load_censo(raw_path)
    selected = select_and_rename(df)
    print(f"\nSelected shape: {selected.shape}")
    print(f"Columns: {list(selected.columns)}")
    print(selected.head(3).to_string())

    out = OUTPUT_DIR / "censo2021_secciones_from_ine.parquet"
    selected.to_parquet(out, index=False)
    print(f"\nSaved: {out}  ({out.stat().st_size/1e6:.1f} MB)")

"""
Download and process the Censo de Población y Viviendas 2021
Indicator file for secciones censales — single file, all Spain.

Source: https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177108&menu=resultados
Direct: https://www.ine.es/censos2021/C2021_Indicadores.csv

Keeps only the indicators relevant for HVAC and solar propensity models:
  - Ownership rate (% viviendas en propiedad)
  - Building age distribution
  - Building type (apartment vs house)
  - Household size
  - Population structure
"""

import requests
import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path(".")

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


# ── Load & inspect ────────────────────────────────────────────────────────────
def load_censo(path: Path) -> pd.DataFrame:
    # The file uses semicolon separator and has a header row + data
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    print(f"\nLoaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"First columns: {list(df.columns[:8])}")
    print(f"\nAll column names:")
    for i, c in enumerate(df.columns):
        print(f"  [{i:03d}] {c}")
    return df


# ── Select relevant indicators ────────────────────────────────────────────────
# These are the known column name patterns in C2021_Indicadores.csv
# Exact names confirmed from INE documentation

INDICATOR_MAP = {
    # Geography
    "CUSEC":            "cod_seccion",       # 10-digit section code (key join field)
    "NMUN":             "municipio",
    "NPRO":             "provincia",
    "NCA":              "ccaa",

    # Population
    "t1_1":             "poblacion_total",
    "t1_2":             "poblacion_hombres",
    "t1_3":             "poblacion_mujeres",

    # Age structure
    "t2_1":             "pct_menores_16",
    "t2_2":             "pct_16_64",
    "t2_3":             "pct_65_mas",
    "t2_4":             "edad_media",

    # Household
    "t6_1":             "n_hogares",
    "t6_2":             "tamano_medio_hogar",
    "t6_3":             "pct_hogares_unipersonales",

    # Housing tenure — KEY for both solar and HVAC
    "t8_1":             "n_viviendas_principales",
    "t8_2":             "pct_vivienda_propiedad",       # % owned (not renting)
    "t8_3":             "pct_vivienda_alquiler",        # % renting
    "t8_4":             "pct_vivienda_otra_forma",      # % other tenure

    # Building type — KEY for solar (houses > flats) and HVAC sizing
    "t9_1":             "pct_edificio_unifamiliar",     # detached/semi-detached
    "t9_2":             "pct_edificio_bloque",          # apartment block

    # Building age — KEY for replacement demand (old = no system or outdated)
    "t10_1":            "pct_antes_1900",
    "t10_2":            "pct_1900_1940",
    "t10_3":            "pct_1941_1960",
    "t10_4":            "pct_1961_1970",
    "t10_5":            "pct_1971_1980",
    "t10_6":            "pct_1981_1990",
    "t10_7":            "pct_1991_2000",
    "t10_8":            "pct_2001_2010",
    "t10_9":            "pct_despues_2010",

    # Housing surface — proxy for ticket size
    "t11_1":            "pct_menos_30m2",
    "t11_2":            "pct_30_45m2",
    "t11_3":            "pct_45_60m2",
    "t11_4":            "pct_60_75m2",
    "t11_5":            "pct_75_90m2",
    "t11_6":            "pct_90_105m2",
    "t11_7":            "pct_105_120m2",
    "t11_8":            "pct_mas_120m2",

    # Education (proxy for income stability)
    "t4_1":             "pct_sin_estudios",
    "t4_2":             "pct_estudios_primarios",
    "t4_3":             "pct_estudios_secundarios",
    "t4_4":             "pct_estudios_superiores",

    # Employment
    "t5_1":             "pct_ocupados",
    "t5_2":             "pct_parados",
    "t5_3":             "pct_inactivos",

    # Nationality (affects income attribution in ADRH)
    "t3_1":             "pct_espanoles",
    "t3_2":             "pct_extranjeros",
}


def select_and_rename(df: pd.DataFrame) -> pd.DataFrame:
    # Find which expected columns actually exist
    available  = {k: v for k, v in INDICATOR_MAP.items() if k in df.columns}
    missing    = [k for k in INDICATOR_MAP if k not in df.columns]

    if missing:
        print(f"\nWarning: {len(missing)} expected columns not found (may have different names):")
        print(f"  {missing}")
        print("\nSearching for similar columns...")
        # Try to find close matches
        for m in missing[:5]:
            close = [c for c in df.columns if m.lower() in c.lower() or c.lower().startswith(m[:3].lower())]
            if close:
                print(f"  '{m}' → possible matches: {close[:3]}")

    selected = df[list(available.keys())].copy()
    selected.rename(columns=available, inplace=True)

    # Convert numeric columns
    for col in selected.columns:
        if col not in ["cod_seccion", "municipio", "provincia", "ccaa"]:
            selected[col] = (
                selected[col]
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
            )

    # Derived features useful for the model
    if "pct_1941_1960" in selected.columns and "pct_1961_1970" in selected.columns:
        selected["pct_edificios_pre1980"] = (
            selected[["pct_antes_1900","pct_1900_1940","pct_1941_1960",
                       "pct_1961_1970","pct_1971_1980"]]
            .sum(axis=1, skipna=True)
        )

    return selected


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Download
    raw = download(
        "https://www.ine.es/censos2021/C2021_Indicadores.csv",
        OUTPUT_DIR / "censo2021_indicadores_raw.csv",
    )

    # 2. Load and inspect all columns
    df = load_censo(raw)

    # 3. Select relevant indicators
    selected = select_and_rename(df)
    print(f"\nSelected shape: {selected.shape}")
    print(f"Columns: {list(selected.columns)}")
    print(selected.head(3).to_string())

    # 4. Save
    selected.to_parquet(OUTPUT_DIR / "censo2021_secciones.parquet", index=False)
    selected.to_csv(OUTPUT_DIR / "censo2021_secciones.csv", index=False)
    print(f"\nSaved: censo2021_secciones.parquet  ({selected.memory_usage(deep=True).sum()/1e6:.1f} MB)")
    print(f"Saved: censo2021_secciones.csv")

    # 5. Merge with ADRH 2023 if available
    adrh_path = OUTPUT_DIR / "adrh_secciones_2023.parquet"
    if adrh_path.exists():
        print("\nMerging with ADRH 2023...")
        adrh  = pd.read_parquet(adrh_path)
        # Align keys: ADRH cod_seccion is already 10-digit string
        merged = adrh.merge(
            selected.rename(columns={"cod_seccion": "cod_seccion"}),
            on="cod_seccion",
            how="left",
            suffixes=("_adrh", "_censo"),
        )
        merged.to_parquet(OUTPUT_DIR / "features_secciones_2023.parquet", index=False)
        merged.to_csv(OUTPUT_DIR / "features_secciones_2023.csv", index=False)
        print(f"Merged shape: {merged.shape}")
        print(f"Saved: features_secciones_2023.parquet  ← use this as model input")
    else:
        print("\nNote: run adrh_secciones.py first to generate adrh_secciones_2023.parquet")
        print("Then re-run this script for the auto-merge.")

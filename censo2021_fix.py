"""
Fix and process the Censo 2021 secciones censales indicator file.

Issues fixed:
  1. Separator is comma, not semicolon
  2. Geography must be built from component columns: cpro + cmun + dist + secc
  3. Column names are t-codes — read the indicator dictionary to map them

Run this ONCE first to inspect columns and values:
    python censo2021_fix.py --inspect

Then run normally to process:
    python censo2021_fix.py
"""

import pandas as pd
from pathlib import Path
import sys

RAW_CSV   = Path("censo2021_indicadores_raw.csv")
DICT_XLSX = Path("censo2021_indicadores_dict.xlsx")   # download from INE if available
OUTPUT_DIR = Path(".")

# ── Step 1: Read with correct separator ──────────────────────────────────────
def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, sep=",", encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    print(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ── Step 2: Print column sample so you can see what each t-code contains ─────
def inspect(df: pd.DataFrame):
    print("\n=== COLUMN INSPECTION ===")
    print(f"{'Column':<12} {'Sample value 1':<20} {'Sample value 2':<20} {'Sample value 3'}")
    print("-" * 80)
    for col in df.columns:
        samples = df[col].dropna().head(3).tolist()
        s1 = str(samples[0])[:18] if len(samples) > 0 else ""
        s2 = str(samples[1])[:18] if len(samples) > 1 else ""
        s3 = str(samples[2])[:18] if len(samples) > 2 else ""
        print(f"{col:<12} {s1:<20} {s2:<20} {s3}")


# ── Step 3: Try to read the indicator dictionary XLSX ────────────────────────
def load_dict() -> dict:
    """
    The INE indicator dictionary XLSX maps t-codes to descriptions.
    Download it from:
    https://www.ine.es/censos2021/indicadores_seccen_c2021.xlsx
    Save as: censo2021_indicadores_dict.xlsx
    """
    if not DICT_XLSX.exists():
        print(f"\nWarning: {DICT_XLSX} not found.")
        print("Download it from: https://www.ine.es/censos2021/indicadores_seccen_c2021.xlsx")
        print("Save as: censo2021_indicadores_dict.xlsx")
        print("Then re-run. Proceeding with best-guess mapping.\n")
        return {}

    try:
        ddf = pd.read_excel(DICT_XLSX, dtype=str)
        print(f"\nDictionary loaded: {ddf.shape}")
        print(ddf.head(10).to_string())
        # Try to build code→description map
        # Typical structure: first col = code, second = description
        code_col = ddf.columns[0]
        desc_col = ddf.columns[1] if len(ddf.columns) > 1 else None
        if desc_col:
            mapping = dict(zip(ddf[code_col].str.strip(), ddf[desc_col].str.strip()))
            return mapping
    except Exception as e:
        print(f"Could not read dictionary: {e}")
    return {}


# ── Step 4: Known t-code mapping (best guess from INE documentation) ─────────
# Based on the Censo 2021 indicator file structure.
# Run --inspect first to verify these match your actual data values.

TCODE_MAP = {
    # Geography (component columns — will be combined into cod_seccion)
    "ccaa":   "ccaa",
    "cpro":   "cpro",
    "cmun":   "cmun",
    "dist":   "dist",
    "secc":   "secc",

    # Population
    "t1_1":   "poblacion_total",

    # Age
    "t2_1":   "edad_media",
    "t2_2":   "pct_menores_18",

    # Nationality
    "t3_1":   "pct_extranjeros",

    # Education
    "t4_1":   "pct_sin_estudios",
    "t4_2":   "pct_estudios_primarios",
    "t4_3":   "pct_estudios_superiores",

    # Activity / Employment
    "t5_1":   "tasa_paro",

    # Households
    "t6_1":   "n_hogares",

    # Household size
    "t7_1":   "tamano_medio_hogar",

    # Housing tenure — KEY for solar & HVAC
    "t8_1":   "pct_vivienda_propiedad",

    # Housing surface (m²)
    "t9_1":   "superficie_media_m2",

    # Building age — KEY for replacement demand
    "t10_1":  "pct_edificios_anterior_1900",   # verify with --inspect

    # Other housing/building indicators (verify with --inspect)
    "t11_1":  "t11_1",
    "t12_1":  "t12_1",
    "t13_1":  "t13_1",
    "t14_1":  "t14_1",
    "t15_1":  "t15_1",
    "t16_1":  "t16_1",

    # Building type breakdown
    "t17_1":  "t17_1",
    "t17_2":  "t17_2",
    "t17_3":  "t17_3",
    "t17_4":  "t17_4",
    "t17_5":  "t17_5",

    "t18_1":  "t18_1",
    "t19_1":  "t19_1",
    "t19_2":  "t19_2",
    "t20_1":  "t20_1",
    "t20_2":  "t20_2",
    "t20_3":  "t20_3",
    "t21_1":  "t21_1",
    "t22_1":  "t22_1",
    "t22_2":  "t22_2",
    "t22_3":  "t22_3",
    "t22_4":  "t22_4",
    "t22_5":  "t22_5",
}


# ── Step 5: Process ───────────────────────────────────────────────────────────
def process(df: pd.DataFrame, dict_map: dict) -> pd.DataFrame:
    # Build 10-digit sección censal code: cpro(2) + cmun(3) + dist(2) + secc(3)
    df["cod_seccion"] = (
        df["cpro"].str.zfill(2) +
        df["cmun"].str.zfill(3) +
        df["dist"].str.zfill(2) +
        df["secc"].str.zfill(3)
    )
    df["cod_provincia"] = df["cpro"].str.zfill(2)
    df["cod_municipio"] = df["cpro"].str.zfill(2) + df["cmun"].str.zfill(3)

    # Rename t-codes using dict first, then fallback to TCODE_MAP
    rename = {}
    for col in df.columns:
        if col in dict_map:
            rename[col] = dict_map[col].lower().replace(" ", "_")[:40]
        elif col in TCODE_MAP:
            rename[col] = TCODE_MAP[col]

    df = df.rename(columns=rename)

    # Convert all t-code columns to numeric
    skip = {"ccaa", "cpro", "cmun", "dist", "secc", "cod_seccion", "cod_provincia", "cod_municipio"}
    for col in df.columns:
        if col not in skip:
            df[col] = (
                df[col].astype(str).str.strip()
                .str.replace(",", ".", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
            )

    # Reorder: geography first
    geo_cols   = ["cod_seccion", "cod_provincia", "cod_municipio", "ccaa", "cpro", "cmun", "dist", "secc"]
    other_cols = [c for c in df.columns if c not in geo_cols]
    df = df[geo_cols + other_cols]

    print(f"\nProcessed shape: {df.shape}")
    print(df.head(3).to_string())
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    inspect_only = "--inspect" in sys.argv

    df = load_raw()

    if inspect_only:
        inspect(df)
        print("\nRe-run without --inspect to process and save.")
        sys.exit(0)

    # Always show inspect output first
    inspect(df)

    # Load dictionary if available
    dict_map = load_dict()

    # Process
    out = process(df, dict_map)

    # Save
    out.to_parquet(OUTPUT_DIR / "censo2021_secciones.parquet", index=False)
    out.to_csv(OUTPUT_DIR / "censo2021_secciones.csv", index=False)
    print(f"\nSaved: censo2021_secciones.parquet")
    print(f"Saved: censo2021_secciones.csv")

    # Auto-merge with ADRH 2023
    adrh_path = OUTPUT_DIR / "adrh_secciones_2023.parquet"
    if adrh_path.exists():
        print("\nMerging with ADRH 2023...")
        adrh   = pd.read_parquet(adrh_path)
        merged = adrh.merge(out, on="cod_seccion", how="left")
        merged.to_parquet(OUTPUT_DIR / "features_secciones_2023.parquet", index=False)
        merged.to_csv(OUTPUT_DIR / "features_secciones_2023.csv", index=False)
        print(f"Merged shape: {merged.shape}")
        print(f"Saved: features_secciones_2023.parquet  ← use this as model input")
    else:
        print("\nNote: generate adrh_secciones_2023.parquet first for auto-merge.")

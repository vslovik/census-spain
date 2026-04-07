"""
Download and process ADRH priority tables (municipios + distritos + secciones censales).
Filters to sección censal level, pivots to wide format, saves as parquet + CSV.

Tables:
  31098 - Distribución por fuente de ingresos (salaries, pensions, unemployment, etc.)
  53688 - Índice de Gini y distribución de la renta P80/P20
  31105 - Indicadores demográficos (age, household size, etc.)
"""

import requests
import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path(".")

TABLES = {
    31098: "fuente_ingresos",
    53688: "gini_p8020",
    31105: "demograficos",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.ine.es/dynt3/inebase/index.htm?padre=12385&capsel=5650",
}


# ── Download ──────────────────────────────────────────────────────────────────
def download_csv(table_id: int, label: str) -> Path:
    url  = f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{table_id}.csv"
    dest = OUTPUT_DIR / f"raw_{table_id}_{label}.csv"

    if dest.exists():
        print(f"  [{table_id}] Already downloaded, skipping.")
        return dest

    print(f"\n[{table_id}] Downloading {label} ...")
    print(f"  URL: {url}")

    with requests.get(url, headers=HEADERS, stream=True, timeout=180) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=256 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = f" ({downloaded/total*100:.0f}%)" if total else ""
                    sys.stdout.write(f"\r  {downloaded/1e6:.1f} MB{pct}")
                    sys.stdout.flush()

    print(f"\n  Saved: {dest}  ({dest.stat().st_size/1e6:.1f} MB)")
    return dest


# ── Clean & filter to sección level ──────────────────────────────────────────
def process(raw_path: Path, label: str) -> pd.DataFrame:
    df = pd.read_csv(raw_path, sep=";", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    # Rename geography columns (INE uses different col names per table)
    geo_cols  = [c for c in df.columns if any(k in c.lower() for k in ["municipio", "distrito", "seccion"])]
    val_cols  = [c for c in df.columns if c not in geo_cols]

    # Detect indicator and period columns
    # Typical structure: Municipios | Distritos | Secciones | <Indicator> | Periodo | Total
    col_municipio = next((c for c in geo_cols if "municipio" in c.lower()), None)
    col_distrito  = next((c for c in geo_cols if "distrito"  in c.lower()), None)
    col_seccion   = next((c for c in geo_cols if "seccion"   in c.lower() or "sección" in c.lower()), None)

    non_geo   = [c for c in df.columns if c not in [col_municipio, col_distrito, col_seccion]]
    col_indic = non_geo[0] if len(non_geo) >= 3 else None
    col_per   = next((c for c in non_geo if "periodo" in c.lower() or "year" in c.lower()), non_geo[-2])
    col_val   = non_geo[-1]  # "Total" or similar

    print(f"\n[{label}] Columns detected: {list(df.columns)}")
    print(f"  Rows: {len(df):,}  |  Unique indicators: {df[col_indic].nunique() if col_indic else '?'}")

    # Keep sección level only
    secciones = df[df[col_seccion].notna()].copy()
    print(f"  Sección rows: {len(secciones):,}  |  Unique secciones: {secciones[col_seccion].nunique():,}")

    # Clean values
    secciones[col_val] = (
        secciones[col_val]
        .astype(str).str.strip()
        .replace(".", None)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )

    # Extract clean 10-digit section code
    secciones["cod_seccion"]   = secciones[col_seccion].str.extract(r"^(\d{10})")
    secciones["cod_provincia"] = secciones["cod_seccion"].str[:2]
    secciones["cod_municipio"] = secciones["cod_seccion"].str[:5]

    # Pivot to wide
    wide = (
        secciones
        .pivot_table(
            index=["cod_seccion", "cod_provincia", "cod_municipio", col_municipio, col_per],
            columns=col_indic,
            values=col_val,
            aggfunc="first",
        )
        .reset_index()
    )
    wide.columns.name = None
    wide.rename(columns={col_municipio: "municipio", col_per: "periodo"}, inplace=True)

    print(f"  Wide shape: {wide.shape}")
    return wide


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for table_id, label in TABLES.items():
        raw   = download_csv(table_id, label)
        wide  = process(raw, label)

        out_parquet = OUTPUT_DIR / f"adrh_secciones_{label}.parquet"
        out_csv     = OUTPUT_DIR / f"adrh_secciones_{label}.csv"

        wide.to_parquet(out_parquet, index=False)
        wide.to_csv(out_csv, index=False)
        print(f"  → {out_parquet}")
        print(f"  → {out_csv}")

    print("\n\nAll done. Files saved:")
    for label in TABLES.values():
        print(f"  adrh_secciones_{label}.parquet")

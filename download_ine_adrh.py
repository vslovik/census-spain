"""
Download INE Atlas de Distribución de Renta de los Hogares (ADRH)
Table: Indicadores de renta media y mediana — municipios, distritos y secciones censales
Table ID: 31097
Series: 2015–2023

Usage:
    python download_ine_adrh.py

Downloads a ~300 MB CSV file from the INE public API.
No authentication required.
"""

import requests
import os
import sys
from pathlib import Path

# --- Configuration ---
TABLE_ID = 31097
OUTPUT_DIR = Path(".")          # change to your preferred folder
FORMAT = "csv_bdsc"             # semicolon-separated CSV  (best for pandas)
                                # alternatives: csv_bd (tab), xlsx, px, json

# INE direct file URL (no JS needed, works without a browser)
URL = f"https://www.ine.es/jaxiT3/files/t/es/{FORMAT}/{TABLE_ID}.csv"

OUTPUT_FILE = OUTPUT_DIR / f"adrh_{TABLE_ID}_renta_media_mediana.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/octet-stream,*/*",
    "Referer": "https://www.ine.es/dynt3/inebase/index.htm?padre=12385&capsel=5650",
}

def download(url: str, dest: Path) -> None:
    print(f"Downloading:\n  {url}")
    print(f"Saving to:  {dest}\n")

    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()

        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256   # 256 KB chunks

        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        mb = downloaded / 1e6
                        sys.stdout.write(f"\r  {mb:.1f} MB / {total/1e6:.1f} MB  ({pct:.1f}%)")
                    else:
                        sys.stdout.write(f"\r  {downloaded/1e6:.1f} MB downloaded")
                    sys.stdout.flush()

    print(f"\n\nDone! File saved: {dest}  ({os.path.getsize(dest)/1e6:.1f} MB)")


if __name__ == "__main__":
    download(URL, OUTPUT_FILE)

    # Quick preview with pandas (optional)
    try:
        import pandas as pd
        print("\nPreviewing first 5 rows:")
        df = pd.read_csv(OUTPUT_FILE, sep=";", encoding="utf-8-sig", nrows=5)
        print(df.to_string())
    except ImportError:
        print("\n(Install pandas to get a quick preview: pip install pandas)")

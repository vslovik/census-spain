"""
Filter ADRH table 31097 to sección censal level only and pivot to wide format.
Output: one row per (sección censal × year), one column per indicator.
"""

import pandas as pd

INPUT  = "adrh_31097_renta_media_mediana.csv"
OUTPUT = "adrh_secciones_renta.parquet"   # parquet keeps dtypes and is much smaller

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT, sep=";", encoding="utf-8-sig")
df.columns = ["municipio", "distrito", "seccion", "indicador", "periodo", "valor"]

print(f"Rows loaded: {len(df):,}")

# ── Keep only sección censal rows (seccion column is NOT null) ─────────────────
secciones = df[df["seccion"].notna()].copy()
print(f"Rows at sección level: {len(secciones):,}")
print(f"Unique secciones: {secciones['seccion'].nunique():,}")
print(f"Years: {sorted(secciones['periodo'].unique())}")
print(f"Indicators:\n  " + "\n  ".join(sorted(secciones["indicador"].unique())))

# ── Clean values  ('.' → NaN, European decimal comma → dot) ──────────────────
secciones["valor"] = (
    secciones["valor"]
    .astype(str)
    .str.strip()
    .replace(".", None)                          # suppressed cells
    .str.replace(".", "", regex=False)           # thousands separator
    .str.replace(",", ".", regex=False)          # decimal comma
    .pipe(pd.to_numeric, errors="coerce")
)

# ── Extract clean sección code (10-digit string: 2 prov + 3 mun + 2 dist + 3 sec) ──
# The seccion column looks like "2800101001 Acebeda, La sección 01001"
secciones["cod_seccion"] = secciones["seccion"].str.extract(r"^(\d{10})")

# Also extract province and municipality codes for easy grouping
secciones["cod_provincia"] = secciones["cod_seccion"].str[:2]
secciones["cod_municipio"] = secciones["cod_seccion"].str[:5]

# ── Pivot: wide format, one row per sección × year ───────────────────────────
wide = (
    secciones
    .pivot_table(
        index=["cod_seccion", "cod_provincia", "cod_municipio", "municipio", "periodo"],
        columns="indicador",
        values="valor",
        aggfunc="first",
    )
    .reset_index()
)

# Flatten column names
wide.columns.name = None

# Friendly short column names
rename = {
    "Renta neta media por persona":       "renta_neta_media_persona",
    "Renta neta media por hogar":         "renta_neta_media_hogar",
    "Media de la renta por unidad de consumo":   "renta_media_uc",
    "Mediana de la renta por unidad de consumo": "renta_mediana_uc",
    "Renta bruta media por persona":      "renta_bruta_media_persona",
    "Renta bruta media por hogar":        "renta_bruta_media_hogar",
}
wide.rename(columns=rename, inplace=True)

print(f"\nFinal shape: {wide.shape}")
print(wide.head(10).to_string())

# ── Save ──────────────────────────────────────────────────────────────────────
wide.to_parquet(OUTPUT, index=False)
print(f"\nSaved: {OUTPUT}  ({wide.memory_usage(deep=True).sum()/1e6:.1f} MB in memory)")

# Also save CSV if needed
wide.to_csv(OUTPUT.replace(".parquet", ".csv"), index=False)
print(f"Saved: {OUTPUT.replace('.parquet', '.csv')}")

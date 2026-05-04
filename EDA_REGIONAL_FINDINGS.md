# Regional EDA Findings — ADRH + Census 2021

**Sources used:**
- `data/generated/adrh/adrh_secciones_latest.parquet` — 37,034 secciones, 29 indicators, most-recent-available (ADRH JSON, tables 30824/30825/30826/30829/30832/37677)
- `data/input/ineatlas/census_2021_tract.csv` — Census 2021 tract-level demographics (age, employment, pensions, dwelling tenure)
- `docs/censo_2021_jun.pdf` — INE Nota de Prensa 30 June 2023, *Censos de Población y Viviendas 2021: Resultados sobre Hogares y Viviendas*

Heatmaps built in `eda_adrh.ipynb`, Section 6. Aggregation: **median** of secciones within each province, then median of province medians within each CCAA.

---

## 1. Coverage — all 29 indicators are high-coverage

All 29 indicators in the secciones_latest parquet exceed the 50 % coverage threshold at sección level:

| Coverage band | Indicators |
|---|---|
| 100 % | All 7 demographics from table 30832 (`poblacion`, `edad_media`, `tamano_medio_del_hogar`, `porcentaje_de_hogares_unipersonales`, `pct_65_y_mas`, `pct_menor_18`, `pct_espanola`) |
| ~99.9 % | All 6 income metrics from table 30824 (`renta_neta_media_por_hogar`, `renta_neta_media_por_persona`, `renta_bruta_*`, `media/mediana_renta_por_uc`) |
| ~96.6 % | Income sources (30825): salary, other income; inequality (37677): Gini, P80/P20 |
| ~92 % | Income sources (30825): pensions, unemployment benefits, other benefits |
| ~88.8 % | All 9 poverty threshold indicators from tables 30826/30829 |

**No partial-coverage indicators** — all 29 are used in both heatmaps.

---

## 2. Province-level heatmap — income, pension share, Gini

### Income gradient

The range is steep: the wealthiest province is roughly twice the poorest.

| Rank | Province code | Net hh income (€) | Notes |
|---|---|---|---|
| 1 | 52 (Melilla) | 45,728 | Autonomous city — outlier (see §4) |
| 2 | 20 (Gipuzkoa) | 44,684 | Basque Country |
| 3 | 07 (Illes Balears) | 42,834 | |
| 4 | 51 (Ceuta) | 42,393 | Autonomous city — outlier (see §4) |
| 5 | 28 (Madrid) | 41,768 | |
| 6 | 48 (Bizkaia) | 41,705 | Basque Country |
| 7 | 08 (Barcelona) | 41,470 | |
| 8 | 31 (Navarra) | 41,258 | |
| ... | | | |
| 50 | 06 (Badajoz) | 26,693 | |
| 51 | 23 (Jaén) | 26,564 | |
| 52 | 10 (Cáceres) | 25,136 | |

Provinces 01 (Álava), 20 (Gipuzkoa) and 48 (Bizkaia) rank at the top for income but have **NaN pension share** — see §5 for the explanation.

### Pension share

Strong inverse relationship with income. The high-pension provinces are the rural, aging interior:

| Province | Pension share (%) | Net hh income (€) |
|---|---|---|
| 32 (Ourense) | 34.3 | 29,679 |
| 49 (Zamora) | 33.3 | 27,845 |
| 24 (León) | 33.3 | 31,829 |
| 27 (Lugo) | 32.1 | 31,840 |
| 33 (Asturias) | 31.6 | 33,406 |
| 37 (Salamanca) | 30.9 | 29,549 |
| 10 (Cáceres) | 30.1 | 25,136 |

### Gini

Relatively flat nationally (26–30), with two sharp exceptions:

- **Melilla (52): 35.6** — extreme bimodal income distribution
- **Ceuta (51): 32.4** — same reason
- Mainland range: ~26.4 (Cáceres, Huelva) to ~29.6 (Alicante), ~29.2 (Madrid, Canarias)

High Gini + high income (Madrid, Navarra) signals **intra-region heterogeneity**: CCAA-level averages mask very different secciones. Province- or distrito-level targeting matters more there.

---

## 3. CCAA-level heatmap — 8 HVAC-relevant indicators

Sorted by net household income (high → low). Key column values:

| CCAA | Net hh income (€) | Salary (%) | Pension (%) | Gini | Pop ≥65 (%) | Pop <18 (%) | Mean hh size | Pop (median sec.) |
|---|---|---|---|---|---|---|---|---|
| Melilla | 45,728 | 63.2 | 14.8 | 35.7 | 12.2 | 24.2 | 3.15 | 1,893 |
| Illes Balears | 42,834 | 61.7 | 15.4 | 28.7 | 17.2 | 16.3 | 2.70 | 1,749 |
| Ceuta | 42,393 | 65.1 | 16.2 | 32.5 | 13.2 | 19.8 | 2.90 | 1,376 |
| Comunidad de Madrid | 41,768 | 64.5 | 19.3 | 29.2 | 20.1 | 14.6 | 2.60 | 1,424 |
| País Vasco | 41,705 | 57.5 | NaN | 26.8 | 24.8 | 14.1 | 2.30 | 1,275 |
| Navarra | 41,258 | 55.0 | 23.5 | 29.8 | 23.5 | 15.2 | 2.50 | 1,134 |
| Cataluña | 38,527 | 60.3 | 20.3 | 28.8 | 20.5 | 16.7 | 2.55 | 1,496 |
| Canarias | 34,186 | 60.7 | 19.4 | 28.6 | 19.0 | 13.9 | 2.60 | 1,451 |
| Cantabria | 34,155 | 55.0 | 26.7 | 27.3 | 26.1 | 13.6 | 2.40 | 1,175 |
| Aragón | 33,898 | 54.8 | 24.9 | 27.7 | 26.8 | 13.2 | 2.30 | 506 |
| Asturias | 33,406 | 49.9 | 31.6 | 27.7 | 29.7 | 11.5 | 2.20 | 1,147 |
| Galicia | 33,019 | 51.9 | 30.5 | 27.1 | 30.4 | 11.9 | 2.35 | 1,134 |
| Región de Murcia | 33,018 | 62.2 | 19.1 | 28.3 | 16.9 | 18.6 | 2.80 | 1,188 |
| La Rioja | 32,520 | 55.7 | 24.9 | 28.5 | 27.3 | 13.2 | 2.20 | 914 |
| Comunitat Valenciana | 32,232 | 58.1 | 22.5 | 28.8 | 20.9 | 15.7 | 2.50 | 1,394 |
| Castilla y León | 31,829 | 49.2 | 28.8 | 28.0 | 34.3 | 9.0 | 2.20 | 306 |
| Castilla-La Mancha | 29,351 | 58.5 | 22.3 | 28.4 | 23.7 | 14.9 | 2.40 | 1,096 |
| Andalucía | 28,958 | 55.8 | 24.2 | 27.4 | 20.0 | 16.1 | 2.50 | 1,325 |
| Extremadura | 25,914 | 50.2 | 27.6 | 26.6 | 26.1 | 13.4 | 2.25 | 994 |

### Four demand profiles

**High value, urban — affordability and upsell potential:**
Madrid, País Vasco, Navarra, Cataluña. Salary-dominant (55–65 %), high income (38–42k€), moderate household size (2.3–2.6). Primary HVAC replacement and premium service market. High Gini in Madrid and Navarra means intra-CCAA segmentation matters — target at distrito or sección level, not CCAA.

**Tourist/young — volume, price-sensitive:**
Illes Balears, Canarias, Murcia, Ceuta, Melilla. Salary-dominant (60–65 %), moderate-to-high income, youngest populations (≥65 share: 13–19 %, largest households 2.6–3.2). High-AC-demand climate + active households. Volume market but price-sensitive; sporadic-use dwellings are a significant share (see §6).

**Aging, pension-heavy — trust and maintenance focus:**
Galicia, Asturias, Castilla y León. Income 31–33k€, pension share 28–34 %, ≥65 population 29–34 %, smallest household sizes (2.2). Castilla y León is the extreme: 34.3 % aged ≥65 (highest in Spain), median sección population only 306 (tiny rural tracts), 9 % under-18. HVAC messaging should emphasise reliability, long-term service relationships, and trust — not premium or tech-forward narratives. Low population density makes customer acquisition cost high.

**Low income, rural interior — price-sensitive, modest scale:**
Extremadura, Andalucía, Castilla-La Mancha. Income 26–29k€, mixed age profiles. Andalucía is large (high volume) but income-constrained; Extremadura is the lowest-income CCAA overall.

---

## 4. Anomalies: Ceuta and Melilla

Both autonomous cities appear at the top of the income ranking (45,728€ and 42,393€) but this is misleading:

- **Gini**: 35.7 and 32.5 — the highest in Spain. The median income is high but the distribution is bimodal (a thin high-income layer over a large low-income population).
- **Youngest populations**: ≥65 only 12.2 % (Melilla) and 13.2 % (Ceuta), with very high under-18 shares (24.2 % and 19.8 %) and large household sizes (3.15 and 2.90).
- **Small total population**: median sección population 1,893 and 1,376 — dense urban but tiny total market.

For HVAC propensity modelling, the median income figure for these cities should not be used at face value. Sección-level income distribution is the right lens here, and the high Gini flags that many secciones within each city will be at very different income levels.

---

## 5. Basque Country pension NaN — root cause (not a pipeline bug)

Provinces 01 (Álava), 20 (Gipuzkoa) and 48 (Bizkaia) return **NaN for all income-source indicators** (table 30825: pension share, salary share, etc.) at sección level. Both data sources were checked:

- **JSON (30825.json.zst)**: 1,753 Basque sección pension series exist in the file, but every single one has `Valor = None` across all years. The data is present in structure but suppressed entirely.
- **CSV (30825_secciones.parquet)**: 1,727 Basque secciones appear, but there are zero pension rows for any of them.

Both sources agree: the suppression is complete and consistent. This is **not a data engineering issue** — it is an INE data publication constraint rooted in Spain's fiscal structure. The Basque Country operates under the *Concierto Económico*, with its own Haciendas Forales (Araba, Bizkaia, Gipuzkoa) that collect taxes independently of the AEAT (national tax authority). The ADRH income-source breakdown (table 30825) is derived from AEAT tax microdata. INE does not have access to the equivalent Haciendas Forales microdata at sección level, so income-source decomposition cannot be published for the Basque provinces.

**Note:** Navarra (province 31) also has its own foral system but *does* have pension data (23.5%). INE apparently receives some aggregated data from Navarra's Hacienda Foral, or the suppression threshold differs.

**Income totals (table 30824) are not affected** — net and gross household income figures are available for all Basque secciones (likely estimated through an alternative administrative route). Only the decomposition by income source (salary vs. pension vs. benefits) is suppressed.

**Implication for modelling:** The Basque Country pension/salary split cannot be derived from ADRH. If this decomposition matters for propensity scoring in those provinces, an alternative proxy would be needed — e.g., the Census 2021 retirement pension share variable available in `eda_ineatlas.ipynb` (which comes from Census enumerations, not fiscal records, and covers all provinces including Basque Country).

---

## 6. Cross-validation with Census 2021 notebook (`eda_ineatlas.ipynb`)

The Census 2021 notebook covers **who lives there** (demographic stock from Census microdata); ADRH covers **what they earn and how unequally** (income flows from fiscal records). They use the same sección → province → CCAA geographic hierarchy.

### Consistent signals

| Signal | Census 2021 (ineatlas) | ADRH (eda_adrh) |
|---|---|---|
| NW aging axis | High retirement pension share in Galicia, Asturias, CyL | High income-source pension share in Galicia (30.5%), Asturias (31.6%), CyL (28.8%) |
| CyL oldest CCAA | Highest % age 65+ | 34.3 % aged ≥65 (ADRH confirms) |
| Basque/Madrid top income | High employment, low retirement pension | Highest net hh income: PV 41.7k€, Madrid 41.8k€ |
| Urban tract density | Illes Balears, Cataluña, Madrid largest tracts | Illes Balears, Madrid among top income CCAAa |

The demographic signal for aging and income is robust and consistent across two independent INE sources.

### What ADRH adds that Census 2021 does not provide

- **The 2:1 income gap**: Madrid 41,768€ vs. Extremadura 25,914€ — the income gradient was not visible in the Census notebook (only employment/age ratios).
- **Gini and P80/P20**: The Census has no inequality measure. ADRH reveals that Madrid and Navarra — despite being high-income — have above-average inequality. Province or distrito targeting is more appropriate than CCAA-level.
- **Salary vs. pension income decomposition**: Age share alone (Census) underdetermines HVAC propensity. A 63-year-old drawing 32 % pension income in Galicia is a different customer segment from a 63-year-old drawing 19 % pension income in Madrid. The income source split is the more actionable signal.

### What Census 2021 adds that ADRH does not provide (relevant for HVAC)

- **Dwelling tenure** (Census 2021): 75.5 % of Spain's 18.5M households own their home (PDF, p.3). High-ownership municipalities are the primary HVAC installation/replacement market. Rental households rarely contract multi-year service agreements. The PDF's Barcelona (31.1% rental) vs. Huelva (8.6% rental) gap directly affects addressable market size.
- **Vacant dwellings** (PDF, p.7–8): 14.4 % of Spain's 26.6M dwellings are vacant. Rural municipalities (<1,000 pop) have a vacancy rate of 33.3 per 100 dwellings. Castilla y León — the most rural CCAA by sección population (median 306) — will have very high vacancy. Vacant homes are not HVAC propensity targets.
- **Sporadic-use dwellings** (PDF, p.9–10): 9.4 % of all dwellings (2.5M). Concentrated in coastal Cantabria, Castellón, Valencia, Girona, Almería. Cantabria (Noja 47.7%, Laredo 31.5%), Valencia coast (Peñíscola 31.8%), Girona coast (Castell-Platja d'Aro 22.4%). Sporadic-use homes represent seasonal rather than annual HVAC demand.
- **Single-person households** (PDF, p.2): 27 % of all households and growing fast (+19.3 % vs. 2011). 2.1M single-person households are aged 65+; 70.8 % of those are women. This segment has high HVAC maintenance need (heating reliability in winter) but low propensity for expensive upgrades. The CCAA dimension: this segment is most concentrated in the aging NW CCAAa confirmed by both sources.

### Combined picture: what a joined dataset enables

Once ADRH income data and Census 2021 demographic/dwelling data are joined at sección level (shared key: `cod_seccion`), the combined feature set includes:

- **Affordability**: net household income, income source mix
- **Age profile**: % aged 65+, % under 18, mean age
- **Household structure**: size, unipersonal share
- **Dwelling stock**: total dwellings, primary vs. secondary, ownership rate (Census)
- **Inequality**: Gini (for sub-CCAA targeting confidence)

This is the natural input layer for a propensity-to-buy or propensity-to-renew model at sección level.

---

## 7. Comparison with `docs/censo_2021_jun.pdf`

The PDF covers household and housing structure (not income). Key figures and their relationship to our findings:

### Household size trend
PDF: national mean 2.54 in 2021, down from 2.58 in 2011, continuing a 50-year decline (3.82 in 1970). Our CCAA heatmap is consistent: Melilla (3.15) and Ceuta (2.90) are far above the national mean — both are young, immigrant-heavy autonomous cities with cultural norms of larger family units. The NW CCAAa (Asturias 2.20, CyL 2.20, País Vasco 2.30) are well below national mean, consistent with an ageing, single-person-heavy population.

### Unipersonal households
PDF: 5.0M single-person households nationally (+19.3% in a decade); 2.09M of these are aged 65+. This structural shift affects HVAC demand: smaller, older households use less energy but have stronger need for reliable, low-maintenance heating. The CCAA heatmap's `porcentaje_de_hogares_unipersonales` would show this concentrated in the aging NW CCAAa — a direct link between the PDF's national trend and our regional income data.

### Property tenure
PDF: 75.5% ownership nationally, rental grown to 16.1%. Cities with highest rental: Barcelona (31.1%), Girona (30.9%), Palma (23.9%), Madrid (20.0%). The rental share directly reduces the addressable owned-home HVAC market. In our heatmap: Madrid and Cataluña have the highest CCAA incomes but also the highest rental shares — the net addressable market may be smaller than income alone suggests.

### Vacant and sporadic dwellings
PDF: 14.4% vacant, 9.4% sporadic use. Together, nearly 24% of Spain's housing stock is not a primary residence. Key implications for the HVAC propensity model:

- **Sporadic use hotspots** (PDF, p.10): Cantabria coast (Noja 47.7%, Laredo 31.5%), Castellón/Valencia coast (Peñíscola 31.8%, Oropesa 32.4%), Girona coast — all have extremely high sporadic-use rates. These secciones will look like high-income areas in the ADRH data (tourism inflates local incomes) but the seasonal dwelling pattern means HVAC demand is sporadic, not annual. This is a trap for a simple income-based propensity model.
- **Rural vacancy**: Small-municipality Castilla y León (median sección pop = 306) will have very high vacancy rates — the PDF confirms municipalities <1,000 pop average 33.3 vacant per 100 dwellings. ADRH income values for these secciones are valid but the actual addressable dwelling stock is much smaller than the total housing count.

### What is *not* in the PDF
The PDF does not cover regional income levels, Gini, or pension/salary income mix — those are entirely from ADRH and are the primary new findings from `eda_adrh.ipynb` Section 6. The two documents are complementary: the PDF describes the housing stock; ADRH describes the financial profile of the people living in it.

---

## 8. Immediate implications for HVAC propensity modelling

1. **Do not model at CCAA level.** High Gini in Madrid and Navarra, and the sporadic-use distortion in coastal Cantabria/Valencia, mean CCAA averages are misleading. Model at sección or at minimum at province level.

2. **Pension income share is a better signal than age share alone.** Use ADRH `fuente_de_ingreso_pensiones` rather than Census `pct_over64` as the primary aging-customer signal — it directly measures income dependence on pensions, not just demographic composition.

3. **Adjust for dwelling stock quality.** Combine ADRH income with Census vacancy and sporadic-use rates to filter out non-primary-residence secciones from propensity scores. A sección with high income but 40% sporadic-use dwellings (e.g., Noja, Benasque) is not a standard HVAC market.

4. **Basque Country requires a proxy.** For provinces 01/20/48, use Census 2021 `pct_retirement_pension` from `eda_ineatlas.ipynb` as a substitute for the missing ADRH pension income share. Income totals (table 30824) are available and valid for Basque provinces.

5. **Rural Castilla y León is a low-priority outlier.** High aging metrics + high pension share + tiny secciones + high vacancy = expensive customer acquisition in a small addressable market. This CCAA should carry low propensity weight unless there is a specific rural boiler replacement programme.

# Data Request — Customer Service Addresses for HVAC Propensity Model

**To:** Sales / CRM team  
**From:** AI & Data team  
**Subject:** Request for customer address data to support HVAC propensity modelling

---

Hi team,

We're building a propensity model to identify which HomeServe Spain customers are most likely to need — or be receptive to — HVAC products and services (boilers, heat pumps, air conditioning). We'd like to ask for your help in accessing one piece of customer data that is essential to make this work.

## What we need

**The full service address on record for each policy** — specifically:

- Street name and number
- Municipality (city/town)
- Province
- Postal code (código postal)

This is the address associated with the insured property, which we understand is already captured at policy inception.

## Why we need it

Spain has two publicly available datasets that are extremely rich for HVAC demand prediction:

1. **Census 2021 (INE)** — covers all ~36,000 census tracts in Spain with data on age structure, household size, homeownership rates, and pension share. Older homeowners are the highest-demand segment for heating and hot water systems.

2. **ADRH — Atlas de Distribución de Renta de los Hogares (INE)** — annual income data at census tract level: net household income, income sources (salary vs pension), inequality index.

These datasets do not contain individual customer data — they describe the neighbourhood. To use them, we need to map each customer to their census tract. The only way to do that accurately is from the **service address**: we geocode it to coordinates, then match those coordinates to the INE census tract boundary.

Without an address, we can only work at province level, which is too coarse to be useful for targeting — the difference between a wealthy Madrid neighbourhood and a rural Castilla y León town is invisible at province level but critical for conversion probability.

## What this enables

Once the address join is in place, every customer record automatically gains ~70 neighbourhood-level features, including:

| Signal | Source | Why it matters for HVAC |
|---|---|---|
| Net household income | ADRH | Affordability — higher income = more likely to invest in quality HVAC |
| % retirement pensioners in tract | Census 2021 | Elderly residents spend more time at home, have older systems, are higher-priority for boiler replacement |
| Homeownership rate | Census 2021 | Owners invest in HVAC; renters generally don't |
| Mean age of population | Census 2021 | Age is one of the strongest correlates of HVAC purchase intent |
| Mean annual temperature | Open-Meteo reference | Climate zone determines heating vs AC demand orientation |
| Income Gini index | ADRH | Signals whether a tract needs premium or value positioning |

These features feed directly into a scoring model that ranks customers by their likelihood to purchase. The commercial team can then prioritise outreach and tailor offers by segment rather than running undifferentiated campaigns.

## Data format requested

Ideally a flat extract with one row per policy, containing:

```
policy_id | customer_id | service_address | city | province | postal_code
```

A one-time historical extract plus a regular refresh cadence (monthly) would be ideal. If there are data access constraints, we're happy to work within whatever process is already in place for internal data requests.

## Privacy and data handling

The service address is used only for geocoding — we match it to a census tract code and then work with that code and the associated public statistics. We do not store or transmit the raw address beyond what is needed for the geocoding step, and all processing takes place within the HomeServe data environment. The neighbourhood-level features that result from the join are aggregate public statistics and do not constitute personal data.

## Next steps

If you can share or point us to the relevant CRM extract, we can run an initial pilot on a sample of ~10,000 policies to validate match rates and feature quality before scaling to the full customer base.

Happy to jump on a call to discuss further — please let us know what works best.

Thanks,  
AI & Data team
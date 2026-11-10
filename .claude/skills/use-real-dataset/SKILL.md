---
name: use-real-dataset
description: Replace the synthetic demo data with a real housing dataset (Kaggle, bproperty-style listings, Bengaluru house data, etc.) and map its columns to this project's schema.
---

# Swap in a real dataset

The pipeline expects `data/raw/house_data.csv` with exactly these columns:

| column | type | notes |
|---|---|---|
| `location` | text | area / neighbourhood name |
| `total_sqft` | number or range text | `"1200 - 1400"` is averaged automatically |
| `bhk` | integer | bedrooms (parse "3 BHK" / "3 Bedroom" to 3) |
| `bath` | integer, may be blank | blanks are median-imputed |
| `price` | number | **in BDT**. Convert lakh → ×100,000, crore → ×10,000,000, or INR → BDT |

## Steps

1. Load the source file with pandas and inspect `df.head()`, `df.dtypes`, null counts.
2. Rename/convert columns to the table above. Drop columns not used (e.g. `society`, `balcony`, `availability`).
3. Drop personal or demographic columns (owner names, phones, income, religion) — proposal §5.2.
4. Save to `data/raw/house_data.csv` and run `python -m src.train`.
5. If R² < 0.80, look at `reports/figures/outliers_before_after.png` and the cleaning report;
   consider tuning `MIN_LOCATION_COUNT` or `IQR_K` in `src/preprocess.py`.
6. Update the README "Dataset" section with the source and licence of the data.

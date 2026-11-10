---
name: train-price-model
description: Retrain, tune or compare the real estate price models in this project. Use when asked to retrain, add a new regressor, change hyperparameters, check R² / MAE gates, or regenerate EDA charts.
---

# Train the price model

The training entry point is `src/train.py`; cleaning lives in `src/preprocess.py`.

## Steps

1. Make sure the dataset exists at `data/raw/house_data.csv` with columns
   `location, total_sqft, bhk, bath, price` (price in BDT). If it is missing, run
   `python data/generate_dataset.py` (synthetic demo data).
2. Run `python -m src.train`. It:
   - cleans data (sqft ranges, median bath imputation, < 300 sqft/bedroom removal),
   - groups locations with < 10 listings into `Other`,
   - drops per-location price-per-sqft outliers with the IQR rule (k = 1.5),
   - tunes Linear Regression, Lasso, Decision Tree, Random Forest and Gradient Boosting
     with 5-fold `GridSearchCV` on log(price),
   - picks the best test R², refits it on all data, saves `models/model.joblib` and
     `models/metadata.json`, and writes charts to `reports/figures/`.
3. Check the gates printed at the end: **R² ≥ 0.80 (FR-9)** and **MAE < 10% of mean price (FR-10)**.
   The script exits with code 1 if R² fails.
4. Run `python -m pytest -q` — `test_model_meets_accuracy_gates` re-checks both gates.

## Adding a model

Add a tuple to `candidates()` in `src/train.py`: `(name, estimator, param_grid, needs_scaling)`.
Grid keys are plain estimator params; the script prefixes them.

## Rules

- Never add demographic or personal features (proposal §5.2 ethics). Only location, size, bedrooms, bathrooms.
- Keep the IQR and grouping thresholds as constants in `src/preprocess.py` so the report can cite them.
- After retraining, restart the Flask server: it loads the model once at startup.

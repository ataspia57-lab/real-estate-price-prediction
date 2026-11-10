# Real Estate Price Prediction System

SE331 Software Engineering Design Capstone, Section E1, Batch 41
Team: Afroza Yesmin (232-35-636), Taspia Ahmed (232-35-710), Sanzida Islam (232-35-701)
Course teacher: MD. Rashedul Alam

You enter a location, size, bedroom count and bathroom count, and the web app returns an estimated price in BDT. It runs a cleaned ML pipeline, compares five regression models and serves the best one through a Flask REST API.

## Quick start

```bash
pip install -r requirements.txt
python data/generate_dataset.py   # demo dataset (see "Dataset" below)
python -m src.train               # clean -> compare models -> save best + charts
python -m pytest -q               # 23 tests
python -m app.server              # open http://127.0.0.1:5000
```

A trained model is already in `models/`, so `python -m app.server` works right away.

## Project structure

```
data/generate_dataset.py   synthetic Dhaka dataset generator
data/raw/house_data.csv    dataset used for training
src/preprocess.py          cleaning: sqft parsing, imputation, IQR outliers, "Other" grouping
src/train.py               multi-model comparison, tuning, R²/MAE gates, EDA charts
models/                    model.joblib + metadata.json (metrics, locations, input bounds)
app/server.py              Flask API + validation
app/db.py                  prediction log (SQLite, PostgreSQL or MySQL)
app/templates, app/static  web UI
reports/                   model_comparison.csv + figures/
tests/                     pytest suite
.claude/skills/            project skills for Claude
plugin/                    Claude plugin with all project and bundled skills
```

## Results (current model, synthetic data)

| Model | Test R² | MAE (BDT) | MAE % of mean |
|---|---|---|---|
| **Gradient Boosting (deployed)** | **0.968** | 1,232,983 | 7.61% |
| Random Forest | 0.966 | 1,285,449 | 7.93% |
| Decision Tree | 0.960 | 1,384,659 | 8.54% |
| Linear Regression | 0.940 | 1,523,795 | 9.40% |
| Lasso | 0.940 | 1,549,717 | 9.56% |

Cleaning took 12,000 raw rows down to 11,554. It kept 39 named areas and grouped the rarer ones as "Other". Both gates pass: R² ≥ 0.80 (FR-9) and MAE < 10% (FR-10). Prediction latency is about 30 ms, well under the 500 ms target.

> These numbers come from **synthetic** data. Retrain on a real dataset before final submission and update this table.

## Dataset

Shell network access was off while this was built, so `data/generate_dataset.py` creates realistic synthetic Dhaka listings. It includes missing values, sqft ranges, impossible rows and fake-price outliers, so every cleaning step has real work to do.

To use real data, save it as `data/raw/house_data.csv` with these columns: `location, total_sqft, bhk, bath, price` (price in BDT). Then run `python -m src.train`. The `use-real-dataset` skill covers the column mapping.

## Requirement traceability

| Req | Implementation |
|---|---|
| FR-1 inputs | `app/templates/index.html` |
| FR-2 searchable locations | combobox in `app/static/app.js`, `/api/locations` |
| FR-3 validation | client (`app.js`) + server (`validate()` in `app/server.py`) |
| FR-4 BDT price < 2 s | `/api/predict`, lakh/crore formatting |
| FR-5 out-of-range error | bounds from `metadata.json` checked in `validate()` |
| FR-6 median imputation | `SimpleImputer(strategy="median")` |
| FR-7 one-hot encoding | `OneHotEncoder(handle_unknown="ignore")` |
| FR-8 continuous prediction | log-target regressor pipeline |
| FR-9 / FR-10 gates | `src/train.py`, `tests/test_pipeline.py` |

## Budget finder

Enter a budget (in lakh taka), a bedroom count and an optional minimum size. For every area the model prices flats from the smallest valid size up, then shows:

- the biggest flat that fits the budget, and its price
- what a typical flat of that bedroom count costs there
- whether a typical flat fits (green), only a smaller one fits (amber), or nothing fits (grey)

You can sort by best areas (highest price per sqft you can still afford) or by biggest flat. API: `POST /api/budget {"budget": 12000000, "bhk": 3, "min_sqft": 1200}`.

## Admin panel

Open `/admin` (password from the `ADMIN_PASSWORD` env var; the demo default is `admin123`). The panel has:

- **Overview:** total estimates, average price, response time, daily usage, most searched areas
- **Predictions:** full log with a location filter, CSV export and a clear-log action
- **Model:** comparison table, R²/MAE gates, cleaning report, charts and a **Retrain model** button (reloads the new model without a restart)
- **Dataset:** rows, missing values, and listings per area

## API

```
POST /api/predict  {"location":"Dhanmondi","total_sqft":1450,"bhk":3,"bath":2}
→ {"price":21795000,"currency":"BDT","range":[...],"price_per_sqft":15031,
   "model":"Gradient Boosting","latency_ms":27.7,"disclaimer":"..."}
GET /api/locations | /api/health | /api/model-info | /api/history
```

## Deploy

- Docker: `docker build -t propvalue . && docker run -p 8000:8000 propvalue`
- Render / Railway / Heroku: use the `Procfile` (gunicorn).
- Database: SQLite by default. Set `DATABASE_URL` to use PostgreSQL or MySQL.

## Claude skills and plugin

- `.claude/skills/` holds 4 project skills: `train-price-model`, `run-price-app`, `use-real-dataset`, `capstone-report`.
- `plugin/` is the `realestate-capstone` plugin, with those 4 skills plus 63 bundled skills (design, data, Figma, frontend, docs, productivity and more). See `plugin/README.md`.
- `.claude/settings.json` + `.claude-plugin/marketplace.json` let Claude Code load the plugin automatically when the repo is opened.

## Ethics and limits

The model uses only location, size, bedrooms and bathrooms. It uses no demographic or personal data. Every estimate carries a "not a certified legal appraisal" disclaimer. The model does not account for inflation, interest rates, legal status or property condition (proposal §1.4, §5.2).

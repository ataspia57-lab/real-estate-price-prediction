---
name: run-price-app
description: Run, debug, test or deploy the Flask web app and REST API for the real estate price predictor. Use for anything about the UI, /api/predict, validation messages, the prediction log database, Docker or cloud deployment.
---

# Run and deploy the price app

## Local

```bash
pip install -r requirements.txt
python -m app.server          # http://127.0.0.1:5000
python -m pytest -q           # API, validation, latency (<500 ms) and gate tests
```

## Layout

- `app/server.py` — Flask factory `create_app()`, input validation (FR-3, FR-5), `/api/predict`, `/api/locations`, `/api/health`, `/api/model-info`, `/api/history`.
- `app/db.py` — prediction log. SQLite by default; set `DATABASE_URL` for PostgreSQL/MySQL (needs `sqlalchemy` + driver).
- `app/templates/index.html`, `app/static/` — UI: searchable location combobox (FR-2), steppers, BDT lakh/crore formatting, disclaimer.

## API contract

`POST /api/predict` with JSON `{location, total_sqft, bhk, bath?}` →
`{price, currency: "BDT", range: [low, high], price_per_sqft, model, latency_ms, bath_imputed, disclaimer}`.
Errors return HTTP 400 with `{error: "<human readable message>"}`.

## Deploy

- Docker: `docker build -t propvalue . && docker run -p 8000:8000 propvalue`
- Render/Railway/Heroku: the `Procfile` runs gunicorn on `$PORT`.
- Commit `models/model.joblib` + `models/metadata.json`, or the Docker build trains a fresh model.

## Rules

- Every prediction response must keep the "not a certified legal appraisal" disclaimer (proposal §5.2).
- Validate on the server even though the UI validates too.
- Do not log anything that identifies a user.

"""
Flask REST API + web UI for the Real Estate Price Prediction System.

    python -m app.server            # http://127.0.0.1:5000

Endpoints
---------
GET  /                  web UI
GET  /api/health        model status + metrics
GET  /api/locations     known locations (FR-2)
POST /api/predict       {location, total_sqft, bhk, bath?} -> price in BDT (FR-4, FR-8)
GET  /api/history       last 20 predictions (stored in SQL database)
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

import joblib
from flask import Flask, jsonify, render_template, request, send_from_directory

from src.preprocess import to_model_input

from . import db

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(os.environ.get("MODEL_DIR", ROOT / "models"))


class ValidationError(ValueError):
    pass


def load_model():
    model = joblib.load(MODEL_DIR / "model.joblib")
    meta = json.loads((MODEL_DIR / "metadata.json").read_text())
    return model, meta


def _number(payload: dict, key: str, *, integer: bool, required: bool = True):
    raw = payload.get(key)
    if raw in (None, ""):
        if required:
            raise ValidationError(f"'{key}' is required.")
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"'{key}' must be a number.")
    if math.isnan(val) or math.isinf(val):
        raise ValidationError(f"'{key}' must be a finite number.")
    if val <= 0:
        raise ValidationError(f"'{key}' must be greater than zero.")
    if integer and not val.is_integer():
        raise ValidationError(f"'{key}' must be a whole number.")
    return int(val) if integer else val


def validate(payload: dict, meta: dict) -> dict:
    """FR-3 input validation + FR-5 out-of-range checks."""
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object.")
    location = str(payload.get("location") or "").strip()
    if not location:
        raise ValidationError("'location' is required.")
    if location not in meta["locations"]:
        raise ValidationError(
            f"'{location}' is not in the training data. Pick a location from the list, "
            "or choose 'Other' for an unlisted neighbourhood.")
    sqft = _number(payload, "total_sqft", integer=False)
    bhk = _number(payload, "bhk", integer=True)
    bath = _number(payload, "bath", integer=True, required=False)

    b = meta["bounds"]
    lo, hi = b["total_sqft"]
    if not lo <= sqft <= hi:
        raise ValidationError(
            f"Size {sqft:,.0f} sqft is outside what the model was trained on "
            f"({lo:,.0f}-{hi:,.0f} sqft), so a prediction would not be reliable.")
    if not b["bhk"][0] <= bhk <= b["bhk"][1]:
        raise ValidationError(f"Bedrooms must be between {b['bhk'][0]} and {b['bhk'][1]}.")
    if sqft / bhk < b["sqft_per_bhk_min"]:
        raise ValidationError(
            f"{sqft:,.0f} sqft is too small for {bhk} bedrooms "
            f"(need at least {b['sqft_per_bhk_min']} sqft per bedroom).")
    if bath is not None and not b["bath"][0] <= bath <= min(b["bath"][1], bhk + 2):
        raise ValidationError(
            f"Bathrooms must be between {b['bath'][0]} and {min(b['bath'][1], bhk + 2)} "
            f"for a {bhk}-bedroom property.")
    return {"location": location, "total_sqft": sqft, "bhk": bhk, "bath": bath}


def create_app(model=None, meta=None, database_url: str | None = None) -> Flask:
    app = Flask(__name__)
    if model is None or meta is None:
        model, meta = load_model()
    app.config["MODEL"], app.config["META"] = model, meta
    app.config["DB_URL"] = database_url or os.environ.get(
        "DATABASE_URL", f"sqlite:///{ROOT / 'predictions.db'}")
    db.init(app.config["DB_URL"])

    @app.get("/")
    def index():
        model, meta = app.config["MODEL"], app.config["META"]
        return render_template("index.html", meta=meta)

    @app.get("/api/health")
    def health():
        model, meta = app.config["MODEL"], app.config["META"]
        best = next(r for r in meta["results"] if r["model"] == meta["best_model"])
        return jsonify(status="ok", model=meta["best_model"], trained_at=meta["trained_at"],
                       test_r2=best["test_r2"], mae_pct=best["mae_pct_of_mean"],
                       gates=meta["gates"])

    @app.get("/api/locations")
    def locations():
        model, meta = app.config["MODEL"], app.config["META"]
        return jsonify(locations=meta["locations"])

    @app.get("/api/model-info")
    def model_info():
        model, meta = app.config["MODEL"], app.config["META"]
        return jsonify(best_model=meta["best_model"], results=meta["results"],
                       cleaning=meta["cleaning"], bounds=meta["bounds"])

    @app.post("/api/predict")
    def predict():
        model, meta = app.config["MODEL"], app.config["META"]
        t0 = time.perf_counter()
        try:
            clean = validate(request.get_json(silent=True), meta)
        except ValidationError as e:
            return jsonify(error=str(e)), 400
        X = to_model_input(clean, meta["locations"])
        price = float(model.predict(X)[0])
        price = max(round(price, -3), 0)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        db.log_prediction(app.config["DB_URL"], clean, price, meta["best_model"], ms)
        mae_pct = next(r for r in meta["results"] if r["model"] == meta["best_model"])["mae_pct_of_mean"]
        return jsonify(
            price=price, currency="BDT",
            range=[round(price * (1 - mae_pct / 100), -3), round(price * (1 + mae_pct / 100), -3)],
            price_per_sqft=round(price / clean["total_sqft"]),
            model=meta["best_model"], latency_ms=ms,
            bath_imputed=clean["bath"] is None,
            disclaimer=("Statistical estimate from historical data, not a certified "
                        "legal appraisal."))

    @app.get("/figures/<path:name>")
    def figures(name):
        return send_from_directory(ROOT / "reports" / "figures", name)

    @app.get("/api/history")
    def history():
        return jsonify(items=db.recent(app.config["DB_URL"], 20))

    from .admin import register_admin
    register_admin(app)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
                     debug=os.environ.get("FLASK_DEBUG") == "1")

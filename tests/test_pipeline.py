import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.preprocess import (OTHER, basic_clean, clean, group_rare_locations, parse_sqft,
                            remove_price_outliers_iqr, to_model_input)

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
needs_model = pytest.mark.skipif(not (MODEL_DIR / "model.joblib").exists(),
                                 reason="run `python -m src.train` first")


# ---------------------------------------------------------------- preprocessing
@pytest.mark.parametrize("raw,expected", [
    ("1250", 1250.0), (1250, 1250.0), ("1200 - 1400", 1300.0), ("abc", None), (None, None),
])
def test_parse_sqft(raw, expected):
    out = parse_sqft(raw)
    assert (np.isnan(out) if expected is None else out == expected)


def test_basic_clean_imputes_and_drops():
    df = pd.DataFrame({
        "location": ["A", "A", None, "B", "B"],
        "total_sqft": ["1000", "1100 - 1300", "900", "200", "1500"],
        "bhk": [2, 2, 2, 2, 3],
        "bath": [2, np.nan, 1, 1, 3],
        "price": [1e7, 1.2e7, 9e6, 3e6, 2e7],
    })
    out = basic_clean(df)
    assert out["location"].notna().all()            # missing location dropped
    assert (out["total_sqft"] / out["bhk"] >= 300).all()  # 200 sqft/2 bhk dropped
    assert out["bath"].notna().all()                # FR-6 median imputation
    assert len(out) == 3


def test_rare_locations_grouped():
    df = pd.DataFrame({"location": ["A"] * 12 + ["B"] * 3})
    out, keep = group_rare_locations(df, min_count=10)
    assert keep == ["A"]
    assert set(out["location"]) == {"A", OTHER}


def test_iqr_removes_fake_listing():
    df = pd.DataFrame({"location": ["A"] * 20, "total_sqft": [1000] * 20,
                       "price": [1e7 + i * 1e4 for i in range(19)] + [1e9]})
    out = remove_price_outliers_iqr(df)
    assert 1e9 not in out["price"].values and len(out) == 19


def test_unknown_location_maps_to_other():
    X = to_model_input({"location": "Atlantis", "total_sqft": 1000, "bhk": 2, "bath": 2}, ["A"])
    assert X.loc[0, "location"] == OTHER


# ---------------------------------------------------------------- model gates
@needs_model
def test_model_meets_accuracy_gates():
    meta = json.loads((MODEL_DIR / "metadata.json").read_text())
    best = next(r for r in meta["results"] if r["model"] == meta["best_model"])
    assert best["test_r2"] >= 0.80          # FR-9
    assert best["mae_pct_of_mean"] < 10.0   # FR-10
    names = {r["model"] for r in meta["results"]}
    assert {"Linear Regression", "Decision Tree", "Random Forest"} <= names


# ---------------------------------------------------------------- API
@pytest.fixture
def client(tmp_path):
    if not (MODEL_DIR / "model.joblib").exists():
        pytest.skip("run `python -m src.train` first")
    from app.server import create_app
    app = create_app(database_url=f"sqlite:///{tmp_path/'t.db'}")
    app.testing = True
    return app.test_client()


def _loc(client):
    return client.get("/api/locations").get_json()["locations"][0]


def test_locations_endpoint(client):
    locs = client.get("/api/locations").get_json()["locations"]
    assert len(locs) > 5 and OTHER in locs


def test_predict_ok_and_fast(client):
    payload = {"location": _loc(client), "total_sqft": 1250, "bhk": 3, "bath": 2}
    client.post("/api/predict", json=payload)  # warm-up
    t0 = time.perf_counter()
    r = client.post("/api/predict", json=payload)
    elapsed = (time.perf_counter() - t0) * 1000
    body = r.get_json()
    assert r.status_code == 200
    assert body["currency"] == "BDT" and body["price"] > 0
    assert body["range"][0] < body["price"] < body["range"][1]
    assert "appraisal" in body["disclaimer"]
    assert elapsed < 500                    # proposal: sub-500ms latency


def test_bigger_flat_costs_more(client):
    loc = _loc(client)
    small = client.post("/api/predict", json={"location": loc, "total_sqft": 900, "bhk": 2, "bath": 2}).get_json()
    big = client.post("/api/predict", json={"location": loc, "total_sqft": 2200, "bhk": 4, "bath": 3}).get_json()
    assert big["price"] > small["price"]


def test_missing_bath_is_imputed(client):
    r = client.post("/api/predict", json={"location": _loc(client), "total_sqft": 1200, "bhk": 3})
    assert r.status_code == 200 and r.get_json()["bath_imputed"] is True


@pytest.mark.parametrize("payload,fragment", [
    ({"total_sqft": 1000, "bhk": 2}, "location"),
    ({"location": "Atlantis", "total_sqft": 1000, "bhk": 2}, "not in the training data"),
    ({"location": "__LOC__", "total_sqft": -5, "bhk": 2}, "greater than zero"),
    ({"location": "__LOC__", "total_sqft": "abc", "bhk": 2}, "must be a number"),
    ({"location": "__LOC__", "total_sqft": 1000, "bhk": 2.5}, "whole number"),
    ({"location": "__LOC__", "total_sqft": 99999, "bhk": 3}, "outside what the model"),
    ({"location": "__LOC__", "total_sqft": 500, "bhk": 4}, "too small"),
])
def test_validation_errors(client, payload, fragment):
    payload = {k: (_loc(client) if v == "__LOC__" else v) for k, v in payload.items()}
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 400
    assert fragment in r.get_json()["error"]


def test_history_logged(client):
    client.post("/api/predict", json={"location": _loc(client), "total_sqft": 1250, "bhk": 3, "bath": 2})
    items = client.get("/api/history").get_json()["items"]
    assert len(items) == 1 and items[0]["bhk"] == 3


def test_ui_renders(client):
    r = client.get("/")
    assert r.status_code == 200 and b"Estimate price" in r.data

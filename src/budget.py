"""
Budget finder: "I have X taka -- where can I buy, and how big?"

For every known location the model prices a range of flat sizes (for the chosen
bedroom count) in one batch, then reports the largest size that fits the budget
and what a typical flat of that bedroom count costs there.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .preprocess import OTHER

SQFT_STEP = 25


def typical_sqft(bhk: int) -> int:
    """Typical flat size for a bedroom count (matches the training data's average)."""
    return int(round((350 + 420 * bhk) / 50) * 50)


def default_bath(bhk: int) -> int:
    return bhk if bhk <= 2 else bhk - 1


def budget_search(model, meta: dict, budget: float, bhk: int, min_sqft: float | None = None) -> dict:
    b = meta["bounds"]
    lo = max(b["total_sqft"][0], b["sqft_per_bhk_min"] * bhk, min_sqft or 0)
    hi = min(b["total_sqft"][1], int(typical_sqft(bhk) * 1.75))  # stay within realistic sizes
    locations = [l for l in meta["locations"] if l != OTHER]
    typ = int(min(max(typical_sqft(bhk), lo), hi))
    bath = default_bath(bhk)

    if lo > hi:
        return {"budget": budget, "bhk": bhk, "typical_sqft": typ, "areas": [],
                "error": f"No {bhk}-bedroom size in the data is at least {min_sqft:,.0f} sqft."}

    grid = np.arange(lo, hi + 1, SQFT_STEP, dtype=float)
    if grid[-1] != hi:
        grid = np.append(grid, hi)
    sizes = np.append(grid, typ)  # last column = typical size

    X = pd.DataFrame({
        "location": np.repeat(locations, len(sizes)),
        "total_sqft": np.tile(sizes, len(locations)),
        "bhk": bhk, "bath": bath,
    })
    prices = model.predict(X).reshape(len(locations), len(sizes))

    areas = []
    for loc, row in zip(locations, prices):
        grid_prices, typ_price = row[:-1], float(row[-1])
        ok = np.where(grid_prices <= budget)[0]
        entry = {
            "location": loc,
            "typical_price": round(typ_price, -3),
            "min_price": round(float(grid_prices[0]), -3),
            "price_per_sqft": round(typ_price / typ),
        }
        if len(ok):
            i = int(ok.max())
            entry.update(max_sqft=int(grid[i]), price_at_max=round(float(grid_prices[i]), -3))
            entry["status"] = "fits" if typ_price <= budget else "smaller"
        else:
            entry.update(max_sqft=None, price_at_max=None, status="over")
        areas.append(entry)

    rank = {"fits": 0, "smaller": 1, "over": 2}
    areas.sort(key=lambda a: (rank[a["status"]], -(a["max_sqft"] or 0), a["min_price"]))
    counts = {k: sum(a["status"] == k for a in areas) for k in rank}
    return {"budget": budget, "bhk": bhk, "bath": bath, "typical_sqft": typ,
            "min_sqft": lo, "counts": counts, "areas": areas}

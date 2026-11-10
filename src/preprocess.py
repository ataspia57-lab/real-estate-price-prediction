"""
Data cleaning and feature preparation (proposal sections 1.6 Step 2, FR-6, FR-7).

Steps
-----
1. Drop rows with no location or price; strip whitespace.
2. Parse total_sqft (handles ranges like "1200 - 1400" -> 1300).
3. Median-impute missing bath values (FR-6).
4. Remove impossible rows: < MIN_SQFT_PER_BHK square feet per bedroom.
5. Dynamic location categorisation: locations with fewer than
   MIN_LOCATION_COUNT listings become "Other" (proposal 1.7).
6. IQR filtering on price-per-sqft, per location, to drop extreme outliers.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

MIN_SQFT_PER_BHK = 300
MIN_LOCATION_COUNT = 10
IQR_K = 1.5
OTHER = "Other"

FEATURES = ["location", "total_sqft", "bhk", "bath"]
TARGET = "price"


def parse_sqft(value) -> float:
    """'1250' -> 1250.0, '1200 - 1400' -> 1300.0, junk -> NaN."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    nums = re.findall(r"\d+(?:\.\d+)?", str(value))
    if not nums:
        return np.nan
    vals = [float(n) for n in nums[:2]]
    return sum(vals) / len(vals)


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["location"] = df["location"].astype("string").str.strip()
    df = df.dropna(subset=["location", "price"])
    df["total_sqft"] = df["total_sqft"].map(parse_sqft)
    for col in ["bhk", "bath", "price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["total_sqft", "bhk", "price"])
    df["bath"] = df["bath"].fillna(df["bath"].median())
    df = df[(df["total_sqft"] > 0) & (df["bhk"] > 0) & (df["price"] > 0)]
    df = df[df["total_sqft"] / df["bhk"] >= MIN_SQFT_PER_BHK]
    df = df[df["bath"] <= df["bhk"] + 2]
    df["bhk"] = df["bhk"].astype(int)
    df["location"] = df["location"].astype(str)
    return df


def group_rare_locations(df: pd.DataFrame, min_count: int = MIN_LOCATION_COUNT):
    counts = df["location"].value_counts()
    keep = sorted(counts[counts >= min_count].index.tolist())
    df = df.copy()
    df["location"] = np.where(df["location"].isin(keep), df["location"], OTHER)
    return df, keep


def remove_price_outliers_iqr(df: pd.DataFrame, k: float = IQR_K) -> pd.DataFrame:
    """Per-location IQR filter on price per sqft."""
    df = df.copy()
    df["pps"] = df["price"] / df["total_sqft"]
    q1 = df.groupby("location")["pps"].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby("location")["pps"].transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    mask = (df["pps"] >= q1 - k * iqr) & (df["pps"] <= q3 + k * iqr)
    return df[mask].drop(columns="pps")


def clean(df: pd.DataFrame):
    """Full cleaning pipeline. Returns (clean_df, kept_locations, report)."""
    report = {"raw_rows": int(len(df))}
    df = basic_clean(df)
    report["after_basic_clean"] = int(len(df))
    df, keep = group_rare_locations(df)
    report["locations_kept"] = len(keep)
    df = remove_price_outliers_iqr(df)
    report["after_iqr"] = int(len(df))
    report["rows_removed"] = report["raw_rows"] - report["after_iqr"]
    return df.reset_index(drop=True), keep, report


def to_model_input(payload: dict, known_locations: list[str]) -> pd.DataFrame:
    """Turn one API request into the single-row frame the model expects."""
    loc = str(payload.get("location", "")).strip()
    if loc not in known_locations:
        loc = OTHER
    return pd.DataFrame([{
        "location": loc,
        "total_sqft": payload.get("total_sqft"),
        "bhk": payload.get("bhk"),
        "bath": payload.get("bath"),  # may be None -> median-imputed by the pipeline (FR-6)
    }])

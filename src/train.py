"""
Train, compare and export the price model (proposal 1.3, 1.6 Step 3-4, FR-9, FR-10).

    python -m src.train                       # uses data/raw/house_data.csv
    python -m src.train --data my.csv --no-eda

Multi-model comparison engine: every candidate is tuned with GridSearchCV,
scored on the same hold-out test set, and the best R^2 wins. Deployment is
blocked (non-zero exit) if the winner misses the R^2 >= 0.80 gate.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

from .preprocess import FEATURES, TARGET, clean

ROOT = Path(__file__).resolve().parents[1]
R2_GATE = 0.80
MAE_GATE_PCT = 10.0


def build_preprocessor(scale: bool) -> ColumnTransformer:
    num_steps = [("impute", SimpleImputer(strategy="median"))]  # FR-6
    if scale:
        num_steps.append(("scale", StandardScaler()))
    return ColumnTransformer([
        ("loc", OneHotEncoder(handle_unknown="ignore"), ["location"]),  # FR-7
        ("num", Pipeline(num_steps), ["total_sqft", "bhk", "bath"]),
    ])


def candidates(seed: int):
    """(name, estimator, param_grid, needs_scaling)"""
    return [
        ("Linear Regression", LinearRegression(), {}, True),
        ("Lasso", Lasso(max_iter=20000), {"alpha": [0.0005, 0.005, 0.05]}, True),
        ("Decision Tree", DecisionTreeRegressor(random_state=seed),
         {"max_depth": [8, 14, None], "min_samples_leaf": [2, 5, 10]}, False),
        ("Random Forest", RandomForestRegressor(random_state=seed, n_jobs=-1),
         {"n_estimators": [200], "max_depth": [None, 20], "min_samples_leaf": [1, 3]}, False),
        ("Gradient Boosting", GradientBoostingRegressor(random_state=seed),
         {"n_estimators": [300], "learning_rate": [0.05, 0.1], "max_depth": [3, 5]}, False),
    ]


def make_pipeline(est, scale: bool) -> TransformedTargetRegressor:
    # Prices are right-skewed; model log(price) and invert on output.
    pipe = Pipeline([("prep", build_preprocessor(scale)), ("model", est)])
    return TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)


def save_eda(df: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    out_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.histplot(df["price"] / 1e5, bins=60, ax=ax, color="#2f6f62")
    ax.set(title="Price distribution (cleaned)", xlabel="Price (lakh BDT)", ylabel="Listings")
    fig.tight_layout(); fig.savefig(out_dir / "price_distribution.png", dpi=120); plt.close(fig)

    top = df.assign(pps=df.price / df.total_sqft).groupby("location")["pps"].median().sort_values()
    fig, ax = plt.subplots(figsize=(8, 8))
    top.plot.barh(ax=ax, color="#2f6f62")
    ax.set(title="Median price per sqft by location", xlabel="BDT per sqft", ylabel="")
    fig.tight_layout(); fig.savefig(out_dir / "price_per_sqft_by_location.png", dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(df[["total_sqft", "bhk", "bath", "price"]].corr(), annot=True, fmt=".2f",
                cmap="Greens", ax=ax, vmin=0, vmax=1)
    ax.set_title("Feature correlation")
    fig.tight_layout(); fig.savefig(out_dir / "correlation.png", dpi=120); plt.close(fig)


def save_raw_boxplot(raw: pd.DataFrame, cleaned: pd.DataFrame, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .preprocess import basic_clean

    before = basic_clean(raw)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    axes[0].boxplot(before.price / before.total_sqft)
    axes[0].set_title("Price/sqft before IQR filter")
    axes[1].boxplot(cleaned.price / cleaned.total_sqft)
    axes[1].set_title("Price/sqft after IQR filter")
    for a in axes:
        a.set_ylabel("BDT per sqft")
    fig.tight_layout(); fig.savefig(out_dir / "outliers_before_after.png", dpi=120); plt.close(fig)


def train(data_path: Path, out_dir: Path, seed: int = 42, eda: bool = True) -> dict:
    raw = pd.read_csv(data_path)
    df, locations, clean_report = clean(raw)
    print(f"Cleaning: {clean_report}")

    X, y = df[FEATURES], df[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=seed)
    cv = KFold(n_splits=5, shuffle=True, random_state=seed)

    results, best = [], None
    for name, est, grid, scale in candidates(seed):
        t0 = time.perf_counter()
        model = make_pipeline(est, scale)
        grid = {f"regressor__model__{k}": v for k, v in grid.items()}
        if not grid:  # Linear Regression has nothing to tune
            grid = {"regressor__model__fit_intercept": [True]}
        search = GridSearchCV(model, grid, cv=cv, scoring="r2", n_jobs=-1)
        search.fit(X_tr, y_tr)
        pred = search.predict(X_te)
        r2 = r2_score(y_te, pred)
        mae = mean_absolute_error(y_te, pred)
        row = {
            "model": name,
            "cv_r2": round(float(search.best_score_), 4),
            "test_r2": round(float(r2), 4),
            "test_mae_bdt": round(float(mae)),
            "mae_pct_of_mean": round(float(mae / y_te.mean() * 100), 2),
            "best_params": {k.split("__")[-1]: v for k, v in search.best_params_.items()},
            "train_seconds": round(time.perf_counter() - t0, 1),
        }
        results.append(row)
        print(f"  {name:<18} test R2={r2:.4f}  MAE={mae:,.0f} BDT ({row['mae_pct_of_mean']}%)")
        if best is None or r2 > best[1]:
            best = (search.best_estimator_, r2, row)

    model, best_r2, best_row = best
    # Refit the winner on all clean data for deployment.
    model.fit(X, y)

    bounds = {
        "total_sqft": [float(df.total_sqft.min()), float(df.total_sqft.max())],
        "bhk": [int(df.bhk.min()), int(df.bhk.max())],
        "bath": [int(df.bath.min()), int(df.bath.max())],
        "sqft_per_bhk_min": 300,
    }
    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_file": str(data_path.name),
        "currency": "BDT",
        "best_model": best_row["model"],
        "gates": {"r2_min": R2_GATE, "mae_pct_max": MAE_GATE_PCT,
                  "r2_passed": best_r2 >= R2_GATE,
                  "mae_passed": best_row["mae_pct_of_mean"] < MAE_GATE_PCT},
        "results": results,
        "cleaning": clean_report,
        "locations": locations + ["Other"],
        "bounds": bounds,
        "median_bath": float(df.bath.median()),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"Best: {best_row['model']} (test R2={best_r2:.4f}) -> {out_dir/'model.joblib'}")

    if eda:
        fig_dir = ROOT / "reports" / "figures"
        save_eda(df, fig_dir)
        save_raw_boxplot(raw, df, fig_dir)
        pd.DataFrame(results).drop(columns="best_params").to_csv(
            ROOT / "reports" / "model_comparison.csv", index=False)
        print(f"EDA charts -> {fig_dir}")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "raw" / "house_data.csv"))
    ap.add_argument("--out", default=str(ROOT / "models"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-eda", action="store_true")
    args = ap.parse_args()
    meta = train(Path(args.data), Path(args.out), args.seed, eda=not args.no_eda)
    if not meta["gates"]["r2_passed"]:
        print(f"FAILED deployment gate: R2 < {R2_GATE}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

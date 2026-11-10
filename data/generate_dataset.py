"""
Generate a SYNTHETIC Dhaka housing dataset for development and demos.

The proposal calls for a historical housing dataset. Shell network access was
unavailable while scaffolding, so this script produces a realistic stand-in
with the same columns the pipeline expects:

    location, total_sqft, bhk, bath, price   (price in BDT)

It deliberately includes the problems the cleaning step must solve:
missing values, non-numeric sqft ranges ("1200 - 1400"), impossible
sqft-per-bedroom rows, and extreme price outliers / fake listings.

Replace data/raw/house_data.csv with a real dataset (same column names)
before final submission. See README.md -> "Using a real dataset".
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Base price per sqft (BDT) for well-known Dhaka areas -- illustrative values.
AREAS = {
    "Gulshan": 21000, "Banani": 19000, "Baridhara": 23000, "Dhanmondi": 15500,
    "Lalmatia": 13500, "Bashundhara R/A": 12500, "Uttara": 10500,
    "Mohakhali": 11500, "Tejgaon": 9800, "Niketan": 14000, "Mohammadpur": 8800,
    "Mirpur": 7800, "Shyamoli": 8700, "Motijheel": 9200, "Malibagh": 8200,
    "Rampura": 7600, "Badda": 7200, "Khilgaon": 7300, "Banasree": 6900,
    "Aftabnagar": 6600, "Wari": 7900, "Jatrabari": 5900, "Keraniganj": 4300,
    "Savar": 4600, "Tongi": 4900, "Purbachal": 6200, "Kallyanpur": 7400,
    "Agargaon": 9000, "Kafrul": 7700, "Eskaton": 12000,
}
# Low-frequency neighbourhoods -> should be grouped into "Other" by the pipeline.
RARE_AREAS = [
    "Shahjahanpur", "Hatirpool", "Kathalbagan", "Segunbagicha", "Kalabagan",
    "Mugda", "Basabo", "Goran", "Nadda", "Kuril", "Dakshinkhan", "Uttarkhan",
    "Demra", "Sutrapur", "Lalbagh", "Hazaribagh", "Rayer Bazar", "Pallabi",
    "Bhashantek", "Matikata",
]


def generate(n: int = 12000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = list(AREAS)
    weights = rng.dirichlet(np.ones(len(names)) * 2.0)

    rows = []
    for _ in range(n):
        if rng.random() < 0.012:
            loc = rng.choice(RARE_AREAS)
            base = rng.uniform(6000, 11000)
        else:
            loc = rng.choice(names, p=weights)
            base = AREAS[loc]

        bhk = int(rng.choice([1, 2, 3, 4, 5, 6], p=[0.07, 0.30, 0.38, 0.17, 0.06, 0.02]))
        sqft = float(np.clip(rng.normal(350 + bhk * 420, 140 + bhk * 40), 350, 6000))
        bath = int(np.clip(bhk + rng.choice([-1, 0, 0, 1]), 1, bhk + 2))

        # Non-linear effects: premium areas reward size more; extra baths add value;
        # very large units in cheap areas get a discount.
        size_factor = (sqft / 1200) ** (0.08 if base > 12000 else -0.05)
        bath_factor = 1 + 0.025 * (bath - bhk)
        noise = rng.lognormal(0, 0.09)
        price = sqft * base * size_factor * bath_factor * noise
        rows.append([loc, round(sqft), bhk, bath, round(price, -3)])

    df = pd.DataFrame(rows, columns=["location", "total_sqft", "bhk", "bath", "price"])
    df["total_sqft"] = df["total_sqft"].astype(object)

    # --- inject data-quality problems ----------------------------------------
    idx = rng.choice(len(df), size=int(0.02 * n), replace=False)
    df.loc[idx, "bath"] = np.nan                         # missing baths
    idx = rng.choice(len(df), size=int(0.005 * n), replace=False)
    df.loc[idx, "location"] = np.nan                     # missing location
    idx = rng.choice(len(df), size=int(0.01 * n), replace=False)
    df.loc[idx, "total_sqft"] = [                         # ranges like "1200 - 1400"
        f"{int(v) - 100} - {int(v) + 100}" for v in df.loc[idx, "total_sqft"]
    ]
    idx = rng.choice(len(df), size=int(0.008 * n), replace=False)
    df.loc[idx, "total_sqft"] = 250                      # impossible sqft per bedroom
    idx = rng.choice(len(df), size=int(0.012 * n), replace=False)
    df.loc[idx, "price"] = df.loc[idx, "price"] * rng.choice([0.08, 6, 12], size=len(idx))  # fake listings
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=12000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(Path(__file__).parent / "raw" / "house_data.csv"))
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.rows, args.seed)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} synthetic rows -> {out}")


if __name__ == "__main__":
    main()

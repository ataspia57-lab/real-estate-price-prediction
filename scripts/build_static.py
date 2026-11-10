"""
Build a single self-contained HTML page (dist/index.html) that runs the trained
model in the browser -- no Python server needed. Handy for sharing a demo link.

    python scripts/build_static.py

Works when the deployed model is Gradient Boosting (the tree ensemble is exported
to JSON). For other model types, use the Flask app.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def export_model() -> dict:
    model = joblib.load(ROOT / "models" / "model.joblib")
    meta = json.loads((ROOT / "models" / "metadata.json").read_text())
    pipe = model.regressor_
    prep, gb = pipe.named_steps["prep"], pipe.named_steps["model"]
    if type(gb).__name__ != "GradientBoostingRegressor":
        raise SystemExit(f"Static build supports Gradient Boosting only (got {type(gb).__name__}).")
    ohe = prep.named_transformers_["loc"]
    num = prep.named_transformers_["num"]
    if "scale" in num.named_steps:
        raise SystemExit("Static build expects unscaled numeric features.")
    sample = pd.DataFrame([{"location": meta["locations"][0], "total_sqft": 1000, "bhk": 2, "bath": 2}])
    init = float(gb._raw_predict_init(prep.transform(sample))[0, 0])
    trees = []
    for est in gb.estimators_[:, 0]:
        t = est.tree_
        trees.append({"f": t.feature.tolist(), "t": [round(x, 6) for x in t.threshold.tolist()],
                      "l": t.children_left.tolist(), "r": t.children_right.tolist(),
                      "v": [round(x, 8) for x in t.value[:, 0, 0].tolist()]})
    best = next(r for r in meta["results"] if r["model"] == meta["best_model"])
    return {"cats": ohe.categories_[0].tolist(), "median": num.named_steps["impute"].statistics_.tolist(),
            "lr": gb.learning_rate, "init": init, "trees": trees, "bounds": meta["bounds"],
            "locations": meta["locations"], "best": meta["best_model"],
            "mae_pct": best["mae_pct_of_mean"]}, meta


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def main() -> None:
    model_json, meta = export_model()
    static = ROOT / "app" / "static"
    env = Environment(loader=FileSystemLoader(ROOT / "app" / "templates"))
    html = env.get_template("index.html").render(
        meta=meta, url_for=lambda endpoint, filename="": f"__STATIC__/{filename}")

    css = (static / "style.css").read_text()
    js = (static / "app.js").read_text()
    local_api = (static / "local_api.js").read_text()
    model = json.dumps(model_json, separators=(",", ":"))

    html = html.replace('<link rel="stylesheet" href="__STATIC__/style.css">', f"<style>\n{css}\n</style>")
    html = html.replace('<script src="__STATIC__/app.js"></script>',
                        f"<script>window.MODEL={model};</script>\n<script>\n{local_api}\n</script>\n"
                        f"<script>\n{js}\n</script>")
    for fig in (ROOT / "reports" / "figures").glob("*.png"):
        html = html.replace(f'src="/figures/{fig.name}"', f'src="{data_uri(fig)}"')
    html = html.replace('href="/"', 'href="#"').replace(' <a href="/admin/">Admin</a>', '')

    out = ROOT / "dist" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

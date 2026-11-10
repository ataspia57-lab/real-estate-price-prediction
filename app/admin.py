"""
Admin panel: /admin

- Overview: prediction volume, average price, latency, top areas, daily usage
- Predictions: paged, filterable log of every estimate (+ CSV export, clear log)
- Model: comparison table, deployment gates, cleaning report, charts, one-click retrain
- Data: dataset summary per location

Login uses ADMIN_PASSWORD (env). If it is not set, the default password is
"admin123" and the panel shows a warning -- set a real one before deploying.
"""
from __future__ import annotations

import csv
import hmac
import io
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import pandas as pd
from flask import (Blueprint, Response, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from . import db

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORD = "admin123"

bp = Blueprint("admin", __name__, url_prefix="/admin")

_retrain_lock = threading.Lock()
_retrain_state = {"running": False, "started": None, "finished": None, "ok": None, "message": ""}


# ------------------------------------------------------------------ auth helpers
def _password() -> str:
    return os.environ.get("ADMIN_PASSWORD", DEFAULT_PASSWORD)


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*a, **kw)
    return wrapped


def _csrf_token() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def _check_csrf() -> bool:
    return hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "-"))


@bp.app_context_processor
def _inject():
    return {"csrf_token": _csrf_token, "default_password": "ADMIN_PASSWORD" not in os.environ}


# ------------------------------------------------------------------ routes
@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), _password()):
            session.clear()
            session["admin"] = True
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/admin") else url_for("admin.dashboard"))
        time.sleep(0.5)  # slow down guessing
        error = "Wrong password."
    return render_template("admin/login.html", error=error)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@bp.get("/")
@login_required
def dashboard():
    url = current_app.config["DB_URL"]
    meta = current_app.config["META"]
    tab = request.args.get("tab", "overview")
    loc = request.args.get("location") or None
    pg = max(int(request.args.get("page", 1) or 1), 1)
    per = 25
    rows, total_rows = db.page(url, limit=per, offset=(pg - 1) * per, location=loc)
    return render_template(
        "admin/dashboard.html", tab=tab, meta=meta, stats=db.stats(url),
        rows=rows, total_rows=total_rows, page=pg, pages=max((total_rows + per - 1) // per, 1),
        location=loc, dataset=_dataset_summary(), retrain=_retrain_state)


@bp.get("/export.csv")
@login_required
def export_csv():
    rows = db.all_rows(current_app.config["DB_URL"])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["id"] + db.COLS)
    w.writeheader()
    w.writerows(rows)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=predictions_{stamp}.csv"})


@bp.post("/clear")
@login_required
def clear_log():
    if not _check_csrf() or request.form.get("confirm") != "DELETE":
        flash("Type DELETE to confirm clearing the log.", "error")
    else:
        db.clear(current_app.config["DB_URL"])
        flash("Prediction log cleared.", "ok")
    return redirect(url_for("admin.dashboard", tab="predictions"))


@bp.post("/retrain")
@login_required
def retrain():
    if not _check_csrf():
        flash("Session expired, try again.", "error")
        return redirect(url_for("admin.dashboard", tab="model"))
    app = current_app._get_current_object()
    with _retrain_lock:
        if _retrain_state["running"]:
            flash("Retraining is already running.", "error")
            return redirect(url_for("admin.dashboard", tab="model"))
        _retrain_state.update(running=True, started=_now(), finished=None, ok=None,
                              message="Training models…")
    threading.Thread(target=_run_retrain, args=(app,), daemon=True).start()
    flash("Retraining started. This takes a few minutes; the page updates when it finishes.", "ok")
    return redirect(url_for("admin.dashboard", tab="model"))


@bp.get("/retrain/status")
@login_required
def retrain_status():
    return jsonify(_retrain_state)


# ------------------------------------------------------------------ helpers
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _run_retrain(app) -> None:
    from src.train import train
    from .server import load_model
    try:
        meta = train(ROOT / "data" / "raw" / "house_data.csv", ROOT / "models", eda=True)
        if meta["gates"]["r2_passed"]:
            model, meta = load_model()
            app.config["MODEL"], app.config["META"] = model, meta
            msg = f"Done. Deployed {meta['best_model']}."
            ok = True
        else:
            msg = "Finished, but the best model missed the R² ≥ 0.80 gate. Check the data."
            ok = False
    except Exception as exc:  # surface the error in the panel
        msg, ok = f"Failed: {exc}", False
    _retrain_state.update(running=False, finished=_now(), ok=ok, message=msg)


def _dataset_summary() -> dict | None:
    path = ROOT / "data" / "raw" / "house_data.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    counts = df["location"].value_counts()
    return {
        "file": path.name, "rows": len(df), "columns": list(df.columns),
        "missing": {c: int(n) for c, n in df.isna().sum().items() if n},
        "locations": len(counts),
        "per_location": [{"location": k, "count": int(v)} for k, v in counts.head(40).items()],
        "modified": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def register_admin(app) -> None:
    app.secret_key = os.environ.get("SECRET_KEY") or app.secret_key or secrets.token_hex(32)
    app.register_blueprint(bp)

    @app.template_filter("bdt_short")
    def bdt_short(n):
        n = float(n or 0)
        return f"৳{n / 1e7:.2f} cr" if n >= 1e7 else f"৳{n / 1e5:.1f} lakh"

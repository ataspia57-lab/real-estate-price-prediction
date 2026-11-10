"""
Prediction query log (proposal section 3: "store user logs, historical prediction queries").

Default: SQLite file (zero setup). For PostgreSQL / MySQL set DATABASE_URL, e.g.
    postgresql+psycopg://user:pass@host/realestate
    mysql+pymysql://user:pass@host/realestate
and `pip install sqlalchemy psycopg[binary]` (or pymysql).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id          INTEGER PRIMARY KEY {autoinc},
    created_at  VARCHAR(32) NOT NULL,
    location    VARCHAR(120) NOT NULL,
    total_sqft  REAL NOT NULL,
    bhk         INTEGER NOT NULL,
    bath        INTEGER,
    price_bdt   REAL NOT NULL,
    model       VARCHAR(60) NOT NULL,
    latency_ms  REAL NOT NULL
)
"""
COLS = ["created_at", "location", "total_sqft", "bhk", "bath", "price_bdt", "model", "latency_ms"]


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite:///")


def _sqlite_path(url: str) -> str:
    return url[len("sqlite:///"):] or ":memory:"


_engines: dict = {}


def _engine(url: str):
    from sqlalchemy import create_engine  # optional dependency
    if url not in _engines:
        _engines[url] = create_engine(url, pool_pre_ping=True)
    return _engines[url]


def init(url: str) -> None:
    if _is_sqlite(url):
        with sqlite3.connect(_sqlite_path(url)) as con:
            con.execute(SCHEMA.format(autoinc="AUTOINCREMENT"))
        return
    from sqlalchemy import text
    autoinc = "AUTO_INCREMENT" if url.startswith("mysql") else ""
    schema = SCHEMA.format(autoinc=autoinc)
    if url.startswith("postgres"):
        schema = schema.replace("INTEGER PRIMARY KEY ", "SERIAL PRIMARY KEY ")
    with _engine(url).begin() as con:
        con.execute(text(schema))


def log_prediction(url: str, inp: dict, price: float, model: str, ms: float) -> None:
    row = [datetime.now(timezone.utc).isoformat(timespec="seconds"), inp["location"],
           inp["total_sqft"], inp["bhk"], inp["bath"], price, model, ms]
    try:
        if _is_sqlite(url):
            with sqlite3.connect(_sqlite_path(url)) as con:
                con.execute(f"INSERT INTO predictions ({','.join(COLS)}) VALUES ({','.join('?' * len(COLS))})", row)
            return
        from sqlalchemy import text
        with _engine(url).begin() as con:
            con.execute(text(f"INSERT INTO predictions ({','.join(COLS)}) "
                             f"VALUES ({','.join(':' + c for c in COLS)})"), dict(zip(COLS, row)))
    except Exception as exc:  # logging must never break a prediction
        print(f"[db] could not log prediction: {exc}")


def recent(url: str, limit: int = 20) -> list[dict]:
    q = f"SELECT {','.join(COLS)} FROM predictions ORDER BY id DESC LIMIT {int(limit)}"
    if _is_sqlite(url):
        with sqlite3.connect(_sqlite_path(url)) as con:
            return [dict(zip(COLS, r)) for r in con.execute(q).fetchall()]
    from sqlalchemy import text
    with _engine(url).connect() as con:
        return [dict(zip(COLS, r)) for r in con.execute(text(q)).fetchall()]


# ------------------------------------------------------------------ admin queries
def _rows(url: str, sql: str, params: dict | None = None) -> list[tuple]:
    params = params or {}
    if _is_sqlite(url):
        with sqlite3.connect(_sqlite_path(url)) as con:
            return con.execute(sql, params).fetchall()
    from sqlalchemy import text
    with _engine(url).connect() as con:
        return [tuple(r) for r in con.execute(text(sql), params).fetchall()]


def _exec(url: str, sql: str) -> None:
    if _is_sqlite(url):
        with sqlite3.connect(_sqlite_path(url)) as con:
            con.execute(sql)
        return
    from sqlalchemy import text
    with _engine(url).begin() as con:
        con.execute(text(sql))


def stats(url: str) -> dict:
    total, avg_price, avg_ms, max_ms = _rows(
        url, "SELECT COUNT(*), AVG(price_bdt), AVG(latency_ms), MAX(latency_ms) FROM predictions")[0]
    today = _rows(url, "SELECT COUNT(*) FROM predictions WHERE created_at >= :d",
                  {"d": datetime.now(timezone.utc).strftime("%Y-%m-%d")})[0][0]
    top = _rows(url, "SELECT location, COUNT(*) AS n, AVG(price_bdt) FROM predictions "
                     "GROUP BY location ORDER BY n DESC LIMIT 8")
    by_day = _rows(url, "SELECT SUBSTR(created_at, 1, 10) AS d, COUNT(*) FROM predictions "
                        "GROUP BY d ORDER BY d DESC LIMIT 14")
    by_bhk = _rows(url, "SELECT bhk, COUNT(*) FROM predictions GROUP BY bhk ORDER BY bhk")
    return {
        "total": total or 0, "today": today or 0,
        "avg_price": avg_price or 0, "avg_ms": avg_ms or 0, "max_ms": max_ms or 0,
        "top_locations": [{"location": l, "count": n, "avg_price": p} for l, n, p in top],
        "by_day": [{"day": d, "count": n} for d, n in reversed(by_day)],
        "by_bhk": [{"bhk": b, "count": n} for b, n in by_bhk],
    }


def page(url: str, *, limit: int = 25, offset: int = 0, location: str | None = None) -> tuple[list[dict], int]:
    where, params = "", {"lim": int(limit), "off": int(offset)}
    if location:
        where, params["loc"] = "WHERE location = :loc", location
    total = _rows(url, f"SELECT COUNT(*) FROM predictions {where}", params)[0][0]
    rows = _rows(url, f"SELECT id, {','.join(COLS)} FROM predictions {where} "
                      "ORDER BY created_at DESC, id DESC LIMIT :lim OFFSET :off", params)
    return [dict(zip(["id"] + COLS, r)) for r in rows], total


def all_rows(url: str) -> list[dict]:
    return [dict(zip(["id"] + COLS, r))
            for r in _rows(url, f"SELECT id, {','.join(COLS)} FROM predictions ORDER BY id")]


def clear(url: str) -> None:
    _exec(url, "DELETE FROM predictions")

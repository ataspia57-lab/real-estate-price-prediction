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

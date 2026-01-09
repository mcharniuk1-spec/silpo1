import sqlite3
from typing import Dict, Any, Iterable, Optional

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  category_url TEXT NOT NULL,
  max_pages INTEGER NOT NULL,
  headless INTEGER NOT NULL,
  status TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  page_no INTEGER NOT NULL,
  page_url TEXT NOT NULL,
  title TEXT,
  product_url TEXT,
  brand TEXT,
  pack_qty REAL,
  pack_unit TEXT,
  price_current REAL,
  price_old REAL,
  discount_pct REAL,
  raw_json TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_obs_run ON observations(run_id);
CREATE INDEX IF NOT EXISTS idx_obs_page ON observations(run_id, page_no);
"""

def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

def insert_run(conn: sqlite3.Connection, run: Dict[str, Any]) -> None:
    conn.execute(
        """INSERT INTO runs(run_id, started_at, category_url, max_pages, headless, status, notes)
           VALUES(?,?,?,?,?,?,?)""",
        (
            run["run_id"],
            run["started_at"],
            run["category_url"],
            run["max_pages"],
            1 if run["headless"] else 0,
            run["status"],
            run.get("notes"),
        ),
    )
    conn.commit()

def finish_run(conn: sqlite3.Connection, run_id: str, finished_at: str, status: str, notes: Optional[str]) -> None:
    conn.execute(
        "UPDATE runs SET finished_at=?, status=?, notes=? WHERE run_id=?",
        (finished_at, status, notes, run_id),
    )
    conn.commit()

def insert_observations(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]]) -> int:
    cur = conn.cursor()
    n = 0
    for r in rows:
        cur.execute(
            """INSERT INTO observations(
                 run_id, observed_at, page_no, page_url,
                 title, product_url, brand, pack_qty, pack_unit,
                 price_current, price_old, discount_pct, raw_json
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                r["run_id"], r["observed_at"], r["page_no"], r["page_url"],
                r.get("title"), r.get("product_url"), r.get("brand"),
                r.get("pack_qty"), r.get("pack_unit"),
                r.get("price_current"), r.get("price_old"), r.get("discount_pct"),
                r.get("raw_json"),
            ),
        )
        n += 1
    conn.commit()
    return n

def fetch_observations(conn: sqlite3.Connection, run_id: str):
    cur = conn.execute(
        """SELECT observed_at, page_no, page_url, title, product_url, brand,
                  pack_qty, pack_unit, price_current, price_old, discount_pct
           FROM observations
           WHERE run_id=?
           ORDER BY page_no, title""",
        (run_id,),
    )
    header = [d[0] for d in cur.description]
    return header, cur.fetchall()

import sqlite3
from pathlib import Path
from typing import List

from ..model import HEADER, ProductRow

DDL_RAW = """
CREATE TABLE IF NOT EXISTS silpo_raw (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upload_ts TEXT,
  page_url TEXT,
  page_number INTEGER,
  source TEXT,
  product_title TEXT,
  brand TEXT,
  product_type TEXT,
  fat_pct TEXT,
  pack_qty TEXT,
  pack_unit TEXT,
  price_current REAL,
  price_old TEXT,
  discount_pct TEXT,
  price_per_l_or_kg_or_piece TEXT,
  rating TEXT,
  price_type TEXT
);
"""

DDL_RUNS = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_ts TEXT,
  category_url TEXT,
  max_pages INTEGER,
  rows_written INTEGER,
  status TEXT,
  note TEXT
);
"""

def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(DDL_RAW)
        con.execute(DDL_RUNS)
        con.execute("CREATE INDEX IF NOT EXISTS idx_silpo_raw_upload_ts ON silpo_raw(upload_ts);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_silpo_raw_title ON silpo_raw(product_title);")

def insert_rows(db_path: Path, rows: List[ProductRow]) -> None:
    if not rows:
        return
    cols = HEADER[:]  # matches dataclass order
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO silpo_raw ({','.join(cols)}) VALUES ({placeholders})"
    values = [r.as_list() for r in rows]

    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL;")
        con.executemany(sql, values)
        con.commit()

def log_run(db_path: Path, run_ts: str, category_url: str, max_pages: int, rows_written: int, status: str, note: str = "") -> None:
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(
            "INSERT INTO runs (run_ts, category_url, max_pages, rows_written, status, note) VALUES (?,?,?,?,?,?)",
            (run_ts, category_url, max_pages, rows_written, status, note),
        )
        con.commit()

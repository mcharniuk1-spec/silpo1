import sqlite3
from typing import List
from .model import ProductRow, PageLog, LogEvent

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  category_url TEXT NOT NULL,
  max_pages INTEGER NOT NULL,
  status TEXT NOT NULL,
  note TEXT
);

CREATE TABLE IF NOT EXISTS products(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  upload_ts TEXT NOT NULL,
  page_url TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  source TEXT NOT NULL,
  product_url TEXT,
  product_id TEXT,
  product_title TEXT NOT NULL,
  brand TEXT,
  product_type TEXT,
  fat_pct TEXT,
  pack_qty REAL,
  pack_unit TEXT,
  price_current REAL,
  price_old REAL,
  discount_pct REAL,
  price_per_unit REAL,
  rating REAL,
  price_type TEXT,
  raw_json TEXT
);

CREATE TABLE IF NOT EXISTS page_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  page_url TEXT NOT NULL,
  method TEXT NOT NULL,
  status TEXT NOT NULL,
  items_seen INTEGER NOT NULL,
  items_saved INTEGER NOT NULL,
  http_status INTEGER,
  note TEXT
);

CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  level TEXT NOT NULL,
  event TEXT NOT NULL,
  message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_run ON products(run_id);
CREATE INDEX IF NOT EXISTS idx_pagelogs_run ON page_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
"""

def connect(path: str) -> sqlite3.Connection:
    """Open SQLite connection with ForeignKeys enabled"""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init(conn: sqlite3.Connection):
    """Initialize database schema"""
    conn.executescript(SCHEMA)
    conn.commit()

def insert_run(conn: sqlite3.Connection, run_id: str, started_at: str, category_url: str, max_pages: int):
    """Create run record"""
    conn.execute(
        "INSERT INTO runs(run_id, started_at, category_url, max_pages, status) VALUES(?,?,?,?,?)",
        (run_id, started_at, category_url, max_pages, "RUNNING"),
    )
    conn.commit()

def finish_run(conn: sqlite3.Connection, run_id: str, finished_at: str, status: str, note: str):
    """Mark run as finished"""
    conn.execute(
        "UPDATE runs SET finished_at=?, status=?, note=? WHERE run_id=?",
        (finished_at, status, note, run_id),
    )
    conn.commit()

def insert_products(conn: sqlite3.Connection, rows: List[ProductRow]) -> int:
    """Insert products, return count"""
    cur = conn.cursor()
    n = 0
    for r in rows:
        cur.execute(
            """
            INSERT INTO products(
              run_id, upload_ts, page_url, page_number, source, product_url, product_id,
              product_title, brand, product_type, fat_pct, pack_qty, pack_unit,
              price_current, price_old, discount_pct, price_per_unit, rating, price_type, raw_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                r.run_id, r.upload_ts, r.page_url, r.page_number, r.source, r.product_url, r.product_id,
                r.product_title, r.brand, r.product_type, r.fat_pct, r.pack_qty, r.pack_unit,
                r.price_current, r.price_old, r.discount_pct, r.price_per_unit, r.rating, r.price_type, r.raw_json
            ),
        )
        n += 1
    conn.commit()
    return n

def insert_page_logs(conn: sqlite3.Connection, logs: List[PageLog]) -> int:
    """Insert page logs"""
    cur = conn.cursor()
    for l in logs:
        cur.execute(
            """
            INSERT INTO page_logs(run_id,page_number,page_url,method,status,items_seen,items_saved,http_status,note)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (l.run_id, l.page_number, l.page_url, l.method, l.status, l.items_seen, l.items_saved, l.http_status, l.note),
        )
    conn.commit()
    return len(logs)

def insert_events(conn: sqlite3.Connection, run_id: str, events: List[LogEvent]) -> int:
    """Insert log events"""
    cur = conn.cursor()
    for e in events:
        cur.execute(
            "INSERT INTO events(run_id,ts,level,event,message) VALUES(?,?,?,?,?)",
            (run_id, e.ts, e.level, e.event, e.message),
        )
    conn.commit()
    return len(events)

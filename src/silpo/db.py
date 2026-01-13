import sqlite3
from typing import Iterable, List, Tuple, Optional
from .model import ProductRow, PageLogRow, LogEvent

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  category_url TEXT NOT NULL,
  max_pages INTEGER NOT NULL,
  headless INTEGER NOT NULL,
  status TEXT NOT NULL,
  note TEXT
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  scraped_at TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  page_url TEXT NOT NULL,
  source TEXT NOT NULL,
  product_id TEXT,
  product_url TEXT,
  title TEXT,
  brand TEXT,
  pack_qty REAL,
  pack_unit TEXT,
  price_current REAL,
  price_old REAL,
  discount_pct REAL,
  raw_json TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS page_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  page_url TEXT NOT NULL,
  method TEXT NOT NULL,
  status TEXT NOT NULL,
  http_status INTEGER,
  items_seen INTEGER NOT NULL,
  items_saved INTEGER NOT NULL,
  note TEXT,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  level TEXT NOT NULL,
  event TEXT NOT NULL,
  message TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_products_run ON products(run_id);
CREATE INDEX IF NOT EXISTS idx_plogs_run ON page_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
"""

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

def insert_run(conn: sqlite3.Connection, run_id: str, started_at: str, category_url: str, max_pages: int, headless: bool):
    conn.execute(
        "INSERT INTO runs(run_id, started_at, category_url, max_pages, headless, status) VALUES(?,?,?,?,?,?)",
        (run_id, started_at, category_url, max_pages, 1 if headless else 0, "RUNNING"),
    )
    conn.commit()

def finish_run(conn: sqlite3.Connection, run_id: str, finished_at: str, status: str, note: Optional[str]):
    conn.execute(
        "UPDATE runs SET finished_at=?, status=?, note=? WHERE run_id=?",
        (finished_at, status, note, run_id),
    )
    conn.commit()

def insert_products(conn: sqlite3.Connection, rows: Iterable[ProductRow]) -> int:
    cur = conn.cursor()
    n = 0
    for r in rows:
        cur.execute(
            """
            INSERT INTO products(
              run_id, scraped_at, page_number, page_url, source,
              product_id, product_url, title, brand,
              pack_qty, pack_unit,
              price_current, price_old, discount_pct,
              raw_json
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                r.run_id, r.scraped_at, r.page_number, r.page_url, r.source,
                r.product_id, r.product_url, r.title, r.brand,
                r.pack_qty, r.pack_unit,
                r.price_current, r.price_old, r.discount_pct,
                r.raw_json
            )
        )
        n += 1
    conn.commit()
    return n

def insert_page_logs(conn: sqlite3.Connection, rows: Iterable[PageLogRow]) -> int:
    cur = conn.cursor()
    n = 0
    for r in rows:
        cur.execute(
            """
            INSERT INTO page_logs(
              run_id, page_number, page_url, method, status, http_status,
              items_seen, items_saved, note
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                r.run_id, r.page_number, r.page_url, r.method, r.status, r.http_status,
                r.items_seen, r.items_saved, r.note
            )
        )
        n += 1
    conn.commit()
    return n

def insert_events(conn: sqlite3.Connection, run_id: str, events: List[LogEvent]) -> int:
    cur = conn.cursor()
    n = 0
    for e in events:
        cur.execute(
            "INSERT INTO events(run_id, ts, level, event, message) VALUES(?,?,?,?,?)",
            (run_id, e.ts, e.level, e.event, e.message),
        )
        n += 1
    conn.commit()
    return n

def fetch_for_export(conn: sqlite3.Connection, run_id: str) -> Tuple[list, list, list, dict]:
    prod_cur = conn.execute(
        """
        SELECT scraped_at, page_number, page_url, source,
               product_id, product_url, title, brand,
               pack_qty, pack_unit,
               price_current, price_old, discount_pct
        FROM products WHERE run_id=?
        ORDER BY page_number, title
        """,
        (run_id,),
    )
    products = prod_cur.fetchall()
    prod_cols = [d[0] for d in prod_cur.description]

    pl_cur = conn.execute(
        """
        SELECT page_number, page_url, method, status, http_status, items_seen, items_saved, note
        FROM page_logs WHERE run_id=?
        ORDER BY page_number
        """,
        (run_id,),
    )
    page_logs = pl_cur.fetchall()
    pl_cols = [d[0] for d in pl_cur.description]

    ev_cur = conn.execute(
        "SELECT ts, level, event, message FROM events WHERE run_id=? ORDER BY id",
        (run_id,),
    )
    events = ev_cur.fetchall()
    ev_cols = [d[0] for d in ev_cur.description]

    run_row = conn.execute(
        "SELECT run_id, started_at, finished_at, category_url, max_pages, headless, status, note FROM runs WHERE run_id=?",
        (run_id,),
    ).fetchone()

    run_meta = {}
    if run_row:
        run_meta = {
            "run_id": run_row[0],
            "started_at": run_row[1],
            "finished_at": run_row[2],
            "category_url": run_row[3],
            "max_pages": run_row[4],
            "headless": run_row[5],
            "status": run_row[6],
            "note": run_row[7],
        }

    return (prod_cols, products, (pl_cols, page_logs), (ev_cols, events), run_meta)

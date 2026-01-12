import csv
import os
from typing import List
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

import sqlite3

def _autosize(ws):
    """Auto-fit column widths"""
    for col in range(1, ws.max_column + 1):
        max_len = 0
        for r in range(1, min(ws.max_row, 5000) + 1):
            v = ws.cell(r, col).value
            if v is None:
                continue
            max_len = max(max_len, len(str(v)))
        ws.column_dimensions[get_column_letter(col)].width = min(max(10, max_len + 2), 60)

def export_xlsx_and_csv(
    conn: sqlite3.Connection,
    exports_dir: str,
    run_id: str,
    log_events: List[dict]
) -> tuple[str, str]:
    """Export to XLSX and CSV"""
    os.makedirs(exports_dir, exist_ok=True)

    # Fetch products
    prod = conn.execute("""
      SELECT upload_ts,page_url,page_number,source,product_url,product_id,product_title,brand,product_type,fat_pct,
             pack_qty,pack_unit,price_current,price_old,discount_pct,price_per_unit,rating,price_type
      FROM products WHERE run_id=? ORDER BY page_number, product_title
    """, (run_id,)).fetchall()

    header = [
        "upload_ts","page_url","page_number","source","product_url","product_id","product_title","brand","product_type","fat_pct",
        "pack_qty","pack_unit","price_current","price_old","discount_pct","price_per_unit","rating","price_type"
    ]

    # Fetch page logs
    plogs = conn.execute("""
      SELECT page_number,page_url,method,status,items_seen,items_saved,http_status,note
      FROM page_logs WHERE run_id=? ORDER BY page_number
    """, (run_id,)).fetchall()
    
    pl_header = ["page_number","page_url","method","status","items_seen","items_saved","http_status","note"]

    # XLSX with multiple sheets
    wb = Workbook()
    
    # Products sheet
    ws = wb.active
    ws.title = "products"
    ws.append(header)
    for r in prod:
        ws.append(list(r))
    ws.freeze_panes = "A2"
    _autosize(ws)

    # Page logs sheet
    ws2 = wb.create_sheet("page_logs")
    ws2.append(pl_header)
    for r in plogs:
        ws2.append(list(r))
    ws2.freeze_panes = "A2"
    _autosize(ws2)

    # Events/logs sheet
    ws3 = wb.create_sheet("logs")
    ws3.append(["ts", "level", "event", "message"])
    for e in log_events:
        ws3.append([e["ts"], e["level"], e["event"], e["message"]])
    ws3.freeze_panes = "A2"
    _autosize(ws3)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    xlsx_path = os.path.join(exports_dir, f"silpo_{ts}_{run_id[:8]}.xlsx")
    latest_xlsx = os.path.join(exports_dir, "latest.xlsx")
    wb.save(xlsx_path)
    wb.save(latest_xlsx)

    # CSV (products only)
    csv_path = os.path.join(exports_dir, f"silpo_{ts}_{run_id[:8]}.csv")
    latest_csv = os.path.join(exports_dir, "latest.csv")
    
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in prod:
            w.writerow(list(r))
    
    with open(latest_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in prod:
            w.writerow(list(r))

    return latest_xlsx, latest_csv

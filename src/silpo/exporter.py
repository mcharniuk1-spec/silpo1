import os
import csv
from datetime import datetime
from typing import List, Tuple, Any, Dict
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

def _autosize(ws):
    for col in range(1, ws.max_column + 1):
        mx = 10
        for row in range(1, min(ws.max_row, 5000) + 1):
            v = ws.cell(row=row, column=col).value
            if v is None:
                continue
            mx = max(mx, len(str(v)))
        ws.column_dimensions[get_column_letter(col)].width = min(max(12, mx + 2), 60)

def export_all(
    exports_dir: str,
    run_meta: Dict[str, Any],
    prod_cols: List[str],
    prod_rows: List[Tuple[Any, ...]],
    pl_cols: List[str],
    pl_rows: List[Tuple[Any, ...]],
    ev_cols: List[str],
    ev_rows: List[Tuple[Any, ...]],
) -> Tuple[str, str]:
    os.makedirs(exports_dir, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    xlsx_path = os.path.join(exports_dir, f"silpo_{ts}_{run_meta.get('run_id','run')[:8]}.xlsx")
    csv_path = os.path.join(exports_dir, f"silpo_{ts}_{run_meta.get('run_id','run')[:8]}.csv")
    latest_xlsx = os.path.join(exports_dir, "latest.xlsx")
    latest_csv = os.path.join(exports_dir, "latest.csv")

    # XLSX
    wb = Workbook()

    ws = wb.active
    ws.title = "products"
    ws.append(prod_cols)
    for r in prod_rows:
        ws.append(list(r))
    ws.freeze_panes = "A2"
    _autosize(ws)

    ws2 = wb.create_sheet("page_logs")
    ws2.append(pl_cols)
    for r in pl_rows:
        ws2.append(list(r))
    ws2.freeze_panes = "A2"
    _autosize(ws2)

    ws3 = wb.create_sheet("logs")
    ws3.append(ev_cols)
    for r in ev_rows:
        ws3.append(list(r))
    ws3.freeze_panes = "A2"
    _autosize(ws3)

    ws4 = wb.create_sheet("run")
    ws4.append(["key", "value"])
    for k, v in run_meta.items():
        ws4.append([k, v])
    ws4.freeze_panes = "A2"
    _autosize(ws4)

    wb.save(xlsx_path)
    wb.save(latest_xlsx)

    # CSV (products only)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(prod_cols)
        for r in prod_rows:
            w.writerow(list(r))

    with open(latest_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(prod_cols)
        for r in prod_rows:
            w.writerow(list(r))

    # Hard checks (so “ran but nothing saved” cannot happen silently)
    if not os.path.exists(xlsx_path) or not os.path.exists(latest_xlsx):
        raise RuntimeError("XLSX export missing on disk")
    if not os.path.exists(csv_path) or not os.path.exists(latest_csv):
        raise RuntimeError("CSV export missing on disk")

    return latest_xlsx, latest_csv

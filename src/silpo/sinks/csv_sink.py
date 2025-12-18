from pathlib import Path
from typing import List
import csv

from ..model import HEADER, ProductRow

def write_csv(path: Path, rows: List[ProductRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for r in rows:
            w.writerow(r.as_list())

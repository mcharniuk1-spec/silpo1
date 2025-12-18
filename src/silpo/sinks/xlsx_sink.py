from pathlib import Path
from typing import List
import pandas as pd

from ..model import HEADER, ProductRow

def write_xlsx(path: Path, rows: List[ProductRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.as_list() for r in rows]
    df = pd.DataFrame(data, columns=HEADER)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="silpo_raw", index=False)

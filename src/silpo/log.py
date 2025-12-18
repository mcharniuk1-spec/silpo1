import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class RunLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, step: str, stage: str, message: str = "", extra: Any | None = None) -> None:
        rec = {
            "ts": utc_iso(),
            "step": step,
            "stage": stage,
            "message": message,
            "extra": extra,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

import json
import os
from datetime import datetime, timezone

class JsonlLogger:
    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log(self, level: str, event: str, **fields):
        rec = {"ts": self._ts(), "level": level, "event": event, **fields}
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def info(self, event: str, **fields): self.log("INFO", event, **fields)
    def warn(self, event: str, **fields): self.log("WARN", event, **fields)
    def error(self, event: str, **fields): self.log("ERROR", event, **fields)

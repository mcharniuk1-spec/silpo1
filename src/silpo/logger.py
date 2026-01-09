import json, os
from datetime import datetime, timezone

class JsonlLogger:
    """Writes one JSON per line so CI logs are machine-readable."""
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log(self, level: str, step: str, **fields):
        rec = {"ts": self._ts(), "level": level, "step": step, **fields}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def info(self, step: str, **fields): self.log("INFO", step, **fields)
    def warn(self, step: str, **fields): self.log("WARN", step, **fields)
    def error(self, step: str, **fields): self.log("ERROR", step, **fields)

import json
import os
from datetime import datetime, timezone
from typing import List
from .model import LogEvent

def utc_iso() -> str:
    """UTC ISO8601 timestamp"""
    return datetime.now(timezone.utc).isoformat()

class RunLogger:
    """
    JSONL file + in-memory event buffer
    - Writes each event immediately to disk
    - Keeps events in memory for XLSX 'logs' sheet
    """
    def __init__(self, jsonl_path: str):
        self.jsonl_path = jsonl_path
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
        self.events: List[LogEvent] = []

    def _write(self, level: str, event: str, message: str):
        """Write single event to JSONL and memory"""
        rec = {"ts": utc_iso(), "level": level, "event": event, "message": message}
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.events.append(LogEvent(**rec))

    def info(self, event: str, message: str):
        self._write("INFO", event, message)

    def warn(self, event: str, message: str):
        self._write("WARN", event, message)

    def error(self, event: str, message: str):
        self._write("ERROR", event, message)

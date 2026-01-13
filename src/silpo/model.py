from dataclasses import dataclass
from typing import Optional

@dataclass
class LogEvent:
    ts: str
    level: str
    event: str
    message: str

@dataclass
class ProductRow:
    run_id: str
    upload_ts: str
    page_number: int
    page_url: str
    source: str  # "api" | "dom"
    product_id: Optional[str]
    product_url: Optional[str]
    title: Optional[str]
    brand: Optional[str]
    pack_qty: Optional[float]
    pack_unit: Optional[str]
    price_current: Optional[float]
    price_old: Optional[float]
    discount_pct: Optional[float]
    raw_json: Optional[str]

@dataclass
class PageLogRow:
    run_id: str
    upload_ts: str
    page_number: int
    page_url: str
    method: str           # "api_capture" | "dom_fallback"
    status: str           # "OK" | "ZERO" | "ERROR"
    http_status: Optional[int]
    items_seen: int
    items_saved: int
    note: Optional[str]

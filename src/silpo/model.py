from dataclasses import dataclass
from typing import Optional

@dataclass
class Pack:
    """Product packaging (qty + unit)"""
    qty: Optional[float]
    unit: Optional[str]

@dataclass
class ProductRow:
    """Extracted product data for database storage"""
    run_id: str
    upload_ts: str
    page_url: str
    page_number: int
    source: str
    product_url: Optional[str]
    product_id: Optional[str]

    product_title: str
    brand: str
    product_type: str
    fat_pct: str

    pack_qty: Optional[float]
    pack_unit: str

    price_current: float
    price_old: Optional[float]
    discount_pct: Optional[float]
    price_per_unit: Optional[float]
    rating: Optional[float]
    price_type: str

    raw_json: Optional[str]

@dataclass
class PageLog:
    """Per-page scraping summary"""
    run_id: str
    page_number: int
    page_url: str
    method: str           # API / ALT_API / HTML
    status: str           # OK / EMPTY / ERROR / CHALLENGE
    items_seen: int
    items_saved: int
    http_status: Optional[int]
    note: str

@dataclass
class LogEvent:
    """Structured log event"""
    ts: str
    level: str
    event: str
    message: str

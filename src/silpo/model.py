from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductRow:
    run_id: str
    scraped_at: str
    page_number: int
    page_url: str
    source: str  # api / next_data / dom

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
    page_number: int
    page_url: str
    method: str      # api_get / api_post / next_data / dom
    status: str      # OK / ZERO / ERROR / BLOCK
    http_status: Optional[int]
    items_seen: int
    items_saved: int
    note: Optional[str]

@dataclass
class LogEvent:
    ts: str
    level: str
    event: str
    message: str

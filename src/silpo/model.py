from dataclasses import dataclass
from typing import Any

HEADER = [
    "upload_ts",
    "page_url",
    "page_number",
    "source",
    "product_title",
    "brand",
    "product_type",
    "fat_pct",
    "pack_qty",
    "pack_unit",
    "price_current",
    "price_old",
    "discount_pct",
    "price_per_l_or_kg_or_piece",
    "rating",
    "price_type",
]

@dataclass
class ProductRow:
    upload_ts: str
    page_url: str
    page_number: int
    source: str
    product_title: str
    brand: str
    product_type: str
    fat_pct: str
    pack_qty: str
    pack_unit: str
    price_current: float
    price_old: str | float
    discount_pct: str
    price_per_l_or_kg_or_piece: str
    rating: str
    price_type: str

    def as_list(self) -> list[Any]:
        return [
            self.upload_ts,
            self.page_url,
            self.page_number,
            self.source,
            self.product_title,
            self.brand,
            self.product_type,
            self.fat_pct,
            self.pack_qty,
            self.pack_unit,
            self.price_current,
            self.price_old,
            self.discount_pct,
            self.price_per_l_or_kg_or_piece,
            self.rating,
            self.price_type,
        ]

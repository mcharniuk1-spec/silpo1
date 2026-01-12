import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from .extractors import (
    extract_brand, extract_product_type, extract_fat_pct,
    extract_pack, compute_price_per_unit, to_float
)
from .model import ProductRow

PRICE_RE = re.compile(r"(\d{1,4}(?:[.,]\d{2})?)\s*грн", re.IGNORECASE)
DISCOUNT_RE = re.compile(r"-\s*(\d{1,2})\s*%", re.IGNORECASE)

def _parse_prices(text: str) -> Optional[Tuple[float, Optional[float], Optional[float], str]]:
    """Extract current, old prices and discount from text"""
    vals = [to_float(x) for x in PRICE_RE.findall(text)]
    vals = [v for v in vals if v is not None]
    
    if not vals:
        return None
    
    cur = float(vals[0])
    old = float(vals[1]) if len(vals) > 1 else None
    dm = DISCOUNT_RE.search(text)
    disc = float(dm.group(1)) if dm else None
    price_type = "discount" if disc is not None else "regular"
    
    return cur, old, disc, price_type

def extract_products_from_html(
    run_id: str,
    html: str,
    page_url: str,
    page_number: int,
    batch_stamp: str,
) -> List[ProductRow]:
    """Parse HTML and extract products"""
    soup = BeautifulSoup(html, "html.parser")
    rows: List[ProductRow] = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        
        # Must be product link
        if not href.startswith("/product/"):
            continue
        
        text = a.get_text(" ", strip=True)
        
        # Must have price
        if "грн" not in text.lower():
            continue

        key = href + "::" + text[:80]
        if key in seen:
            continue
        seen.add(key)

        parsed = _parse_prices(text)
        if not parsed:
            continue
        
        cur, old, disc, price_type = parsed

        title = re.sub(r"\s+", " ", text).strip()
        brand = extract_brand(title)
        ptype = extract_product_type(title)
        fat = extract_fat_pct(title)
        pack = extract_pack(title)
        per_unit = compute_price_per_unit(cur, pack)

        rows.append(ProductRow(
            run_id=run_id,
            upload_ts=batch_stamp,
            page_url=page_url,
            page_number=page_number,
            source="https://silpo.ua",
            product_url="https://silpo.ua" + href,
            product_id=None,
            product_title=title,
            brand=brand,
            product_type=ptype,
            fat_pct=fat,
            pack_qty=pack.qty,
            pack_unit=pack.unit or "",
            price_current=cur,
            price_old=old,
            discount_pct=disc,
            price_per_unit=per_unit,
            rating=None,
            price_type=price_type,
            raw_json=None,
        ))

    return rows

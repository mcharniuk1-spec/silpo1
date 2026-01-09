import json
import re
from typing import Any, Dict, List, Optional, Tuple

PRICE_RE = re.compile(r"(\d{1,4}(?:[.,]\d{2})?)\s*грн", re.IGNORECASE)

def looks_like_challenge(html: str, title: str = "") -> bool:
    h = (html or "").lower()
    t = (title or "").lower()
    return ("just a moment" in h) or ("cf-challenge" in h) or ("challenge" in t) or ("just a moment" in t)

def parse_pack(title: str) -> Tuple[Optional[float], Optional[str]]:
    t = (title or "").lower()
    m = re.search(r"(\d{1,2})\s*шт", t)
    if m: return float(m.group(1)), "шт"
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*л\b", t)
    if m: return round(float(m.group(1).replace(",", ".")) * 1000.0, 3), "мл"
    m = re.search(r"(\d{2,4})\s*(г|мл)\b", t)
    if m: return float(m.group(1)), m.group(2)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*кг\b", t)
    if m: return round(float(m.group(1).replace(",", ".")) * 1000.0, 3), "г"
    return None, None

def parse_prices(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    prices = []
    for p in PRICE_RE.findall(text or ""):
        try:
            v = float(p.replace(",", "."))
            if 0.01 < v < 100000:
                prices.append(v)
        except Exception:
            pass
    if not prices:
        return None, None, None
    current = prices[0]
    old = prices[1] if len(prices) > 1 else None

    disc = None
    m = re.search(r"-\s*(\d{1,2})\s*%", text or "")
    if m:
        disc = float(m.group(1))
    return current, old, disc

def _walk(obj: Any, out: List[Dict[str, Any]], limit: int = 5000) -> None:
    if len(out) >= limit:
        return
    if isinstance(obj, dict):
        keys = {k.lower() for k in obj.keys()}
        # heuristic: product-ish dict
        if ("name" in keys or "title" in keys) and ("price" in keys or "prices" in keys or "currentprice" in keys):
            out.append(obj)
            if len(out) >= limit:
                return
        for v in obj.values():
            _walk(v, out, limit)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, out, limit)

def extract_next_data(html: str) -> List[Dict[str, Any]]:
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html or "", re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    _walk(data, out)
    return out

def normalize_product(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = (raw.get("title") or raw.get("name") or "").strip()
    product_url = raw.get("url") or raw.get("productUrl") or raw.get("link")
    if isinstance(product_url, str) and product_url.startswith("/"):
        product_url = "https://silpo.ua" + product_url

    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name") or brand.get("title")
    if brand is not None:
        brand = str(brand).strip()

    def num(x):
        try:
            return float(str(x).replace(",", "."))
        except Exception:
            return None

    price_current = None
    price_old = None
    discount_pct = None

    for k in ("price", "currentPrice", "priceCurrent", "salePrice"):
        if k in raw:
            price_current = num(raw.get(k))
            break

    if price_current is None and isinstance(raw.get("prices"), dict):
        p = raw["prices"]
        for k in ("current", "sale", "value"):
            if k in p:
                price_current = num(p.get(k))
                break
        for k in ("old", "regular", "base"):
            if k in p:
                price_old = num(p.get(k))
                break

    for k in ("discount", "discountPct", "discountPercent"):
        if k in raw:
            discount_pct = num(raw.get(k))
            break

    pack_qty, pack_unit = parse_pack(title)

    return {
        "title": title or None,
        "product_url": product_url if isinstance(product_url, str) else None,
        "brand": brand or None,
        "pack_qty": pack_qty,
        "pack_unit": pack_unit,
        "price_current": price_current,
        "price_old": price_old,
        "discount_pct": discount_pct,
        "raw_json": json.dumps(raw, ensure_ascii=False),
    }

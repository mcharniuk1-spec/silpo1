import json
import re
from typing import Any, Dict, List, Optional

def is_challenge_html(html: str) -> bool:
    h = html.lower()
    return ("just a moment" in h) or ("cf-challenge" in h) or ("challenge-error-text" in h)

def extract_next_data(html: str) -> Optional[dict]:
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def find_productish_nodes(obj: Any, limit: int = 5000) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    stack = [obj]
    seen = 0
    while stack and len(out) < limit and seen < 200000:
        cur = stack.pop()
        seen += 1
        if isinstance(cur, dict):
            keys = {k.lower() for k in cur.keys()}
            if ("name" in keys or "title" in keys) and ("price" in keys or "prices" in keys):
                out.append(cur)
            for v in cur.values():
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return out

def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title") or raw.get("name") or ""
    title = str(title).strip() if title else None
    product_id = raw.get("id") or raw.get("sku") or raw.get("productId")
    url = raw.get("url") or raw.get("link") or raw.get("productUrl")
    if isinstance(url, str) and url.startswith("/"):
        url = "https://silpo.ua" + url

    def num(x):
        try: return float(str(x).replace(",", "."))
        except Exception: return None

    price_current = None
    price_old = None
    discount = None

    if "price" in raw:
        price_current = num(raw.get("price"))
    if isinstance(raw.get("prices"), dict):
        p = raw["prices"]
        price_current = price_current or num(p.get("current") or p.get("sale") or p.get("value"))
        price_old = num(p.get("old") or p.get("regular") or p.get("base"))

    discount = num(raw.get("discount") or raw.get("discountPct") or raw.get("discountPercent"))

    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name") or brand.get("title")
    brand = str(brand).strip() if brand else None

    return {
        "product_id": str(product_id) if product_id is not None else None,
        "product_url": url if isinstance(url, str) else None,
        "title": title,
        "brand": brand,
        "price_current": price_current,
        "price_old": price_old,
        "discount_pct": discount,
        "raw_json": json.dumps(raw, ensure_ascii=False),
    }

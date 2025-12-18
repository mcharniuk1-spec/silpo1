import json
import random
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from .api_discovery import ApiTemplate, discover_get_category_products_template
from .extractors import (
    clean,
    extract_brand,
    extract_fat_pct,
    extract_pack,
    extract_product_type,
    compute_price_per_unit,
    to_float,
)
from .model import ProductRow

def utc_batch_stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def _set_pagination(body: Dict[str, Any], page_num: int) -> Dict[str, Any]:
    b = deepcopy(body)
    candidates = ["page","pageIndex","pageNumber","currentPage","Page","PageIndex","PageNumber"]
    found = False

    for k in candidates:
        if k in b and isinstance(b[k], (int, float, str)):
            b[k] = int(page_num)
            found = True

    if not found:
        for _, v in list(b.items()):
            if isinstance(v, dict):
                for kk in candidates:
                    if kk in v and isinstance(v[kk], (int, float, str)):
                        v[kk] = int(page_num)
                        found = True

    if "offset" in b and isinstance(b["offset"], (int, float, str)):
        try:
            limit = int(b.get("limit") or b.get("pageSize") or 24)
        except Exception:
            limit = 24
        b["offset"] = (page_num - 1) * limit

    return b

def _find_product_list(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            keys = set().union(*(x.keys() for x in obj))
            nameish = {"title","name","productTitle","productName"}
            priceish = {"price","currentPrice","priceCurrent","salePrice","amount"}
            if keys.intersection(nameish) and keys.intersection(priceish):
                return obj  # type: ignore
        for x in obj:
            got = _find_product_list(x)
            if got:
                return got
    elif isinstance(obj, dict):
        for v in obj.values():
            got = _find_product_list(v)
            if got:
                return got
    return []

def _extract_prices(p: Dict[str, Any]) -> Tuple[float | None, float | None, str, str]:
    current = None
    old = None

    for k in ["currentPrice","priceCurrent","salePrice","price","amount"]:
        if p.get(k) is not None:
            current = to_float(p.get(k))
            break

    for k in ["oldPrice","priceOld","regularPrice","basePrice"]:
        if p.get(k) is not None:
            old = to_float(p.get(k))
            break

    discount_pct = ""
    price_type = "regular"

    if old and current and old > current:
        discount_pct = str(int(round((old - current) / old * 100)))
        price_type = "discount"

    for k in ["isPromo","promo","promotion"]:
        if k in p and bool(p.get(k)):
            price_type = "discount"

    return current, old, discount_pct, price_type

def _pick_title(p: Dict[str, Any]) -> str:
    for k in ["title","name","productTitle","productName"]:
        if p.get(k):
            return clean(str(p.get(k)))
    return ""

def _pick_rating(p: Dict[str, Any]) -> str:
    for k in ["rating","rate","stars"]:
        if p.get(k) is not None:
            r = to_float(p.get(k))
            if r is not None and 0 < r <= 5:
                return str(r)
    return ""

def build_api_template(category_url: str, user_agent: str, timeout_ms: int, cache_path: Path) -> ApiTemplate:
    return discover_get_category_products_template(category_url, user_agent, timeout_ms, cache_path)

def scrape_pages_via_api(
    template: ApiTemplate,
    category_url: str,
    max_pages: int,
    debug_dir: Path,
) -> List[ProductRow]:
    sess = requests.Session()
    batch = utc_batch_stamp()
    debug_dir.mkdir(parents=True, exist_ok=True)

    out: List[ProductRow] = []

    for page_num in range(1, max_pages + 1):
        body = _set_pagination(template.body, page_num)
        time.sleep(0.7 + random.random() * 0.8)

        resp = sess.request(
            method=template.method,
            url=template.endpoint,
            headers=template.headers,
            cookies=template.cookies,
            json=body,
            timeout=45,
        )

        if resp.status_code != 200:
            raise RuntimeError(f"API HTTP {resp.status_code} page={page_num}: {resp.text[:300]}")

        data = resp.json()
        (debug_dir / f"silpo_api_page_{page_num}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        products = _find_product_list(data)
        if not products:
            raise RuntimeError(f"Products list not found in JSON page={page_num}. See debug JSON.")

        page_url = category_url if page_num == 1 else f"{category_url}?page={page_num}"

        for p in products:
            title = _pick_title(p)
            if not title:
                continue

            current, old, discount_pct, price_type = _extract_prices(p)
            if current is None:
                continue

            brand = extract_brand(title)
            ptype = extract_product_type(title)
            fat = extract_fat_pct(title)
            pack = extract_pack(title)
            per_unit = compute_price_per_unit(current, pack)
            rating = _pick_rating(p)

            out.append(ProductRow(
                upload_ts=batch,
                page_url=page_url,
                page_number=page_num,
                source="https://silpo.ua",
                product_title=title,
                brand=brand,
                product_type=ptype,
                fat_pct=fat,
                pack_qty=pack.qty,
                pack_unit=pack.unit,
                price_current=float(current),
                price_old=(float(old) if old is not None else ""),
                discount_pct=discount_pct,
                price_per_l_or_kg_or_piece=per_unit,
                rating=rating,
                price_type=price_type,
            ))

    return out

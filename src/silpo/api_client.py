import json
from typing import Any, Dict, List, Optional

import requests

from .api_discovery import ApiTemplate

def _set_pagination(body: Dict[str, Any], page_no: int) -> Dict[str, Any]:
    """Best-effort pagination for both APIs"""
    b = json.loads(json.dumps(body))  # deep copy

    # ALT API format
    if isinstance(b.get("page"), dict) and "number" in b["page"]:
        b["page"]["number"] = page_no
        return b

    # Generic fields
    for k in ("page", "Page", "pageNumber", "PageNumber"):
        if k in b and isinstance(b[k], int):
            b[k] = page_no
            return b

    # Nested pagination
    if isinstance(b.get("pagination"), dict):
        if "page" in b["pagination"]:
            b["pagination"]["page"] = page_no
        if "pageNumber" in b["pagination"]:
            b["pagination"]["pageNumber"] = page_no
    return b

def _find_products_list(obj: Any) -> List[Dict[str, Any]]:
    """Traverse JSON to find product-like objects"""
    out: List[Dict[str, Any]] = []
    stack = [obj]
    while stack and len(out) < 5000:
        cur = stack.pop()
        if isinstance(cur, dict):
            keys = {k.lower() for k in cur.keys()}
            # Looks like product if has name AND price
            if ("name" in keys or "title" in keys) and (
                "price" in keys or "prices" in keys or "currentprice" in keys
            ):
                out.append(cur)
            for v in cur.values():
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return out

def fetch_products_page(
    template: ApiTemplate, page_no: int, timeout: int = 45
) -> tuple[Optional[int], List[Dict[str, Any]], str]:
    """Fetch one page of products via API"""
    sess = requests.Session()
    body = _set_pagination(template.body, page_no)

    resp = sess.request(
        method=template.method,
        url=template.endpoint,
        headers=template.headers,
        cookies=template.cookies,
        json=body,
        timeout=timeout,
    )

    status = resp.status_code
    note = f"HTTP {status}"
    
    if status != 200:
        return status, [], (note + f" body={resp.text[:200]}")
    
    try:
        data = resp.json()
    except Exception:
        return status, [], "JSON decode failed"

    products = _find_products_list(data)
    return status, products, f"products_found={len(products)}"

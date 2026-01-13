import json
import re
from typing import List, Optional, Tuple
from playwright.sync_api import sync_playwright, Response

from .config import settings
from .logutil import RunLogger, utc_iso
from .model import ProductRow, PageLogRow

PRICE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*грн", re.IGNORECASE)

def _page_url(base: str, page_number: int) -> str:
    return base if page_number == 1 else f"{base}?page={page_number}"

def _to_float(x) -> Optional[float]:
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

def _parse_pack(title: str) -> Tuple[Optional[float], Optional[str]]:
    t = (title or "").lower()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*л\b", t)
    if m: return round(float(m.group(1).replace(",", ".")) * 1000.0, 3), "мл"
    m = re.search(r"(\d{2,4})\s*(г|мл)\b", t)
    if m: return float(m.group(1)), m.group(2)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*кг\b", t)
    if m: return round(float(m.group(1).replace(",", ".")) * 1000.0, 3), "г"
    m = re.search(r"(\d{1,2})\s*шт\b", t)
    if m: return float(m.group(1)), "шт"
    return None, None

def _extract_products_from_any_json(obj) -> List[dict]:
    """Heuristic tree-walk: pick dicts that look like products."""
    out = []
    stack = [obj]
    while stack and len(out) < 5000:
        cur = stack.pop()
        if isinstance(cur, dict):
            keys = {k.lower() for k in cur.keys()}
            if ("name" in keys or "title" in keys) and ("price" in keys or "prices" in keys or "currentprice" in keys):
                out.append(cur)
            for v in cur.values():
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return out

def _norm_product(raw: dict) -> tuple:
    title = (raw.get("title") or raw.get("name") or "").strip() or None
    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name") or brand.get("title")
    brand = str(brand).strip() if brand else None

    product_id = raw.get("id") or raw.get("productId") or raw.get("sku")
    product_id = str(product_id) if product_id is not None else None

    product_url = raw.get("url") or raw.get("productUrl") or raw.get("link")
    if isinstance(product_url, str) and product_url.startswith("/"):
        product_url = "https://silpo.ua" + product_url

    price_current = None
    price_old = None
    discount_pct = None

    # common fields
    for k in ("price", "currentPrice", "priceCurrent", "salePrice"):
        if k in raw:
            price_current = _to_float(raw.get(k))
            break

    if price_current is None and isinstance(raw.get("prices"), dict):
        p = raw["prices"]
        for k in ("current", "sale", "value"):
            if k in p:
                price_current = _to_float(p.get(k))
                break
        for k in ("old", "regular", "base"):
            if k in p:
                price_old = _to_float(p.get(k))
                break

    for k in ("discount", "discountPct", "discountPercent"):
        if k in raw:
            discount_pct = _to_float(raw.get(k))
            break

    pack_qty, pack_unit = _parse_pack(title or "")

    return title, brand, product_id, product_url, pack_qty, pack_unit, price_current, price_old, discount_pct

def scrape(run_id: str, logger: RunLogger) -> tuple[List[ProductRow], List[PageLogRow]]:
    all_products: List[ProductRow] = []
    all_page_logs: List[PageLogRow] = []
    batch_ts = utc_iso()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless)
        ctx = browser.new_context(
            user_agent=settings.user_agent,
            locale="uk-UA",
            timezone_id="Europe/Kyiv",
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.new_page()
        page.set_default_timeout(settings.timeout_ms)

        for page_number in range(1, settings.max_pages + 1):
            url = _page_url(settings.category_url, page_number)
            logger.info("page_start", f"page={page_number} url={url}")

            captured_json = []
            http_status: Optional[int] = None

            def on_response(resp: Response):
                nonlocal http_status
                try:
                    if resp.url:
                        # store first status we see for this navigation
                        if http_status is None:
                            http_status = resp.status
                        ctype = (resp.headers.get("content-type") or "").lower()
                        # try to catch JSON responses (site internal API responses)
                        if "application/json" in ctype:
                            # small guard to avoid huge blobs
                            data = resp.json()
                            captured_json.append(data)
                except Exception:
                    pass

            page.on("response", on_response)

            items_seen = 0
            items_saved = 0
            method = "api_capture"
            status = "OK"
            note = None

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")

                # Parse captured JSON
                raws = []
                for obj in captured_json:
                    raws.extend(_extract_products_from_any_json(obj))

                # If nothing captured -> DOM fallback
                if not raws:
                    method = "dom_fallback"
                    html = page.content().lower()
                    if "just a moment" in html:
                        status = "ERROR"
                        note = "challenge_page_detected (anti-bot)."
                        logger.warn("challenge", f"page={page_number} url={url}")
                        # still write page log and stop further pages (usually same result)
                        all_page_logs.append(PageLogRow(
                            run_id=run_id, upload_ts=batch_ts, page_number=page_number, page_url=url,
                            method=method, status=status, http_status=http_status,
                            items_seen=0, items_saved=0, note=note
                        ))
                        break

                    # very simple DOM parse: find blocks with prices
                    texts = page.locator("text=/грн/i").all()
                    for t in texts[:400]:
                        try:
                            txt = (t.inner_text() or "").strip()
                        except Exception:
                            continue
                        m = PRICE_RE.findall(txt)
                        if not m:
                            continue
                        items_seen += 1
                        price = _to_float(m[0])
                        if price is None:
                            continue

                        title = txt.split("\n")[0][:200]
                        pack_qty, pack_unit = _parse_pack(title)

                        all_products.append(ProductRow(
                            run_id=run_id, upload_ts=batch_ts,
                            page_number=page_number, page_url=url,
                            source="dom",
                            product_id=None, product_url=None,
                            title=title, brand=None,
                            pack_qty=pack_qty, pack_unit=pack_unit,
                            price_current=price, price_old=None, discount_pct=None,
                            raw_json=None
                        ))
                        items_saved += 1

                else:
                    # Normalize products from JSON
                    for raw in raws:
                        items_seen += 1
                        title, brand, pid, purl, pack_qty, pack_unit, pc, po, disc = _norm_product(raw)
                        all_products.append(ProductRow(
                            run_id=run_id, upload_ts=batch_ts,
                            page_number=page_number, page_url=url,
                            source="api",
                            product_id=pid, product_url=purl,
                            title=title, brand=brand,
                            pack_qty=pack_qty, pack_unit=pack_unit,
                            price_current=pc, price_old=po, discount_pct=disc,
                            raw_json=json.dumps(raw, ensure_ascii=False)
                        ))
                        items_saved += 1

                if items_saved == 0:
                    status = "ZERO"
                    note = "no_items_parsed_on_page"

                logger.info("page_done", f"page={page_number} items_seen={items_seen} items_saved={items_saved} method={method}")

            except Exception as e:
                status = "ERROR"
                note = f"exception: {str(e)[:200]}"
                logger.error("page_error", f"page={page_number} url={url} err={note}")

            all_page_logs.append(PageLogRow(
                run_id=run_id, upload_ts=batch_ts, page_number=page_number, page_url=url,
                method=method, status=status, http_status=http_status,
                items_seen=items_seen, items_saved=items_saved, note=note
            ))

        browser.close()

    return all_products, all_page_logs

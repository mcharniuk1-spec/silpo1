from datetime import datetime, timezone
import os
from typing import List, Tuple

from playwright.sync_api import sync_playwright

from .config import settings
from .logutil import RunLogger, utc_iso
from .model import ProductRow, PageLog
from .api_discovery import discover_get_category_products_template
from .api_client import fetch_products_page
from .html_scraper import extract_products_from_html
from .extractors import extract_brand, extract_product_type, extract_fat_pct, extract_pack, compute_price_per_unit

def _page_url(page_no: int) -> str:
    """Construct page URL"""
    return settings.category_url if page_no == 1 else f"{settings.category_url}?page={page_no}"

def _looks_like_challenge(html: str, title: str) -> bool:
    """Detect Cloudflare challenge"""
    h = html.lower()
    t = (title or "").lower()
    return ("just a moment" in h) or ("cf-challenge" in h) or ("just a moment" in t)

def scrape(run_id: str, logger: RunLogger) -> Tuple[List[ProductRow], List[PageLog]]:
    """Main scraping orchestrator"""
    started = utc_iso()
    logger.info("scrape_start", f"run_id={run_id} pages={settings.max_pages} url={settings.category_url}")

    template = discover_get_category_products_template()
    logger.info("api_template", f"endpoint={template.endpoint} method={template.method}")

    all_rows: List[ProductRow] = []
    page_logs: List[PageLog] = []

    # Playwright for HTML fallback
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=settings.headless)
    ctx = browser.new_context(user_agent=settings.user_agent, locale="uk-UA")
    page = ctx.new_page()
    page.set_default_timeout(settings.timeout_ms)

    batch_stamp = datetime.now(timezone.utc).isoformat()

    try:
        for p in range(1, settings.max_pages + 1):
            url = _page_url(p)
            method_used = "API"
            status = "OK"
            note = ""
            http_status = None

            logger.info("page_start", f"page={p} url={url}")

            # 1) Try API
            products_raw = []
            try:
                http_status, products_raw, note = fetch_products_page(template, p, timeout=45)
            except Exception as e:
                status = "ERROR"
                note = f"api_error={str(e)[:200]}"
                products_raw = []

            # 2) Parse API products if found
            saved_before = len(all_rows)
            if products_raw:
                for pr in products_raw:
                    title = str(pr.get("title") or pr.get("name") or "").strip()
                    if not title:
                        continue
                    
                    price = pr.get("currentPrice") or pr.get("price") or pr.get("priceCurrent")
                    try:
                        price_current = float(price)
                    except Exception:
                        continue

                    pack = extract_pack(title)
                    per_unit = compute_price_per_unit(price_current, pack)

                    all_rows.append(ProductRow(
                        run_id=run_id,
                        upload_ts=batch_stamp,
                        page_url=url,
                        page_number=p,
                        source="https://silpo.ua",
                        product_url=(("https://silpo.ua" + pr["url"]) 
                                    if isinstance(pr.get("url"), str) and pr["url"].startswith("/")
                                    else pr.get("url")),
                        product_id=str(pr.get("id")) if pr.get("id") is not None else None,
                        product_title=title,
                        brand=extract_brand(title),
                        product_type=extract_product_type(title),
                        fat_pct=extract_fat_pct(title),
                        pack_qty=pack.qty,
                        pack_unit=pack.unit or "",
                        price_current=price_current,
                        price_old=None,
                        discount_pct=None,
                        price_per_unit=per_unit,
                        rating=None,
                        price_type="regular",
                        raw_json=None,
                    ))

            # 3) HTML fallback if API empty
            if (not products_raw) and settings.use_html_fallback:
                method_used = "HTML"
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle")
                    html = page.content()
                    
                    if _looks_like_challenge(html, page.title()):
                        status = "CHALLENGE"
                        note = "challenge_detected_on_html"
                        logger.warn("challenge", f"page={p} url={url}")
                        page_logs.append(PageLog(run_id, p, url, method_used, status, 0, 0, http_status, note))
                        break

                    rows = extract_products_from_html(run_id, html, url, p, batch_stamp)
                    all_rows.extend(rows)
                    
                    if not rows:
                        status = "EMPTY"
                        note = "html_zero_items"
                        
                except Exception as e:
                    status = "ERROR"
                    note = f"html_error={str(e)[:200]}"

            saved_after = len(all_rows)
            saved = saved_after - saved_before

            page_logs.append(PageLog(
                run_id=run_id,
                page_number=p,
                page_url=url,
                method=method_used,
                status=status if saved > 0 else ("EMPTY" if status == "OK" else status),
                items_seen=len(products_raw),
                items_saved=saved,
                http_status=http_status,
                note=note[:500],
            ))

            logger.info("page_done", f"page={p} status={status} saved={saved} note={note}")

    finally:
        browser.close()
        pw.stop()

    logger.info("scrape_finish", f"run_id={run_id} products={len(all_rows)} pages={len(page_logs)} started={started}")
    return all_rows, page_logs

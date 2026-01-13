import json
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from playwright.sync_api import sync_playwright

from .config import settings
from .model import ProductRow, PageLogRow
from .logutil import RunLogger
from .html_scraper import is_challenge_html, extract_next_data, find_productish_nodes, normalize

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def page_url(page_number: int) -> str:
    return settings.category_url if page_number == 1 else f"{settings.category_url}?page={page_number}"

def scrape(run_id: str, logger: RunLogger) -> Tuple[List[ProductRow], List[PageLogRow]]:
    """
    Strategy:
      1) Open page in Playwright (browser context).
      2) Detect challenge; if challenge -> log BLOCK.
      3) Extract products via __NEXT_DATA__ (stable) or DOM fallback.
    """
    products: List[ProductRow] = []
    page_logs: List[PageLogRow] = []

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

        for pn in range(1, settings.max_pages + 1):
            url = page_url(pn)
            logger.info("page_start", f"page={pn} url={url}")

            method = "next_data"
            status = "OK"
            http_status: Optional[int] = None
            items_seen = 0
            items_saved = 0
            note = None

            try:
                resp = page.goto(url, wait_until="domcontentloaded")
                http_status = resp.status if resp else None
                page.wait_for_load_state("networkidle")
                html = page.content()

                # Detect anti-bot challenge
                if is_challenge_html(html) or "just a moment" in (page.title() or "").lower():
                    status = "BLOCK"
                    note = "challenge_detected"
                    logger.warn("challenge", f"page={pn} url={url} status={http_status}")
                    page_logs.append(PageLogRow(run_id, pn, url, method, status, http_status, 0, 0, note))
                    break

                # Try __NEXT_DATA__
                nd = extract_next_data(html)
                raw_nodes = []
                if nd:
                    raw_nodes = find_productish_nodes(nd)
                    method = "next_data"

                # Fallback: minimal DOM extraction if NEXT_DATA not found
                if not raw_nodes:
                    method = "dom"
                    raw_nodes = page.evaluate("""
                        () => {
                          const cards = Array.from(document.querySelectorAll('[data-testid*="product"], .product-card, a[href*="/product/"]'));
                          const out = [];
                          for (const c of cards.slice(0, 200)) {
                            const t = (c.innerText || "").trim();
                            if (!t) continue;
                            if (!t.toLowerCase().includes("грн")) continue;
                            const a = c.closest("a") || c.querySelector("a");
                            out.push({ title: t.split("\\n")[0], url: a ? a.getAttribute("href") : null });
                          }
                          return out;
                        }
                    """)

                items_seen = len(raw_nodes)

                ts = utc_iso()
                for rn in raw_nodes:
                    n = normalize(rn) if isinstance(rn, dict) else {}
                    pr = ProductRow(
                        run_id=run_id,
                        scraped_at=ts,
                        page_number=pn,
                        page_url=url,
                        source=method,
                        product_id=n.get("product_id"),
                        product_url=n.get("product_url"),
                        title=n.get("title"),
                        brand=n.get("brand"),
                        pack_qty=None,
                        pack_unit=None,
                        price_current=n.get("price_current"),
                        price_old=n.get("price_old"),
                        discount_pct=n.get("discount_pct"),
                        raw_json=n.get("raw_json") if "raw_json" in n else json.dumps(rn, ensure_ascii=False),
                    )
                    products.append(pr)
                    items_saved += 1

                if items_saved == 0:
                    status = "ZERO"
                    note = "no_products_extracted"

                logger.info("page_done", f"page={pn} method={method} seen={items_seen} saved={items_saved}")
                page_logs.append(PageLogRow(run_id, pn, url, method, status, http_status, items_seen, items_saved, note))

            except Exception as e:
                status = "ERROR"
                note = str(e)[:300]
                logger.error("page_error", f"page={pn} url={url} err={note}")
                page_logs.append(PageLogRow(run_id, pn, url, method, status, http_status, items_seen, items_saved, note))
                continue

        browser.close()

    return products, page_logs

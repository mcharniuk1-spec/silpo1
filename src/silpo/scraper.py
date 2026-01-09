import os
import time
from datetime import datetime, timezone
from typing import Dict, List

from playwright.sync_api import sync_playwright
from .config import settings
from .extractors import extract_next_data, normalize_product, looks_like_challenge
from .html_scraper import dom_fallback_extract
from .logutil import JsonlLogger

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _page_url(page_no: int) -> str:
    return settings.category_url if page_no == 1 else f"{settings.category_url}?page={page_no}"

def scrape(logger: JsonlLogger, run_id: str) -> List[Dict]:
    rows: List[Dict] = []

    os.makedirs(settings.html_snapshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless)
        context = browser.new_context(
            locale="uk-UA",
            timezone_id="Europe/Kyiv",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()
        page.set_default_timeout(settings.timeout_ms)

        for page_no in range(1, settings.max_pages + 1):
            url = _page_url(page_no)
            logger.info("page_start", run_id=run_id, page_no=page_no, url=url)

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                html = page.content()
                title = ""
                try:
                    title = page.title()
                except Exception:
                    pass

                # Detect anti-bot / challenge
                if looks_like_challenge(html, title):
                    snap_path = os.path.join(settings.html_snapshots_dir, f"challenge_page_{page_no}.html")
                    with open(snap_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    logger.warn("challenge_detected", run_id=run_id, page_no=page_no, url=url, snapshot=snap_path, title=title)
                    break

                # Strategy A: Next.js __NEXT_DATA__
                raw = extract_next_data(html)
                normalized = [normalize_product(x) for x in raw] if raw else []

                # Strategy B: Nuxt payload
                if not normalized:
                    try:
                        nuxt_payload = page.evaluate("() => window.__NUXT__ || null")
                    except Exception:
                        nuxt_payload = None

                    if nuxt_payload:
                        # reuse normalizer heuristics: traverse in python is heavy;
                        # easiest: store as raw_json only via DOM fallback if needed.
                        logger.info("nuxt_payload_present", run_id=run_id, page_no=page_no, url=url)

                # Strategy C: DOM fallback
                if not normalized and settings.use_html_fallback:
                    normalized = dom_fallback_extract(page)

                observed_at = _now()
                for n in normalized:
                    n.update({
                        "run_id": run_id,
                        "observed_at": observed_at,
                        "page_no": page_no,
                        "page_url": url,
                    })
                rows.extend(normalized)

                logger.info("page_done", run_id=run_id, page_no=page_no, url=url, items=len(normalized))
                time.sleep(1.2)  # small pacing to reduce flakiness

            except Exception as e:
                logger.error("page_error", run_id=run_id, page_no=page_no, url=url, error=str(e))
                continue

        browser.close()

    return rows

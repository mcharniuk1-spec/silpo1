import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from playwright.sync_api import sync_playwright

from .config import settings

@dataclass
class ApiTemplate:
    """Captured API request template"""
    endpoint: str
    method: str
    headers: Dict[str, str]
    cookies: Dict[str, str]
    body: Dict[str, Any]

def discover_get_category_products_template() -> ApiTemplate:
    """
    Try to capture real API request from browser network.
    If fails, fallback to ALT API (catalog) if enabled.
    """
    captured: Optional[ApiTemplate] = None
    target = "product-api.silpo.ua/api/v1/Product/GetCategoryProducts"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless)
        ctx = browser.new_context(
            user_agent=settings.user_agent,
            locale="uk-UA",
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.new_page()

        def on_request(req):
            nonlocal captured
            if captured:
                return
            url = req.url
            if target in url:
                post = req.post_data or ""
                try:
                    body = json.loads(post) if post else {}
                except Exception:
                    body = {}
                # Minimal safe headers
                h = {k.lower(): v for k, v in req.headers.items()}
                headers = {
                    "accept": h.get("accept", "application/json"),
                    "content-type": h.get("content-type", "application/json"),
                    "user-agent": h.get("user-agent", settings.user_agent),
                    "accept-language": h.get("accept-language", "uk-UA,uk;q=0.9,en;q=0.8"),
                }
                cookies = {c["name"]: c["value"] for c in ctx.cookies()}
                captured = ApiTemplate(
                    endpoint=url,
                    method=req.method,
                    headers=headers,
                    cookies=cookies,
                    body=body
                )

        page.on("request", on_request)
        page.goto(settings.category_url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        browser.close()

    if captured:
        return captured

    if settings.use_alt_api:
        # ALT API: catalog service
        body = {
            "query": {"collection": "EcomCatalogGlobal"},
            "filter": {"category": [234]},
            "page": {"size": settings.per_page, "number": 1},
        }
        return ApiTemplate(
            endpoint="https://api.catalog.ecom.silpo.ua/api/2.0/exec/EcomCatalogGlobal",
            method="POST",
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "user-agent": settings.user_agent
            },
            cookies={},
            body=body,
        )

    raise RuntimeError("API template not captured and ALT API disabled.")

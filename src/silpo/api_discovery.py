import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from playwright.sync_api import sync_playwright

@dataclass
class ApiTemplate:
    endpoint: str
    method: str
    headers: Dict[str, str]
    cookies: Dict[str, str]
    body: Dict[str, Any]

def _safe_headers(h: Dict[str, str], category_url: str, user_agent: str) -> Dict[str, str]:
    allow = {"accept","accept-language","content-type","origin","referer","user-agent"}
    out: Dict[str, str] = {}
    for k, v in h.items():
        lk = k.lower()
        if lk in allow:
            out[lk] = v
    out.setdefault("accept", "application/json, text/plain, */*")
    out.setdefault("content-type", "application/json")
    out["referer"] = category_url
    out.setdefault("origin", "https://silpo.ua")
    out["user-agent"] = user_agent
    return out

def _cookies_to_dict(cookies_list) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for c in cookies_list:
        n = c.get("name")
        v = c.get("value")
        if n and v:
            out[n] = v
    return out

def load_cached_template(path: Path) -> ApiTemplate | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ApiTemplate(**data)
    except Exception:
        return None

def save_template(path: Path, tpl: ApiTemplate) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tpl.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

def discover_get_category_products_template(
    category_url: str,
    user_agent: str,
    timeout_ms: int,
    cache_path: Path,
) -> ApiTemplate:
    target_substr = "product-api.silpo.ua/api/v1/Product/GetCategoryProducts"

    cached = load_cached_template(cache_path)
    if cached:
        return cached

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent, locale="uk-UA")
        page = context.new_page()

        captured: Dict[str, Any] = {}

        def on_request(req):
            if target_substr in req.url:
                try:
                    post = req.post_data or ""
                    body = json.loads(post) if post else {}
                except Exception:
                    body = {}
                captured["endpoint"] = req.url
                captured["method"] = req.method
                captured["headers"] = dict(req.headers)
                captured["body"] = body

        page.on("request", on_request)
        page.goto(category_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(6000)

        cookies = _cookies_to_dict(context.cookies())
        browser.close()

        if not captured:
            raise RuntimeError(
                "API template not captured: GetCategoryProducts не спіймано. "
                "Якщо Silpo грузить товари лише після взаємодії — додайте scroll/click у discovery."
            )

        headers = _safe_headers(captured.get("headers", {}), category_url, user_agent)

        tpl = ApiTemplate(
            endpoint=captured["endpoint"],
            method=captured["method"],
            headers=headers,
            cookies=cookies,
            body=captured.get("body", {}),
        )
        save_template(cache_path, tpl)
        return tpl

from typing import Dict, List, Optional
from playwright.sync_api import Page
from .extractors import parse_prices, parse_pack

def dom_fallback_extract(page: Page) -> List[Dict]:
    """
    DOM fallback when JSON payloads are not available.
    Heuristic: try product-like anchors first; fallback to 'грн' blocks.
    """
    results: List[Dict] = []

    # 1) Try anchors that look like product links
    candidates = page.evaluate(
        """() => {
          const out = [];
          const anchors = Array.from(document.querySelectorAll('a[href]'));
          for (const a of anchors) {
            const href = a.getAttribute('href') || '';
            if (!href) continue;
            if (!href.includes('/product') && !href.includes('/tovar') && !href.includes('/goods')) continue;
            const card = a.closest('article, li, div') || a;
            const text = (card.innerText || '').trim();
            if (!text || text.length < 20) continue;
            out.push({ href, text: text.slice(0, 2000) });
            if (out.length >= 400) break;
          }
          return out;
        }"""
    )

    def normalize_href(h: str) -> Optional[str]:
        if not isinstance(h, str) or not h:
            return None
        if h.startswith("http"):
            return h
        if h.startswith("/"):
            return "https://silpo.ua" + h
        return None

    seen = set()
    for c in candidates or []:
        href = normalize_href(c.get("href"))
        text = c.get("text") or ""
        if not text:
            continue

        cur, old, disc = parse_prices(text)
        if cur is None:
            continue

        title = text.split("\n")[0].strip()[:250]
        key = (href or "") + "|" + title
        if key in seen:
            continue
        seen.add(key)

        pack_qty, pack_unit = parse_pack(title)
        results.append({
            "title": title,
            "product_url": href,
            "brand": None,
            "pack_qty": pack_qty,
            "pack_unit": pack_unit,
            "price_current": cur,
            "price_old": old,
            "discount_pct": disc,
            "raw_json": None,
        })

    # 2) If still empty — scan for blocks containing 'грн'
    if not results:
        blocks = page.locator("text=/грн/i").all()
        seen2 = set()
        for b in blocks[:800]:
            try:
                txt = (b.inner_text() or "").strip()
            except Exception:
                continue
            cur, old, disc = parse_prices(txt)
            if cur is None:
                continue
            title = txt.split("\n")[0].strip()[:250]
            if title in seen2:
                continue
            seen2.add(title)
            pack_qty, pack_unit = parse_pack(title)
            results.append({
                "title": title,
                "product_url": None,
                "brand": None,
                "pack_qty": pack_qty,
                "pack_unit": pack_unit,
                "price_current": cur,
                "price_old": old,
                "discount_pct": disc,
                "raw_json": None,
            })

    return results

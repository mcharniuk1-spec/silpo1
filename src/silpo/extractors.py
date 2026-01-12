import re
from .model import Pack

def to_float(x):
    """Parse float, handle comma decimals"""
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

def extract_brand(title: str) -> str:
    """Extract brand from title (looks for «Brand» format)"""
    m = re.search(r"«([^»]{2,40})»", title)
    if m:
        return m.group(1).strip()
    # Fallback: first word (capitalized)
    m = re.match(r"^([A-ZА-ЯІЇЄҐ][\w''‐\s]{2,25})\b", title)
    return (m.group(1).strip() if m else "")

def extract_product_type(title: str) -> str:
    """Classify product type"""
    t = title.lower()
    mapping = {
        "молоко": ["молоко"],
        "кефір": ["кефір"],
        "йогурт": ["йогурт"],
        "сметана": ["сметана"],
        "сир": ["сир", "творог", "кисломолоч"],
        "масло": ["масло", "вершков"],
        "яйця": ["яйця", "яйце"],
        "вершки": ["вершки"],
        "ряжанка": ["ряжанка"],
        "десерт": ["десерт", "пудинг"],
    }
    for k, kws in mapping.items():
        if any(w in t for w in kws):
            return k
    return ""

def extract_fat_pct(title: str) -> str:
    """Extract fat percentage"""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", title)
    return (m.group(1).replace(",", ".") if m else "")

def extract_pack(title: str) -> Pack:
    """Parse packaging (qty + unit)"""
    t = title.lower()
    
    # eggs: шт (pieces)
    m = re.search(r"(\d{1,2})\s*шт", t)
    if m:
        return Pack(qty=float(m.group(1)), unit="шт")
    
    # liters -> convert to ml
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*л\b", t)
    if m:
        return Pack(qty=round(float(m.group(1).replace(",", ".")) * 1000, 3), unit="мл")
    
    # grams/ml
    m = re.search(r"(\d{2,4})\s*(г|мл)\b", t)
    if m:
        return Pack(qty=float(m.group(1)), unit=m.group(2))
    
    # kilograms -> grams
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*кг\b", t)
    if m:
        return Pack(qty=round(float(m.group(1).replace(",", ".")) * 1000, 3), unit="г")
    
    return Pack(qty=None, unit="")

def compute_price_per_unit(price: float, pack: Pack):
    """Compute price per unit (per piece or per kg/liter)"""
    if not price or not pack.qty:
        return None
    if pack.unit == "шт":
        return round(price / pack.qty, 2)
    if pack.unit in {"г", "мл"}:
        base = pack.qty / 1000.0
        if base <= 0:
            return None
        return round(price / base, 2)
    return None

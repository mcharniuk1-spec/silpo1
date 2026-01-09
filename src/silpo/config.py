import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # Category to scrape
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )

    # Pagination
    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))

    # Playwright
    headless: bool = os.getenv("SILPO_HEADLESS", "true").lower() in {"1", "true", "yes"}
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "60000"))

    # Fallbacks
    use_html_fallback: bool = os.getenv("SILPO_USE_HTML_FALLBACK", "true").lower() in {"1", "true", "yes"}

    # Output dirs
    data_dir: str = os.getenv("SILPO_DATA_DIR", "data")
    db_path: str = os.getenv("SILPO_DB_PATH", "data/silpo.sqlite")
    logs_dir: str = os.getenv("SILPO_LOGS_DIR", "data/logs")
    exports_dir: str = os.getenv("SILPO_EXPORTS_DIR", "data/exports")
    html_snapshots_dir: str = os.getenv("SILPO_HTML_SNAPSHOTS_DIR", "data/html_snapshots")

settings = Settings()

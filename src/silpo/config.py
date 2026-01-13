import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # Category with dairy/eggs (adjust if you need a narrower milk-only category)
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )

    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))
    headless: bool = os.getenv("SILPO_HEADLESS", "true").lower() in ("1", "true", "yes")
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "60000"))

    data_dir: str = os.getenv("SILPO_DATA_DIR", "data")
    db_path: str = os.getenv("SILPO_DB_PATH", "data/silpo.sqlite")
    logs_dir: str = os.getenv("SILPO_LOGS_DIR", "data/logs")
    exports_dir: str = os.getenv("SILPO_EXPORTS_DIR", "data/exports")

    user_agent: str = os.getenv(
        "SILPO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

settings = Settings()

from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    # Category page (dairy)
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )

    # How many pages to scrape
    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))

    # Playwright behavior
    headless: bool = os.getenv("SILPO_HEADLESS", "true").lower() in {"1","true","yes"}
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "60000"))

    # Output paths
    db_path: str = os.getenv("SILPO_DB_PATH", "data/silpo.sqlite")
    logs_dir: str = os.getenv("SILPO_LOGS_DIR", "data/logs")
    exports_dir: str = os.getenv("SILPO_EXPORTS_DIR", "data/exports")
    artifacts_dir: str = os.getenv("SILPO_ARTIFACTS_DIR", "data/artifacts")

    # Optional: try API before HTML (no bypass; only if returns data)
    try_api: bool = os.getenv("SILPO_TRY_API", "false").lower() in {"1","true","yes"}

    user_agent: str = os.getenv(
        "SILPO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

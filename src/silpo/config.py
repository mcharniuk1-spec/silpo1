from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    # Category URL (dairy category URL must be correct for your target)
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )

    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))
    headless: bool = os.getenv("SILPO_HEADLESS", "true").lower() in {"1", "true", "yes"}
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "60000"))

    # Output
    data_dir: str = os.getenv("SILPO_DATA_DIR", "data")
    db_path: str = os.getenv("SILPO_DB_PATH", "data/silpo.sqlite")
    exports_dir: str = os.getenv("SILPO_EXPORTS_DIR", "data/exports")
    logs_dir: str = os.getenv("SILPO_LOGS_DIR", "data/logs")

    # Strategy flags
    # API-first approach: try to discover API calls from browser network; fallback to HTML/DOM parsing.
    use_api_first: bool = os.getenv("SILPO_USE_API_FIRST", "true").lower() in {"1", "true", "yes"}
    use_html_fallback: bool = os.getenv("SILPO_USE_HTML_FALLBACK", "true").lower() in {"1", "true", "yes"}

    user_agent: str = os.getenv(
        "SILPO_USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

settings = Settings()

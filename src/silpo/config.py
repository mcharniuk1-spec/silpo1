from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    """All configuration from environment or defaults"""
    
    # URL & pagination
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )
    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))
    per_page: int = int(os.getenv("SILPO_PER_PAGE", "24"))
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "45000"))
    headless: bool = os.getenv("SILPO_HEADLESS", "true").lower() in {"1", "true", "yes"}

    # Fallback switches (let CI decide)
    use_html_fallback: bool = os.getenv("SILPO_USE_HTML_FALLBACK", "true").lower() in {"1", "true", "yes"}
    use_alt_api: bool = os.getenv("SILPO_USE_ALT_API", "true").lower() in {"1", "true", "yes"}

    # Output directories
    data_dir: str = os.getenv("SILPO_DATA_DIR", "data")
    db_path: str = os.getenv("SILPO_DB_PATH", "data/silpo.sqlite")
    logs_dir: str = os.getenv("SILPO_LOGS_DIR", "data/logs")
    exports_dir: str = os.getenv("SILPO_EXPORTS_DIR", "data/exports")
    debug_dir: str = os.getenv("SILPO_DEBUG_DIR", "data/debug")

    # User-Agent
    user_agent: str = os.getenv(
        "SILPO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

settings = Settings()

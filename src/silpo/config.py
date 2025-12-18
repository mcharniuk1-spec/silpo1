from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    category_url: str = os.getenv(
        "SILPO_CATEGORY_URL",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
    )
    max_pages: int = int(os.getenv("SILPO_MAX_PAGES", "10"))
    timeout_ms: int = int(os.getenv("SILPO_TIMEOUT_MS", "45000"))

    # Output structure (Full-scraper style)
    repo_root: Path = Path(__file__).resolve().parents[2]
    outputs_dir: Path = repo_root / "data" / "outputs"
    debug_dir: Path = repo_root / "data" / "debug"
    db_dir: Path = repo_root / "data" / "db"
    logs_dir: Path = repo_root / "data" / "logs"

    user_agent: str = os.getenv(
        "SILPO_UA",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

settings = Settings()

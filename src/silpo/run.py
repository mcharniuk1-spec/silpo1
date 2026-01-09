import os
import uuid
from datetime import datetime, timezone

from .config import settings
from .logutil import JsonlLogger
from . import db
from .scraper import scrape
from .export import export_csv, export_xlsx

def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def main():
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.logs_dir, exist_ok=True)
    os.makedirs(settings.exports_dir, exist_ok=True)

    run_id = str(uuid.uuid4())
    started = _utc()

    log_path = os.path.join(settings.logs_dir, f"run_{started.replace(':','').replace('-','')[:15]}_{run_id[:8]}.jsonl")
    logger = JsonlLogger(log_path)

    conn = db.connect(settings.db_path)
    db.init(conn)
    db.insert_run(conn, {
        "run_id": run_id,
        "started_at": started,
        "category_url": settings.category_url,
        "max_pages": settings.max_pages,
        "headless": settings.headless,
        "status": "RUNNING",
        "notes": None,
    })

    logger.info("run_start", run_id=run_id, category_url=settings.category_url, max_pages=settings.max_pages, headless=settings.headless)

    status = "OK"
    notes = None
    try:
        rows = scrape(logger, run_id)
        n = db.insert_observations(conn, rows)
        logger.info("db_written", run_id=run_id, observations=n)

        header, data = db.fetch_observations(conn, run_id)
        csv_path = export_csv(settings.exports_dir, header, data)
        xlsx_path = export_xlsx(settings.exports_dir, header, data)
        logger.info("export_done", run_id=run_id, csv=csv_path, xlsx=xlsx_path)

        if n == 0:
            status = "ZERO"
            notes = "No observations extracted. Likely anti-bot challenge or empty payload."
            logger.warn("zero_observations", run_id=run_id, notes=notes)

    except Exception as e:
        status = "ERROR"
        notes = str(e)
        logger.error("run_error", run_id=run_id, error=str(e))

    finished = _utc()
    db.finish_run(conn, run_id, finished, status, notes)
    logger.info("run_finish", run_id=run_id, status=status, finished_at=finished, notes=notes)
    conn.close()

if __name__ == "__main__":
    main()

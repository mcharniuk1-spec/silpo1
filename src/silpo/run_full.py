import os
import uuid

from .config import settings
from .logutil import RunLogger, utc_iso
from .db import connect, init, insert_run, finish_run, insert_products, insert_page_logs, insert_events
from .scraper import scrape
from .exporter import export_xlsx_and_csv

def _ensure_dirs():
    """Create all output directories"""
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.logs_dir, exist_ok=True)
    os.makedirs(settings.exports_dir, exist_ok=True)
    os.makedirs(settings.debug_dir, exist_ok=True)

def main():
    """Main entry point"""
    _ensure_dirs()

    run_id = str(uuid.uuid4())
    started_at = utc_iso()

    jsonl_path = os.path.join(
        settings.logs_dir,
        f"run_{run_id[:8]}_{started_at.replace(':', '').replace('-', '')[:15]}.jsonl"
    )
    logger = RunLogger(jsonl_path)
    logger.info("run_start", f"run_id={run_id} started_at={started_at}")

    conn = connect(settings.db_path)
    init(conn)
    insert_run(conn, run_id, started_at, settings.category_url, settings.max_pages)

    status = "OK"
    note = ""
    
    try:
        rows, page_logs = scrape(run_id, logger)
        n_prod = insert_products(conn, rows)
        insert_page_logs(conn, page_logs)
        insert_events(conn, run_id, logger.events)

        logger.info("db_written", f"products={n_prod} page_logs={len(page_logs)} events={len(logger.events)}")

        latest_xlsx, latest_csv = export_xlsx_and_csv(
            conn, settings.exports_dir, run_id,
            [e.__dict__ for e in logger.events]
        )
        logger.info("export_done", f"xlsx={latest_xlsx} csv={latest_csv}")

        if n_prod == 0:
            status = "ZERO"
            note = "zero_products_saved (possible block/challenge or empty extraction)"
            logger.warn("zero_products", note)

    except Exception as e:
        status = "ERROR"
        note = str(e)[:500]
        logger.error("run_error", note)

    finally:
        finished_at = utc_iso()
        finish_run(conn, run_id, finished_at, status, note)
        logger.info("run_finish", f"run_id={run_id} status={status} finished_at={finished_at}")
        conn.close()

if __name__ == "__main__":
    main()

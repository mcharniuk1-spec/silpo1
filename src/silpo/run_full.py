import os
import uuid
from datetime import datetime, timezone

from .config import settings
from .logutil import RunLogger, utc_iso
from .db import connect, init, insert_run, finish_run, insert_products, insert_page_logs, insert_events, fetch_for_export
from .scraper import scrape
from .exporter import export_all

def ensure_dirs():
    for d in (settings.data_dir, settings.exports_dir, settings.logs_dir):
        os.makedirs(d, exist_ok=True)
        # write check
        test = os.path.join(d, ".write_test")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)

def main():
    ensure_dirs()

    run_id = str(uuid.uuid4())
    started_at = utc_iso()

    log_path = os.path.join(settings.logs_dir, f"run_{run_id[:8]}_{started_at.replace(':','').replace('-','')[:15]}.jsonl")
    logger = RunLogger(log_path)
    logger.info("run_start", f"run_id={run_id} url={settings.category_url} pages={settings.max_pages}")

    conn = connect(settings.db_path)
    init(conn)
    insert_run(conn, run_id, started_at, settings.category_url, settings.max_pages, settings.headless)

    status = "ERROR"
    note = None

    try:
        rows, page_logs = scrape(run_id, logger)

        n_prod = insert_products(conn, rows)
        insert_page_logs(conn, page_logs)
        insert_events(conn, run_id, logger.events)

        logger.info("db_written", f"products={n_prod} pages={len(page_logs)} events={len(logger.events)}")

        (prod_cols, prod_rows, (pl_cols, pl_rows), (ev_cols, ev_rows), run_meta) = fetch_for_export(conn, run_id)

        latest_xlsx, latest_csv = export_all(
            settings.exports_dir,
            run_meta,
            prod_cols, prod_rows,
            pl_cols, pl_rows,
            ev_cols, ev_rows,
        )

        if n_prod == 0:
            status = "ZERO"
            note = "zero_products_saved (possible BLOCK/JS/empty)"
            logger.warn("zero_products", note)
        else:
            status = "OK"
            note = f"saved={n_prod}"

        logger.info("export_done", f"xlsx={latest_xlsx} csv={latest_csv}")

    except Exception as e:
        status = "ERROR"
        note = str(e)[:400]
        logger.error("run_error", note)
        raise
    finally:
        finished_at = utc_iso()
        finish_run(conn, run_id, finished_at, status, note)
        logger.info("run_finish", f"status={status} note={note}")
        conn.close()

if __name__ == "__main__":
    main()

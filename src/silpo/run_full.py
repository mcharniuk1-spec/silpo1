import os
import uuid
from .config import settings
from .logutil import RunLogger, utc_iso
from .db import connect, init, insert_run, finish_run, insert_products, insert_page_logs, insert_events
from .scraper import scrape
from .exporter import export_xlsx_csv

def _ensure_dirs():
    for d in (settings.data_dir, settings.logs_dir, settings.exports_dir):
        os.makedirs(d, exist_ok=True)
        # check write permission
        test = os.path.join(d, ".write_test")
        with open(test, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test)

def main():
    _ensure_dirs()

    run_id = str(uuid.uuid4())
    started = utc_iso()

    log_path = os.path.join(settings.logs_dir, f"run_{run_id[:8]}_{started.replace(':','').replace('-','')[:15]}.jsonl")
    logger = RunLogger(log_path)
    logger.info("run_start", f"run_id={run_id} url={settings.category_url} pages={settings.max_pages}")

    conn = connect(settings.db_path)
    init(conn)
    insert_run(conn, run_id, started, settings.category_url, settings.max_pages, settings.headless)

    status = "ERROR"
    note = ""

    try:
        products, page_logs = scrape(run_id, logger)
        n_prod = insert_products(conn, products)
        n_pl = insert_page_logs(conn, page_logs)
        n_ev = insert_events(conn, run_id, logger.events)

        logger.info("db_written", f"products={n_prod} page_logs={n_pl} events={n_ev}")

        # export ALWAYS (even if 0 products — to see logs + page_logs)
        latest_xlsx, latest_csv = export_xlsx_csv(conn, settings.exports_dir, run_id, [e.__dict__ for e in logger.events])
        logger.info("export_done", f"xlsx={latest_xlsx} csv={latest_csv}")

        if n_prod == 0:
            status = "ZERO"
            note = "0 products saved (possible challenge/block or parsing failure). See logs/page_logs."
            logger.warn("zero_products", note)
        else:
            status = "OK"
            note = f"saved {n_prod} products"

    except Exception as e:
        status = "ERROR"
        note = str(e)[:500]
        logger.error("run_error", note)
        raise  # make workflow red (so you never have “green but empty”)

    finally:
        finished = utc_iso()
        finish_run(conn, run_id, finished, status, note)
        logger.info("run_finish", f"status={status} note={note}")
        conn.close()

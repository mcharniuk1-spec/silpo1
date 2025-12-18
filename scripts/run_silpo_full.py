from datetime import datetime, timezone

from silpo.config import settings
from silpo.log import RunLogger
from silpo.scraper import build_api_template, scrape_pages_via_api
from silpo.sinks.csv_sink import write_csv
from silpo.sinks.xlsx_sink import write_xlsx
from silpo.sinks.sqlite_sink import init_db, insert_rows, log_run

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def main() -> None:
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.debug_dir.mkdir(parents=True, exist_ok=True)
    settings.db_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    run_ts = utc_iso()
    logger = RunLogger(settings.logs_dir / "silpo_run_log.jsonl")
    db_path = settings.db_dir / "silpo.sqlite"
    tpl_cache = settings.debug_dir / "api_template.json"

    init_db(db_path)

    logger.event("START", "silpo_full", f"category={settings.category_url}", {"max_pages": settings.max_pages})
    status = "ok"
    note = ""

    try:
        tpl = build_api_template(
            category_url=settings.category_url,
            user_agent=settings.user_agent,
            timeout_ms=settings.timeout_ms,
            cache_path=tpl_cache,
        )
        logger.event("DISCOVER", "api_template", "ready", {"endpoint": tpl.endpoint, "method": tpl.method})

        rows = scrape_pages_via_api(
            template=tpl,
            category_url=settings.category_url,
            max_pages=settings.max_pages,
            debug_dir=settings.debug_dir,
        )
        logger.event("SCRAPE", "done", f"rows={len(rows)}")

        # outputs (latest)
        out_csv = settings.outputs_dir / "silpo_raw_last.csv"
        out_xlsx = settings.outputs_dir / "silpo_raw_last.xlsx"
        write_csv(out_csv, rows)
        write_xlsx(out_xlsx, rows)
        logger.event("WRITE", "files_last", "saved", {"csv": str(out_csv), "xlsx": str(out_xlsx)})

        # outputs (timestamped snapshot)
        safe_ts = run_ts.replace(":", "-")
        snap_csv = settings.outputs_dir / f"silpo_raw_{safe_ts}.csv"
        snap_xlsx = settings.outputs_dir / f"silpo_raw_{safe_ts}.xlsx"
        write_csv(snap_csv, rows)
        write_xlsx(snap_xlsx, rows)
        logger.event("WRITE", "files_snapshot", "saved", {"csv": str(snap_csv), "xlsx": str(snap_xlsx)})

        # db append
        insert_rows(db_path, rows)
        logger.event("WRITE", "db", "appended", {"db": str(db_path), "rows": len(rows)})

    except Exception as e:
        status = "error"
        note = str(e)
        logger.event("ERROR", "silpo_full", note)
        raise
    finally:
        # log run in db
        try:
            log_run(
                db_path=db_path,
                run_ts=run_ts,
                category_url=settings.category_url,
                max_pages=settings.max_pages,
                rows_written=0,  # precise rows written are in file+log; keep minimal to avoid double count ambiguity
                status=status,
                note=note[:800],
            )
        except Exception:
            pass

        logger.event("DONE", "silpo_full", status)

if __name__ == "__main__":
    main()

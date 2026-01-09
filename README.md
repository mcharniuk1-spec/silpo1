# silpo1 — Full Scraper (dairy category)

This repo scrapes Silpo dairy category pages (default 10 pages) and stores results into:
- SQLite: `data/silpo.sqlite`
- Exports: `data/exports/latest.xlsx` and `data/exports/latest.csv`
- Logs: `data/logs/run_*.jsonl`
- HTML snapshots (only on challenge): `data/html_snapshots/*.html`

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# run (default 10 pages)
python -m scripts.run_silpo_full

## Silpo Full Scraper (CSV/XLSX/SQLite)

Pipeline:
1) Playwright відкриває сторінку категорії та перехоплює API-запит GetCategoryProducts (кешує template).
2) Далі сторінки 1..N качаються напряму через API.
3) Результати зберігаються у:
   - data/outputs/*.csv
   - data/outputs/*.xlsx
   - data/db/silpo.sqlite
   - data/logs/silpo_run_log.jsonl
   - data/debug/*.json (API responses + template)

Run locally:
- pip install -r requirements.txt
- playwright install chromium
- python -m scripts.run_silpo_full

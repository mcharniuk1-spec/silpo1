# Silpo.ua Scraper (Python + Playwright)

Full dairy/eggs product scraper for Silpo.ua using Python 3.11+, Playwright, and SQLite.

## Features

- **Dual source**: API (primary) + HTML fallback
- **Fallback detection**: Cloudflare challenge detection
- **3-tier persistence**: SQLite (history) + XLSX (readable) + CSV (analytics)
- **Structured logging**: JSONL file + Excel logs sheet
- **Environment configurable**: All settings via env vars

## Installation

```bash
pip install -r requirements.txt
python -m playwright install --with-deps chromium

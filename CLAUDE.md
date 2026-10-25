# python-scraping-portfolio

## Commands
- Install: `uv sync` (+ `uv run playwright install chromium` for project 2)
- Tests (offline): `uv run pytest -q`
- Lint/format: `uv run ruff format . && uv run ruff check --fix .`
- Run: `uv run scrape-books`, `uv run scrape-quotes js|scroll|login`, `uv run price-monitor OLD NEW`

## Layout
- `core/` shared: `http.py` (robots.txt, delay, retries), `export.py` (styled xlsx/csv/json), `models.py` (pydantic)
- `projects/<name>/parse.py` pure parsing (tested on `tests/fixtures/*.html`), `scraper.py` CLI + network
- `template/` copy for a new order: edit `config.yaml`, keep `parse_page` pure

## Rules
- Ethics: respect robots.txt, delay >= 1 s, clear User-Agent, no personal data, no captcha/paywall/anti-bot bypass.
- Tests never hit the network: save HTML to `tests/fixtures/` and parse that.
- No secrets in git: only `.env.example`; check `git diff --cached` before push.
- Style: ruff, line length 100, type hints, small functions; English code and comments.

## New order from template
1. Copy `template/` to `orders/<client>/` (or a new repo with `core/`).
2. Check `<site>/robots.txt`, save 1-2 pages to fixtures, fill selectors in `config.yaml`.
3. Make the template test pass on the fixture, then one live run, then `DELIVERY_CHECKLIST.md`.

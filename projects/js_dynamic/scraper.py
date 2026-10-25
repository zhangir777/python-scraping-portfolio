"""quotes.toscrape.com with Playwright: JS-rendered pages, infinite scroll, login form.

uv run scrape-quotes js|scroll|login --out samples/quotes_js
"""

import os
import time
from collections.abc import Callable
from pathlib import Path

import typer
from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright
from pydantic import ValidationError

from core.export import export_all
from core.http import USER_AGENT
from core.logging import setup_logging
from core.models import Quote

from .parse import parse_quotes

BASE = "https://quotes.toscrape.com"
COLUMNS = ["text", "author", "tags"]
log = setup_logging("quotes")
app = typer.Typer(add_completion=False, help="Scrape quotes.toscrape.com with a real browser.")


def scrape_paginated(page: Page, start: str, delay: float) -> list[dict]:
    """Follow the 'Next' link page by page, waiting for JS-rendered quotes."""
    rows, url = [], start
    while url:
        page.goto(url)
        page.wait_for_selector("div.quote")
        found = parse_quotes(page.content())
        rows += found
        log.info("%s: %d quotes", page.url, len(found))
        nxt = page.query_selector("li.next a")
        url = BASE + nxt.get_attribute("href") if nxt else None
        time.sleep(delay)
    return rows


def scrape_scroll(page: Page, delay: float) -> list[dict]:
    """Scroll down until no new quotes appear."""
    page.goto(f"{BASE}/scroll")
    page.wait_for_selector("div.quote")
    count, stable = 0, 0
    while stable < 3:
        page.mouse.wheel(0, 20000)
        time.sleep(delay)
        new_count = page.locator("div.quote").count()
        stable = stable + 1 if new_count == count else 0
        count = new_count
        log.info("Loaded %d quotes", count)
    return parse_quotes(page.content())


def scrape_login(page: Page, delay: float) -> list[dict]:
    load_dotenv()
    page.goto(f"{BASE}/login")
    page.fill("#username", os.getenv("QUOTES_USERNAME") or "demo")
    page.fill("#password", os.getenv("QUOTES_PASSWORD") or "demo")
    page.click("input[type=submit]")
    page.wait_for_selector("a[href='/logout']")
    log.info("Logged in")
    return scrape_paginated(page, f"{BASE}/", delay)


def run(mode: str, scrape: Callable[[Page], list[dict]], out: Path, fmt: str, headed: bool):
    started = time.monotonic()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        page = browser.new_page(user_agent=USER_AGENT)
        try:
            raw = scrape(page)
        except Exception:
            shot = Path("logs") / f"error_{mode}_{int(time.time())}.png"
            page.screenshot(path=str(shot), full_page=True)
            log.exception("Failed, screenshot saved to %s", shot)
            raise
        finally:
            browser.close()

    rows, skipped = [], 0
    for item in raw:
        try:
            rows.append(Quote(**item).model_dump())
        except ValidationError:
            skipped += 1
    files = export_all(
        rows,
        out,
        fmt.split(","),
        COLUMNS,
        sheet_title="Quotes",
        summary={"Records": len(rows), "Skipped": skipped, "Mode": mode},
    )
    log.info("Done: %d quotes, %d skipped, %.0fs", len(rows), skipped, time.monotonic() - started)
    for f in files:
        log.info("Saved %s", f)


OUT = typer.Option(None, help="Output path without extension")
FMT = typer.Option("xlsx,csv", help="xlsx,csv,json")
HEADED = typer.Option(False, "--headed", help="Show the browser window")
DELAY = typer.Option(1.0, help="Seconds between page loads")


@app.command()
def js(out: Path = OUT, format: str = FMT, headed: bool = HEADED, delay: float = DELAY):
    """JS-rendered pages: /js/ with pagination."""
    run(
        "js",
        lambda p: scrape_paginated(p, f"{BASE}/js/", delay),
        out or Path("samples/quotes_js"),
        format,
        headed,
    )


@app.command()
def scroll(out: Path = OUT, format: str = FMT, headed: bool = HEADED, delay: float = DELAY):
    """Infinite scroll: /scroll."""
    run(
        "scroll",
        lambda p: scrape_scroll(p, delay),
        out or Path("samples/quotes_scroll"),
        format,
        headed,
    )


@app.command()
def login(out: Path = OUT, format: str = FMT, headed: bool = HEADED, delay: float = DELAY):
    """Log in via form (credentials from .env), then scrape."""
    run(
        "login",
        lambda p: scrape_login(p, delay),
        out or Path("samples/quotes_login"),
        format,
        headed,
    )


if __name__ == "__main__":
    app()

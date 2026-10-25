"""books.toscrape.com -> Excel / CSV / JSON.

uv run scrape-books --out samples/books --format xlsx,csv,json
"""

import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import typer
from pydantic import ValidationError

from core.export import export_all
from core.http import PoliteClient
from core.logging import setup_logging
from core.models import Book

from .parse import dedupe, parse_detail, parse_list_page

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
COLUMNS = list(Book.model_fields)

app = typer.Typer(add_completion=False)


def build_summary(rows: list[dict]) -> dict:
    prices = [r["price_gbp"] for r in rows]
    by_cat = Counter(r["category"] for r in rows)
    return {
        "Records": len(rows),
        "In stock": sum(r["in_stock"] for r in rows),
        "Min price, GBP": min(prices, default=0),
        "Max price, GBP": max(prices, default=0),
        "Average price, GBP": round(sum(prices) / len(prices), 2) if prices else 0,
        "Collected at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Source": "https://books.toscrape.com",
        "Books per category": dict(sorted(by_cat.items(), key=lambda kv: -kv[1])),
    }


@app.command()
def main(
    out: Path = typer.Option(Path("samples/books"), help="Output path without extension"),
    format: str = typer.Option("xlsx,csv", help="Comma-separated: xlsx,csv,json"),
    delay: float = typer.Option(1.0, help="Seconds between requests (be polite)"),
    max_pages: int = typer.Option(0, help="Stop after N list pages (0 = all)"),
) -> None:
    log = setup_logging("books")
    started = time.monotonic()
    client = PoliteClient(delay=delay)
    rows: list[dict] = []
    skipped = pages = 0
    url: str | None = START_URL
    try:
        while url and (not max_pages or pages < max_pages):
            links, url = parse_list_page(client.get_text(url), url)
            pages += 1
            log.info("Page %d: %d products", pages, len(links))
            for link in links:
                try:
                    raw = parse_detail(client.get_text(link), link)
                    rows.append(Book(**raw).model_dump(mode="json"))
                except (ValidationError, ValueError, AttributeError) as exc:
                    skipped += 1
                    log.warning("Skipped %s: %s", link, str(exc).splitlines()[0])
    finally:
        client.close()

    rows = dedupe(rows)
    files = export_all(
        rows,
        out,
        format.split(","),
        COLUMNS,
        summary=build_summary(rows),
        sheet_title="Books",
        money_cols=["price_gbp"],
        url_cols=["product_url", "image_url"],
    )
    log.info(
        "Done: %d pages, %d records, %d skipped, %d requests, %d errors, %.0fs",
        pages,
        len(rows),
        skipped,
        client.requests,
        client.errors,
        time.monotonic() - started,
    )
    for f in files:
        log.info("Saved %s", f)


if __name__ == "__main__":
    app()

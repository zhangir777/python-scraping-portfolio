"""Template test: parse a saved HTML page offline. Replace the fixture and asserts per order."""

from pathlib import Path

from template.scraper import load_config, parse_page

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "books_list.html"  # TODO: save the client's page here


def test_parse_page():
    cfg = load_config(Path(__file__).with_name("config.yaml"))
    rows, nxt = parse_page(
        FIXTURE.read_text(encoding="utf-8"), "https://books.toscrape.com/catalogue/page-1.html", cfg
    )
    assert len(rows) == 20
    assert rows[0]["title"] == "A Light in the Attic"
    assert rows[0]["price"] == 51.77
    assert all(r["url"].startswith("https://") for r in rows)
    assert nxt and nxt.endswith("page-2.html")

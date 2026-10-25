from pathlib import Path

import pytest

from core.models import Book
from projects.js_dynamic.parse import parse_quotes
from projects.static_catalog.parse import (
    dedupe,
    parse_detail,
    parse_list_page,
    parse_price,
    parse_rating,
    parse_stock,
)

FIX = Path(__file__).parent / "fixtures"
LIST_URL = "https://books.toscrape.com/catalogue/page-1.html"
BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_detail_card():
    book = Book(**parse_detail(read("book_detail.html"), BOOK_URL))
    assert book.title == "A Light in the Attic"
    assert book.category == "Poetry"
    assert book.price_gbp == 51.77
    assert book.rating == 3
    assert book.in_stock and book.stock_count == 22
    assert book.upc == "a897fe39b1053632"
    assert str(book.image_url).startswith("https://books.toscrape.com/media/cache/")


def test_list_page_pagination():
    links, nxt = parse_list_page(read("books_list.html"), LIST_URL)
    assert len(links) == 20
    assert links[0] == BOOK_URL
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"


def test_last_page_has_no_next():
    links, nxt = parse_list_page(
        read("books_list_last.html"), "https://books.toscrape.com/catalogue/page-50.html"
    )
    assert len(links) == 20 and nxt is None


@pytest.mark.parametrize(
    ("text", "value"), [("£51.77", 51.77), ("Â£13.99", 13.99), ("12,50 GBP", 12.5), ("£7", 7.0)]
)
def test_parse_price(text, value):
    assert parse_price(text) == value


def test_parse_price_invalid():
    with pytest.raises(ValueError):
        parse_price("free")


def test_parse_rating():
    assert parse_rating("star-rating Five") == 5
    with pytest.raises(ValueError):
        parse_rating("star-rating")


def test_parse_stock():
    assert parse_stock("In stock (3 available)") == (True, 3)
    assert parse_stock("Out of stock") == (False, 0)


def test_dedupe_by_upc():
    rows = [{"upc": "a", "n": 1}, {"upc": "b"}, {"upc": "a", "n": 2}]
    assert [r["upc"] for r in dedupe(rows)] == ["a", "b"]
    assert dedupe(rows)[0]["n"] == 1


def test_parse_quotes_static_markup():
    quotes = parse_quotes(read("quotes_page.html"))
    assert len(quotes) == 10
    assert quotes[0]["author"] == "Albert Einstein"
    assert quotes[0]["tags"] == ["change", "deep-thoughts", "thinking", "world"]


def test_js_page_has_no_quotes_without_browser():
    # Proves why Playwright is needed: raw HTML of /js/ contains only a <script> with data
    assert parse_quotes(read("quotes_js.html")) == []

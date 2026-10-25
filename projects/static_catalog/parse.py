"""Pure parsing functions for books.toscrape.com (no network, easy to test)."""

import re
from urllib.parse import urljoin

from selectolax.lexbor import LexborHTMLParser as HTMLParser

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_price(text: str) -> float:
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match:
        raise ValueError(f"No price in {text!r}")
    return float(match.group().replace(",", "."))


def parse_rating(class_attr: str) -> int:
    for word in class_attr.split():
        if word in RATINGS:
            return RATINGS[word]
    raise ValueError(f"No rating in {class_attr!r}")


def parse_stock(text: str) -> tuple[bool, int]:
    in_stock = "in stock" in text.lower()
    match = re.search(r"(\d+)\s+available", text)
    return in_stock, int(match.group(1)) if match else 0


def parse_list_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Return (product URLs, next page URL or None)."""
    tree = HTMLParser(html)
    links = [urljoin(page_url, a.attributes["href"]) for a in tree.css("article.product_pod h3 a")]
    nxt = tree.css_first("li.next a")
    return links, urljoin(page_url, nxt.attributes["href"]) if nxt else None


def parse_detail(html: str, url: str) -> dict:
    tree = HTMLParser(html)
    main = tree.css_first("div.product_main")
    table = {
        tr.css_first("th").text(strip=True): tr.css_first("td").text(strip=True)
        for tr in tree.css("table.table-striped tr")
    }
    crumbs = tree.css("ul.breadcrumb li a")
    in_stock, count = parse_stock(main.css_first("p.availability").text())
    img = tree.css_first("#product_gallery img")
    return {
        "title": main.css_first("h1").text(strip=True),
        "category": crumbs[-1].text(strip=True) if len(crumbs) >= 3 else "",
        "price_gbp": parse_price(main.css_first("p.price_color").text()),
        "rating": parse_rating(main.css_first("p.star-rating").attributes.get("class", "")),
        "in_stock": in_stock,
        "stock_count": count,
        "upc": table.get("UPC", ""),
        "product_url": url,
        "image_url": urljoin(url, img.attributes["src"]) if img else "",
    }


def dedupe(rows: list[dict], key: str = "upc") -> list[dict]:
    seen: set = set()
    out = []
    for row in rows:
        if row[key] not in seen:
            seen.add(row[key])
            out.append(row)
    return out

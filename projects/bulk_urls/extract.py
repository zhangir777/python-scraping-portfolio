"""Find title and price on any product page: JSON-LD, meta tags, then per-site CSS selectors."""

import json
import re

from selectolax.lexbor import LexborHTMLParser as HTMLParser

META_PRICE = [
    'meta[property="product:price:amount"]',
    'meta[property="og:price:amount"]',
    '[itemprop="price"]',
]
META_CURRENCY = [
    'meta[property="product:price:currency"]',
    'meta[property="og:price:currency"]',
    '[itemprop="priceCurrency"]',
]
SYMBOLS = {"£": "GBP", "$": "USD", "€": "EUR", "₸": "KZT", "₽": "RUB"}


def parse_price(text: str | float | int | None) -> float | None:
    """'£1,299.50' / '1 299,50 €' / 51.77 -> float."""
    if isinstance(text, int | float):
        return float(text)
    m = re.search(r"\d[\d\s.,]*", text or "")
    if not m:
        return None
    num = re.sub(r"\s", "", m.group()).rstrip(".,")
    if "," in num and "." in num:  # the last separator is the decimal one
        num = num.replace(",", "") if num.rfind(".") > num.rfind(",") else num.replace(".", "")
    if "," in num:  # '1299,50' decimal comma, '1,299' thousands
        head, _, tail = num.rpartition(",")
        num = f"{head.replace(',', '')}.{tail}" if len(tail) != 3 else num.replace(",", "")
    return float(num.replace(",", ""))


def _currency(text: str) -> str:
    return next((code for sym, code in SYMBOLS.items() if sym in text), "")


def _products(data) -> list[dict]:
    """All schema.org Product objects in a JSON-LD block (handles lists and @graph)."""
    if isinstance(data, list):
        return [p for item in data for p in _products(item)]
    if not isinstance(data, dict):
        return []
    found = [data] if "Product" in str(data.get("@type", "")) else []
    return found + _products(data.get("@graph", []))


def from_json_ld(tree: HTMLParser) -> dict | None:
    for node in tree.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.text())
        except json.JSONDecodeError:
            continue
        for product in _products(data):
            offers = product.get("offers") or {}
            offer = offers[0] if isinstance(offers, list) and offers else offers
            price = offer.get("price") or offer.get("lowPrice")
            if price is None and offer.get("priceSpecification"):
                spec = offer["priceSpecification"]
                price = (spec[0] if isinstance(spec, list) else spec).get("price")
            if price is not None:
                return {
                    "title": product.get("name", ""),
                    "price": parse_price(price),
                    "currency": offer.get("priceCurrency", ""),
                    "method": "json-ld",
                }
    return None


def _attr_or_text(tree: HTMLParser, selectors: list[str]) -> str:
    for sel in selectors:
        node = tree.css_first(sel)
        if node:
            return (node.attributes.get("content") or node.text()).strip()
    return ""


def extract_price(html: str, selectors: dict | None = None) -> dict:
    """Return {title, price, currency, method}; price is None when nothing was found."""
    tree = HTMLParser(html)
    title_node = tree.css_first("h1") or tree.css_first("title")
    title = title_node.text().strip() if title_node else ""

    if selectors:  # a site config beats generic guesses
        raw = _attr_or_text(tree, [selectors["price"]])
        if raw:
            found = _attr_or_text(tree, [selectors["title"]]) if "title" in selectors else ""
            return {
                "title": found or title,
                "price": parse_price(raw),
                "currency": selectors.get("currency") or _currency(raw),
                "method": "selector",
            }
    if found := from_json_ld(tree):
        found["title"] = found["title"] or title
        return found
    raw = _attr_or_text(tree, META_PRICE)
    if raw:
        cur = _attr_or_text(tree, META_CURRENCY) or _currency(raw)
        return {"title": title, "price": parse_price(raw), "currency": cur, "method": "meta"}
    return {"title": title, "price": None, "currency": "", "method": ""}

"""Product catalog spider (books.toscrape.com): same fields as projects/static_catalog,
runs in Scrapy Cloud on a schedule and exports JSON/CSV/XML from the dashboard."""

import re

import scrapy

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            yield response.follow(href, self.parse_book)
        if nxt := response.css("li.next a::attr(href)").get():
            yield response.follow(nxt, self.parse)

    def parse_book(self, response):
        crumbs = response.css("ul.breadcrumb li a::text").getall()
        stock = " ".join(response.css("p.availability::text").getall())
        count = re.search(r"(\d+)\s+available", stock)
        rating_cls = response.css("p.star-rating::attr(class)").get("")
        table = {
            tr.css("th::text").get(): tr.css("td::text").get()
            for tr in response.css("table.table-striped tr")
        }
        try:
            price = float(
                re.search(r"\d+(?:\.\d+)?", response.css("p.price_color::text").get()).group()
            )
        except (AttributeError, ValueError):
            self.logger.warning("no price on %s, skipped", response.url)
            return
        yield {
            "title": response.css("div.product_main h1::text").get(),
            "category": crumbs[-1] if len(crumbs) >= 3 else "",
            "price_gbp": price,
            "rating": next((RATINGS[w] for w in rating_cls.split() if w in RATINGS), None),
            "in_stock": "in stock" in stock.lower(),
            "stock_count": int(count.group(1)) if count else 0,
            "upc": table.get("UPC", ""),
            "product_url": response.url,
            "image_url": response.urljoin(response.css("#product_gallery img::attr(src)").get("")),
        }

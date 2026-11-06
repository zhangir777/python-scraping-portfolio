from scrapy.exceptions import DropItem


class DedupePipeline:
    """Drop books whose UPC was already scraped in this run."""

    def open_spider(self, spider):
        self.seen = set()

    def process_item(self, item, spider):
        if item["upc"] in self.seen:
            raise DropItem(f"duplicate {item['upc']}")
        self.seen.add(item["upc"])
        return item

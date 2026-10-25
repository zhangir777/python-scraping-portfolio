from selectolax.lexbor import LexborHTMLParser as HTMLParser


def parse_quotes(html: str) -> list[dict]:
    """Parse rendered quotes.toscrape.com HTML (same markup on /js/, /scroll and after login)."""
    out = []
    for q in HTMLParser(html).css("div.quote"):
        out.append(
            {
                "text": q.css_first("span.text").text(strip=True),
                "author": q.css_first("small.author").text(strip=True),
                "tags": [t.text(strip=True) for t in q.css("a.tag")],
            }
        )
    return out

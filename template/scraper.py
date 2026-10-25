"""Config-driven list-page scraper. Copy this folder for a new order and edit config.yaml.

Run from the repo root: uv run python template/scraper.py [path/to/config.yaml]
"""

import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import yaml
from selectolax.lexbor import LexborHTMLParser as HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.export import export_all  # noqa: E402
from core.http import PoliteClient  # noqa: E402
from core.logging import setup_logging  # noqa: E402


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def extract(node, spec: dict, page_url: str):
    el = node.css_first(spec["css"])
    if el is None:
        return None
    value = el.attributes.get(spec["attr"]) if "attr" in spec else el.text(strip=True)
    kind = spec.get("type")
    if value is None:
        return None
    if kind == "url":
        return urljoin(page_url, value)
    if kind == "price":
        m = re.search(r"\d+(?:[.,]\d+)?", value.replace(" ", ""))
        return float(m.group().replace(",", ".")) if m else None
    if kind == "int":
        m = re.search(r"\d+", value)
        return int(m.group()) if m else None
    return value


def parse_page(html: str, page_url: str, cfg: dict) -> tuple[list[dict], str | None]:
    # TODO: selectors live in config.yaml; add custom per-site cleanup here if needed
    tree = HTMLParser(html)
    rows = [
        {name: extract(node, spec, page_url) for name, spec in cfg["fields"].items()}
        for node in tree.css(cfg["item"])
    ]
    nxt = tree.css_first(cfg["next_page"]) if cfg.get("next_page") else None
    return rows, urljoin(page_url, nxt.attributes["href"]) if nxt else None


def main(config_path: Path) -> None:
    cfg = load_config(config_path)
    log = setup_logging("template")
    client = PoliteClient(delay=cfg.get("delay_seconds", 1.0))
    rows: list[dict] = []
    try:
        for url in cfg["start_urls"]:
            pages = 0
            while url and (not cfg.get("max_pages") or pages < cfg["max_pages"]):
                found, url = parse_page(client.get_text(url), url, cfg)
                pages += 1
                rows += found
                log.info("Page %d: %d rows", pages, len(found))
    finally:
        client.close()

    key, seen, unique = cfg.get("dedupe_key"), set(), []
    for row in rows:
        if key and row.get(key) in seen:
            continue
        seen.add(row.get(key))
        unique.append(row)
    empty = sum(1 for r in unique if any(v in (None, "") for v in r.values()))
    files = export_all(
        unique,
        Path(cfg["output"]),
        cfg["formats"],
        list(cfg["fields"]),
        summary={"Records": len(unique), "Rows with empty fields": empty},
        money_cols=cfg.get("money_fields", []),
        url_cols=cfg.get("url_fields", []),
    )
    log.info("Done: %d rows (%d with empty fields) -> %s", len(unique), empty, files)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("config.yaml"))

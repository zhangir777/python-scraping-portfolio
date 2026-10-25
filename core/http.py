"""Polite HTTP client: robots.txt, rate limit, retries with exponential backoff."""

import logging
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "PortfolioScraper/1.0 (+https://github.com/zhangir777/python-scraping-portfolio)"
log = logging.getLogger(__name__)


class RobotsDisallowed(Exception):
    pass


class PoliteClient:
    def __init__(self, delay: float = 1.0, retries: int = 3, timeout: float = 20.0):
        self.delay = delay
        self.retries = retries
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True
        )
        self._robots: dict[str, RobotFileParser] = {}
        self._last = 0.0
        self.requests = 0
        self.errors = 0

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = RobotFileParser()
            try:
                resp = self.client.get(urljoin(base, "/robots.txt"))
                # No robots.txt (4xx) means everything is allowed
                rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
            except httpx.HTTPError:
                rp.parse([])
            self._robots[base] = rp
        return self._robots[base].can_fetch(USER_AGENT, url)

    def _wait(self) -> None:
        pause = self.delay - (time.monotonic() - self._last)
        if pause > 0:
            time.sleep(pause)
        self._last = time.monotonic()

    def get_text(self, url: str) -> str:
        if not self.allowed(url):
            raise RobotsDisallowed(url)
        for attempt in range(self.retries + 1):
            self._wait()
            self.requests += 1
            try:
                resp = self.client.get(url)
            except httpx.HTTPError as exc:
                log.warning("%s on %s", type(exc).__name__, url)
            else:
                if resp.status_code < 500 and resp.status_code != 429:
                    if resp.is_error:
                        self.errors += 1
                        resp.raise_for_status()
                    return resp.content.decode("utf-8", errors="replace")
                log.warning("HTTP %s on %s", resp.status_code, url)
            if attempt < self.retries:
                time.sleep(2**attempt)
        self.errors += 1
        raise httpx.HTTPError(f"Failed after {self.retries + 1} attempts: {url}")

    def close(self) -> None:
        self.client.close()

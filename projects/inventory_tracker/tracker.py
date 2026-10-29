"""One-click inventory tracker: scrape -> save snapshot -> compare with last run -> open report.

uv run inventory-tracker            (or double-click run_tracker.bat / run_tracker.command)
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import typer

from core.logging import setup_logging
from projects.price_monitor.compare import compare
from projects.price_monitor.monitor import read_csv, write_report
from projects.static_catalog.scraper import main as scrape_books

app = typer.Typer(add_completion=False)


def previous_snapshot(history: Path, current: Path) -> Path | None:
    """Latest snapshot older than `current` (names are timestamps, so they sort)."""
    older = sorted(p for p in history.glob("*.csv") if p.name < current.name)
    return older[-1] if older else None


def track(data_dir: Path, scrape: Callable[[Path], None], now: datetime) -> tuple[Path, dict]:
    """Run one cycle and return (report path, summary)."""
    history = data_dir / "history"
    history.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d_%H%M")
    scrape(data_dir / "catalog_latest")  # writes catalog_latest.xlsx + .csv
    current = history / f"{stamp}.csv"
    shutil.copy(data_dir / "catalog_latest.csv", current)

    prev = previous_snapshot(history, current)
    if prev is None:
        return data_dir / "catalog_latest.xlsx", {"First run": "baseline saved, run again later"}
    changes = compare(read_csv(prev), read_csv(current))
    report = write_report(changes, data_dir / "reports" / f"changes_{stamp}.xlsx")
    return report, {"Compared with": prev.stem, **changes.summary()}


def open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", path], check=False)


@app.command()
def main(
    data_dir: Path = typer.Option(Path("tracker_data"), help="Snapshots and reports folder"),
    max_pages: int = typer.Option(0, help="Stop after N list pages (0 = all)"),
    delay: float = typer.Option(1.0, help="Seconds between requests"),
    open_report: bool = typer.Option(True, "--open/--no-open", help="Open the report when done"),
) -> None:
    log = setup_logging("tracker")

    def scrape(out: Path) -> None:
        scrape_books(out=out, format="xlsx,csv", delay=delay, max_pages=max_pages)

    report, summary = track(data_dir, scrape, datetime.now())
    for k, v in summary.items():
        log.info("%s: %s", k, v)
    log.info("Report: %s", report.resolve())
    if open_report:
        open_file(report)


if __name__ == "__main__":
    app()

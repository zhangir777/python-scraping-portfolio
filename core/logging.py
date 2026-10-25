import logging
from pathlib import Path


def setup_logging(name: str, log_dir: Path = Path("logs")) -> logging.Logger:
    """Log to console and to logs/<name>.log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    for handler in (
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8"),
    ):
        handler.setFormatter(fmt)
        root.addHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger(name)

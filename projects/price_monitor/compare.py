"""Compare two catalog snapshots (pure logic, no I/O)."""

from dataclasses import dataclass, field


@dataclass
class Changes:
    added: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    price: list[dict] = field(default_factory=list)
    stock: list[dict] = field(default_factory=list)

    def summary(self) -> dict:
        up = sum(1 for c in self.price if c["diff"] > 0)
        return {
            "New products": len(self.added),
            "Removed products": len(self.removed),
            "Price changes": len(self.price),
            "  price up": up,
            "  price down": len(self.price) - up,
            "Stock status changes": len(self.stock),
        }


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def compare(
    old: list[dict], new: list[dict], key: str = "upc", price: str = "price_gbp"
) -> Changes:
    old_by = {r[key]: r for r in old}
    new_by = {r[key]: r for r in new}
    ch = Changes(
        added=[new_by[k] for k in new_by.keys() - old_by.keys()],
        removed=[old_by[k] for k in old_by.keys() - new_by.keys()],
    )
    for k in sorted(old_by.keys() & new_by.keys()):
        o, n = old_by[k], new_by[k]
        op, np_ = float(o[price]), float(n[price])
        if op != np_:
            ch.price.append(
                {
                    key: k,
                    "title": n.get("title", ""),
                    "old_price": op,
                    "new_price": np_,
                    "diff": round(np_ - op, 2),
                    "diff_pct": round((np_ - op) / op, 4) if op else 0.0,
                    "product_url": n.get("product_url", ""),
                }
            )
        if _bool(o.get("in_stock")) != _bool(n.get("in_stock")):
            ch.stock.append(
                {
                    key: k,
                    "title": n.get("title", ""),
                    "was_in_stock": _bool(o.get("in_stock")),
                    "now_in_stock": _bool(n.get("in_stock")),
                    "product_url": n.get("product_url", ""),
                }
            )
    ch.price.sort(key=lambda c: -abs(c["diff_pct"]))
    return ch

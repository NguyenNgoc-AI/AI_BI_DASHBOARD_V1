"""Return renderer-neutral chart specifications for the frontend."""

from collections import defaultdict


def _series(rows: list[dict], dimension: str) -> tuple[list[str], list[float]]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[str(row.get(dimension, "Unknown"))] += float(row["revenue"])
    labels = sorted(totals)
    return labels, [totals[label] for label in labels]


def revenue_by_date(rows: list[dict]) -> list[dict[str, str | float]]:
    labels, values = _series(rows, "date")
    return [{"date": label, "revenue": value} for label, value in zip(labels, values)]


def revenue_trend(rows: list[dict]) -> dict:
    labels, values = _series(rows, "date")
    return {"type": "line", "title": "Revenue by Date", "x": labels, "series": [{"name": "Revenue", "data": values}]}


def top_products(rows: list[dict], limit: int = 10) -> dict:
    labels, values = _series(rows, "product")
    ranked = sorted(zip(labels, values), key=lambda item: item[1], reverse=True)[:limit]
    return {"type": "bar", "title": "Top Products", "x": [x for x, _ in ranked], "series": [{"name": "Revenue", "data": [y for _, y in ranked]}]}


def revenue_composition(rows: list[dict], dimension: str = "product") -> dict:
    labels, values = _series(rows, dimension)
    return {"type": "pie", "title": f"Revenue by {dimension.title()}", "labels": labels, "values": values}


def generate_charts(rows: list[dict]) -> list[dict]:
    return [revenue_trend(rows), top_products(rows), revenue_composition(rows, "product")]

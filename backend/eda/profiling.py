"""Small, deterministic dataset profiler."""

from statistics import mean, stdev
from typing import Any


def profile_column(values: list[Any]) -> dict[str, Any]:
    present = [value for value in values if value is not None]
    result: dict[str, Any] = {
        "count": len(present),
        "null_count": len(values) - len(present),
        "null_rate": (len(values) - len(present)) / len(values) if values else 0.0,
        "unique_count": len({str(value) for value in present}),
    }
    numeric = [float(value) for value in present if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if present and len(numeric) == len(present):
        result.update({
            "type": "numeric",
            "mean": mean(numeric),
            "std": stdev(numeric) if len(numeric) > 1 else 0.0,
            "min": min(numeric),
            "max": max(numeric),
        })
    else:
        result["type"] = "categorical"
    return result


def profile_dataset(rows: list[dict]) -> dict:
    columns = sorted(set().union(*(row.keys() for row in rows))) if rows else []
    return {"row_count": len(rows), "columns": {column: profile_column([row.get(column) for row in rows]) for column in columns}}

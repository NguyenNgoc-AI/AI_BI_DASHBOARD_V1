"""Quality checks report issues; they never silently delete rows."""

from collections import Counter
from typing import Any

from backend.schema_learning.rule_parser import evaluate_rules


def find_missing(rows: list[dict]) -> dict:
    missing_rows = sum(any(value in (None, "") for value in row.values()) for row in rows)
    return {"rows": missing_rows, "rate": missing_rows / len(rows) if rows else 0.0}


def find_duplicates(rows: list[dict], key: str = "order_id") -> dict:
    counts = Counter(row.get(key) for row in rows)
    duplicates = sum(count - 1 for value, count in counts.items() if value is not None and count > 1)
    return {"rows": duplicates, "rate": duplicates / len(rows) if rows else 0.0}


def find_outliers(values: list[Any]) -> dict:
    numbers = sorted(float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool))
    if len(numbers) < 4:
        return {"count": 0, "values": []}
    midpoint = len(numbers) // 2
    lower, upper = numbers[:midpoint], numbers[(len(numbers) + 1) // 2 :]
    median = lambda seq: (seq[(len(seq) - 1) // 2] + seq[len(seq) // 2]) / 2
    q1, q3 = median(lower), median(upper)
    low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    found = [value for value in numbers if value < low or value > high]
    return {"count": len(found), "values": found, "lower_bound": low, "upper_bound": high}


def check_quality(rows: list[dict], rules: list[dict] | None = None) -> dict:
    missing = find_missing(rows)
    duplicates = find_duplicates(rows)
    validity = evaluate_rules(rows, rules or [])
    invalid_rate = 1.0 - validity["rate"]
    score = max(0.0, 1.0 - missing["rate"] * 0.4 - duplicates["rate"] * 0.3 - invalid_rate * 0.3)
    numeric_columns = sorted({key for row in rows for key, value in row.items() if isinstance(value, (int, float)) and not isinstance(value, bool)})
    return {
        "score": score,
        "valid": validity,
        "missing": missing,
        "duplicates": duplicates,
        "outliers": {column: find_outliers([row.get(column) for row in rows]) for column in numeric_columns},
    }

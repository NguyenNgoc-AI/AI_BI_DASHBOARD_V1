"""Quality checks report issues; they never silently delete rows."""

from collections import Counter
import math
from typing import Any

from backend.schema_learning.rule_parser import evaluate_rules
from semantic.business_rules import DEFAULT_RULE_ENGINE
from semantic.schema_definition import inspect_and_map_columns


def find_missing(rows: list[dict]) -> dict:
    missing_rows = sum(any(value in (None, "") for value in row.values()) for row in rows)
    return {"rows": missing_rows, "rate": missing_rows / len(rows) if rows else 0.0}


def _resolve_duplicate_key(rows: list[dict], default_key: str = "order_id") -> str:
    if not rows:
        return default_key
    headers = list(dict.fromkeys(key for row in rows for key in row.keys()))
    roles = inspect_and_map_columns(headers)["roles"]
    if roles.get("sales_id") and roles["sales_id"] in headers:
        return roles["sales_id"]
    if default_key in headers:
        return default_key
    return roles.get("order_id") or default_key


def find_duplicates(rows: list[dict], key: str = "order_id") -> dict:
    resolved_key = _resolve_duplicate_key(rows, key) if key == "order_id" else key
    counts = Counter(row.get(resolved_key) for row in rows)
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


def _evaluate_semantic_rules(rows: list[dict]) -> dict:
    if not rows:
        return {"valid_rows": 0, "invalid_rows": 0, "rate": 1.0}
    headers = list(dict.fromkeys(key for row in rows for key in row.keys()))
    mapping = inspect_and_map_columns(headers)["columns"]
    # Map matched canonical column names to original row keys
    canonical_to_raw = {
        meta["matched_column"]: raw_col
        for raw_col, meta in mapping.items()
        if meta.get("matched_column")
    }
    hard_rules = [r for r in DEFAULT_RULE_ENGINE.spec.hard_constraints]
    safe_globals = {"__builtins__": None}
    base_ctx = {
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "math": math,
        "where": lambda cond, a, b: a if cond else b,
        "clip": lambda v, low, high: max(low, min(high, v)),
        "maximum": max,
        "minimum": min,
    }
    valid_rows = 0
    for row in rows:
        ctx = dict(base_ctx)
        for k, v in row.items():
            ctx[k] = v
        for canonical_col, raw_col in canonical_to_raw.items():
            if raw_col in row and canonical_col not in ctx:
                ctx[canonical_col] = row[raw_col]
        row_ok = True
        for rule in hard_rules:
            try:
                if not bool(eval(rule.expression, safe_globals, ctx)):
                    row_ok = False
                    break
            except Exception:
                # Rule references columns not present in this dataset
                continue
        if row_ok:
            valid_rows += 1
    return {
        "valid_rows": valid_rows,
        "invalid_rows": len(rows) - valid_rows,
        "rate": valid_rows / len(rows) if rows else 1.0,
    }


def check_quality(rows: list[dict], rules: list[dict] | None = None) -> dict:
    missing = find_missing(rows)
    duplicates = find_duplicates(rows)
    validity = evaluate_rules(rows, rules) if rules is not None else _evaluate_semantic_rules(rows)
    invalid_rate = 1.0 - validity["rate"]
    score = max(0.0, 1.0 - missing["rate"] * 0.4 - duplicates["rate"] * 0.3 - invalid_rate * 0.3)
    ordered_keys = list(dict.fromkeys(key for row in rows for key in row.keys())) if rows else []
    numeric_columns = [
        key
        for key in ordered_keys
        if any(isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool) for row in rows)
    ]
    return {
        "score": score,
        "valid": validity,
        "missing": missing,
        "duplicates": duplicates,
        "outliers": {column: find_outliers([row.get(column) for row in rows]) for column in numeric_columns},
    }

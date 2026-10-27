"""Infer simple column types and numeric correlations."""

from datetime import date
import math
from typing import Any


def infer_value_type(value: Any) -> str:
    if value is None or value == "":
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    try:
        date.fromisoformat(str(value))
        return "date"
    except ValueError:
        return "string"


def infer_column_type(values: list[Any]) -> str:
    types = {infer_value_type(value) for value in values} - {"null"}
    if not types:
        return "null"
    if types <= {"integer", "float"}:
        return "float" if "float" in types else "integer"
    return next(iter(types)) if len(types) == 1 else "string"


def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean, y_mean = sum(xs) / len(xs), sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    return numerator / denominator if denominator else None


def infer_relationships(rows: list[dict]) -> list[dict]:
    numeric = sorted({key for row in rows for key, value in row.items() if isinstance(value, (int, float)) and not isinstance(value, bool)})
    relationships = []
    for index, left in enumerate(numeric):
        for right in numeric[index + 1 :]:
            pairs = [(float(row[left]), float(row[right])) for row in rows if isinstance(row.get(left), (int, float)) and isinstance(row.get(right), (int, float))]
            value = pearson_correlation([x for x, _ in pairs], [y for _, y in pairs]) if pairs else None
            if value is not None:
                relationships.append({"left": left, "right": right, "type": "correlation", "value": value})
    return relationships


def infer_schema(rows: list[dict]) -> dict:
    columns = sorted(set().union(*(row.keys() for row in rows))) if rows else []
    return {
        "columns": {
            column: {
                "type": infer_column_type([row.get(column) for row in rows]),
                "nullable": any(row.get(column) in (None, "") for row in rows),
            }
            for column in columns
        },
        "relationships": infer_relationships(rows),
    }


def infer_database_schema(tables: dict[str, list[dict]]) -> dict:
    if not tables:
        raise ValueError("At least one table is required")
    table_schemas = {name: infer_schema(rows) for name, rows in tables.items()}
    primary_keys: dict[str, list[str]] = {}
    for table_name, rows in tables.items():
        primary_keys[table_name] = []
        if not rows:
            continue
        singular_name = table_name[:-1] if table_name.endswith("s") else table_name
        preferred_names = {"id", f"{singular_name}_id"}
        for column in table_schemas[table_name]["columns"]:
            values = [row.get(column) for row in rows]
            if all(value not in (None, "") for value in values) and len(set(map(str, values))) == len(values):
                if column in preferred_names:
                    primary_keys[table_name].append(column)

    foreign_keys = []
    for child_name, child_rows in tables.items():
        child_columns = table_schemas[child_name]["columns"]
        for parent_name, parent_rows in tables.items():
            if child_name == parent_name:
                continue
            for key in primary_keys[parent_name]:
                if key not in child_columns:
                    continue
                parent_values = {str(row[key]) for row in parent_rows if row.get(key) not in (None, "")}
                child_values = {str(row[key]) for row in child_rows if row.get(key) not in (None, "")}
                if child_values and child_values <= parent_values:
                    foreign_keys.append(
                        {
                            "child_table": child_name,
                            "child_column": key,
                            "parent_table": parent_name,
                            "parent_column": key,
                            "coverage": 1.0,
                        }
                    )
    return {"tables": table_schemas, "primary_key_candidates": primary_keys, "foreign_keys": foreign_keys}

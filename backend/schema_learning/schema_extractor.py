"""Infer column types, semantic metadata (38-column knowledge base), and numeric correlations."""

from datetime import date, datetime
import math
from typing import Any

import numpy as np

from semantic.schema_definition import inspect_and_map_columns


def _is_iso_date_or_datetime(text: str) -> bool:
    n = len(text)
    if n < 8:
        return False
    if n >= 10 and text[4] == "-" and text[7] == "-":
        if n == 10:
            try:
                date.fromisoformat(text)
                return True
            except ValueError:
                return False
        try:
            normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
            datetime.fromisoformat(normalized)
            return True
        except ValueError:
            return False
    if "/" in text[:5] and n <= 22:
        try:
            from backend.dashboard_engine.data_pipeline import _parse_slash_date
            _parse_slash_date(text)
            return True
        except Exception:
            return False
    return False


def infer_value_type(value: Any) -> str:
    if value is None or value == "":
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    text = str(value).strip()
    if _is_iso_date_or_datetime(text):
        return "date"
    return "string"


def infer_column_type(values: list[Any]) -> str:
    has_int = False
    has_float = False
    has_bool = False
    has_date = False
    has_string = False

    for value in values:
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            has_bool = True
        elif isinstance(value, int):
            has_int = True
        elif isinstance(value, float):
            has_float = True
        else:
            if has_string:
                continue
            text = str(value).strip()
            if _is_iso_date_or_datetime(text):
                has_date = True
            else:
                has_string = True
                if has_int or has_float or has_bool or has_date:
                    return "string"

    types: set[str] = set()
    if has_int:
        types.add("integer")
    if has_float:
        types.add("float")
    if has_bool:
        types.add("boolean")
    if has_date:
        types.add("date")
    if has_string:
        types.add("string")

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


def _ordered_columns(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    first_keys = list(rows[0].keys())
    if all(len(row) == len(first_keys) for row in rows[:20]):
        return list(dict.fromkeys(k for row in rows for k in row.keys()))
    return list(dict.fromkeys(k for row in rows for k in row.keys()))


def infer_relationships(rows: list[dict]) -> list[dict]:
    if len(rows) < 2:
        return []
    columns = _ordered_columns(rows)
    numeric: list[str] = []
    for key in columns:
        for row in rows:
            val = row.get(key)
            if val is not None and val != "":
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    numeric.append(key)
                break

    if len(numeric) < 2:
        return []

    n_rows = len(rows)
    n_cols = len(numeric)
    matrix = np.full((n_cols, n_rows), np.nan, dtype=np.float64)
    has_nan = False

    for col_idx, key in enumerate(numeric):
        col_vals = [row.get(key) for row in rows]
        try:
            arr = np.asarray(col_vals, dtype=np.float64)
            matrix[col_idx] = arr
            if np.isnan(arr).any():
                has_nan = True
        except (TypeError, ValueError):
            has_nan = True
            for row_idx, v in enumerate(col_vals):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    matrix[col_idx, row_idx] = float(v)

    relationships: list[dict] = []
    if not has_nan:
        means = matrix.mean(axis=1, keepdims=True)
        centered = matrix - means
        ss = np.sqrt(np.sum(centered * centered, axis=1))
        for i in range(n_cols):
            if ss[i] == 0.0:
                continue
            left = numeric[i]
            ci = centered[i]
            ssi = ss[i]
            for j in range(i + 1, n_cols):
                if ss[j] == 0.0:
                    continue
                denom = ssi * ss[j]
                if denom > 0.0:
                    corr = float(np.dot(ci, centered[j]) / denom)
                    relationships.append({"left": left, "right": numeric[j], "type": "correlation", "value": corr})
        return relationships

    valid_masks = ~np.isnan(matrix)
    for i in range(n_cols):
        left = numeric[i]
        vi = valid_masks[i]
        xi = matrix[i]
        for j in range(i + 1, n_cols):
            joint = vi & valid_masks[j]
            if int(joint.sum()) < 2:
                continue
            xs = xi[joint]
            ys = matrix[j][joint]
            dx = xs - xs.mean()
            dy = ys - ys.mean()
            denom = float(np.sqrt(np.dot(dx, dx) * np.dot(dy, dy)))
            if denom > 0.0:
                corr = float(np.dot(dx, dy) / denom)
                relationships.append({"left": left, "right": numeric[j], "type": "correlation", "value": corr})
    return relationships


def infer_schema(rows: list[dict]) -> dict:
    columns = _ordered_columns(rows)
    semantic_info = inspect_and_map_columns(columns)["columns"] if columns else {}
    return {
        "columns": {
            column: {
                "type": infer_column_type([row.get(column) for row in rows]),
                "nullable": any(row.get(column) in (None, "") for row in rows),
                "semantic_type": semantic_info.get(column, {}).get("semantic_type", "custom"),
                "matched_column": semantic_info.get(column, {}).get("matched_column"),
                "matched_table": semantic_info.get(column, {}).get("matched_table"),
                "unit": semantic_info.get(column, {}).get("unit"),
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

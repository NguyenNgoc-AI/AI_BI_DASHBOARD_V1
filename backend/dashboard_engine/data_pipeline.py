"""Read and normalize the small canonical e-commerce dataset."""

import csv
import io
import json
import math
import re
from datetime import date
from typing import Any

REQUIRED_COLUMNS = {"date", "order_id", "product", "revenue", "cost"}
MAX_COLUMNS = 100


def _column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def read_csv(content: bytes) -> list[dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("CSV must use UTF-8 encoding") from error
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if not reader.fieldnames or any(not name.strip() for name in reader.fieldnames):
        raise ValueError("CSV headers must not be empty")
    normalized = [_column_name(name) for name in reader.fieldnames]
    if len(normalized) != len(set(normalized)):
        raise ValueError("CSV contains duplicate headers")
    if len(normalized) > MAX_COLUMNS:
        raise ValueError(f"Dataset exceeds the {MAX_COLUMNS}-column limit")
    try:
        return [{_column_name(key): value for key, value in row.items()} for row in reader]
    except csv.Error as error:
        raise ValueError(f"Malformed CSV: {error}") from error


def read_json(content: bytes) -> list[dict[str, Any]]:
    try:
        value = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Malformed UTF-8 JSON") from error
    if isinstance(value, dict) and set(value) == {"data"}:
        value = value["data"]
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("JSON must be an array of flat objects")
    if any(any(isinstance(cell, (dict, list)) for cell in row.values()) for row in value):
        raise ValueError("Nested JSON values are not supported")
    return [{_column_name(str(key)): cell for key, cell in row.items()} for row in value]


def validate_required_columns(rows: list[dict[str, Any]], required: set[str] = REQUIRED_COLUMNS) -> None:
    if not rows:
        raise ValueError("Dataset is empty")
    all_columns = set().union(*(row.keys() for row in rows))
    missing = required - all_columns
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")


def coerce_ecommerce_types(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    numeric_optional = {"quantity", "ad_spend", "new_customers"}
    for index, row in enumerate(rows, start=1):
        item = {key: (None if value == "" else value) for key, value in row.items()}
        try:
            item["date"] = date.fromisoformat(str(item["date"])).isoformat()
            item["revenue"] = float(item["revenue"])
            item["cost"] = float(item["cost"])
            for key in numeric_optional & item.keys():
                if item[key] is not None:
                    item[key] = float(item[key])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Invalid value at row {index}: {error}") from error
        numeric_values = [item["revenue"], item["cost"]] + [item[key] for key in numeric_optional & item.keys() if item[key] is not None]
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError(f"Numeric values must be finite at row {index}")
        if item["revenue"] < 0 or item["cost"] < 0:
            raise ValueError(f"Revenue and cost must be non-negative at row {index}")
        if not str(item["order_id"]).strip() or not str(item["product"]).strip():
            raise ValueError(f"order_id and product are required at row {index}")
        item["order_id"] = str(item["order_id"]).strip()
        item["product"] = str(item["product"]).strip()
        converted.append(item)
    return converted


def ingest(content: bytes, filename: str, max_rows: int = 100_000) -> list[dict[str, Any]]:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        rows = read_csv(content)
    elif suffix == "json":
        rows = read_json(content)
    else:
        raise ValueError("Only CSV and JSON files are supported")
    if len(rows) > max_rows:
        raise ValueError(f"Dataset exceeds the {max_rows}-row limit")
    validate_required_columns(rows)
    return coerce_ecommerce_types(rows)


# Backward-compatible name from the original scaffold.
load_records = ingest

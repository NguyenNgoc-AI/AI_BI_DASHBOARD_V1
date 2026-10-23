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


def prepare_rows(rows: list[dict], max_rows: int = 100_000) -> list[dict]:
    """Validate a flat table without imposing a business schema or deleting rows."""
    if not rows or len(rows) > max_rows:
        raise ValueError(f"Dataset must contain 1 to {max_rows} rows")
    result = []
    columns = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} must be an object")
        item = {}
        for key, value in row.items():
            name = _column_name(str(key))
            if not name or name in item:
                raise ValueError(f"Empty or duplicate normalized column at row {index}")
            if isinstance(value, (dict, list)):
                raise ValueError(f"Nested values are not supported at row {index}")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"Numeric values must be finite at row {index}")
            item[name] = None if value == "" else value
        columns.update(item)
        if len(columns) > MAX_COLUMNS:
            raise ValueError(f"Dataset exceeds the {MAX_COLUMNS}-column limit")
        result.append(item)
    if not columns:
        raise ValueError("Dataset has no columns")
    # Missing keys become explicit nulls so quality checks include them.
    result = [{key: row.get(key) for key in sorted(columns)} for row in result]
    # Infer only unambiguous numeric columns; keep identifiers and leading zeroes.
    for key in columns:
        if any(part in key.split("_") for part in ("id", "code", "zip", "phone")):
            continue
        present = [row[key] for row in result if row[key] is not None]
        if present and all(isinstance(v, str) and re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", v) for v in present):
            converted = [float(v) for v in present]
            if all(math.isfinite(v) for v in converted):
                for row in result:
                    if row[key] is not None:
                        row[key] = float(row[key])
    return result


def _column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def read_csv(content: bytes, max_rows: int = 100_000) -> list[dict[str, Any]]:
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
        rows = []
        for index, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV column count mismatch at line {index}")
            rows.append(row)
            if len(rows) > max_rows:
                raise ValueError(f"Dataset exceeds the {max_rows}-row limit")
        return prepare_rows(rows, max_rows)
    except csv.Error as error:
        raise ValueError(f"Malformed CSV: {error}") from error


def read_json(content: bytes, max_rows: int = 100_000) -> list[dict[str, Any]]:
    try:
        def unique_pairs(pairs):
            item = {}
            for key, cell in pairs:
                if key in item:
                    raise ValueError(f"Duplicate JSON key: {key}")
                item[key] = cell
            return item
        value = json.loads(content.decode("utf-8-sig"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Malformed UTF-8 JSON") from error
    if isinstance(value, dict) and set(value) == {"data"}:
        value = value["data"]
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("JSON must be an array of flat objects")
    if any(any(isinstance(cell, (dict, list)) for cell in row.values()) for row in value):
        raise ValueError("Nested JSON values are not supported")
    return prepare_rows(value, max_rows)


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
        if any(item.get(key) is None for key in REQUIRED_COLUMNS):
            raise ValueError(f"Missing required value at row {index}")
        if any(isinstance(item.get(key), bool) for key in {"revenue", "cost"} | numeric_optional):
            raise ValueError(f"Boolean is not a numeric value at row {index}")
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
        for key in numeric_optional & item.keys():
            value = item[key]
            if value is not None and (value < 0 or (key != "ad_spend" and not value.is_integer())):
                raise ValueError(f"Invalid non-negative amount/count for {key} at row {index}")
        if not str(item["order_id"]).strip() or not str(item["product"]).strip():
            raise ValueError(f"order_id and product are required at row {index}")
        item["order_id"] = str(item["order_id"]).strip()
        item["product"] = str(item["product"]).strip()
        converted.append(item)
    return converted


def ingest(content: bytes, filename: str, max_rows: int = 100_000, *, generic: bool = False) -> list[dict[str, Any]]:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        rows = read_csv(content, max_rows)
    elif suffix == "json":
        rows = read_json(content, max_rows)
    else:
        raise ValueError("Only CSV and JSON files are supported")
    if len(rows) > max_rows:
        raise ValueError(f"Dataset exceeds the {max_rows}-row limit")
    if generic:
        return rows
    validate_required_columns(rows)
    return coerce_ecommerce_types(rows)


# Backward-compatible name from the original scaffold.
load_records = ingest

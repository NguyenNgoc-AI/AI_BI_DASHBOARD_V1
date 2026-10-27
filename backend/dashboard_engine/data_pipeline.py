"""Read, validate, and project e-commerce datasets while preserving original customer headers."""

import csv
import io
import json
import math
import re
from datetime import date, datetime
from typing import Any

from semantic.business_rules import calculate_cogs, calculate_gross_sales, calculate_net_sales
from semantic.schema_definition import inspect_and_map_columns, normalize_alias_token

REQUIRED_COLUMNS = {"date", "order_id", "product", "revenue", "cost"}
MAX_COLUMNS = 100


def _column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _clean_header(value: str) -> str:
    cleaned = str(value).strip()
    if cleaned and cleaned.isascii():
        slug = _column_name(cleaned)
        if slug in REQUIRED_COLUMNS:
            return slug
    return cleaned


def _parse_iso_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Empty date value")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        return datetime.fromisoformat(normalized).date().isoformat()


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    return list(dict.fromkeys(key for row in rows for key in row.keys())) if rows else []


def read_csv(content: bytes) -> list[dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("CSV must use UTF-8 encoding") from error
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if not reader.fieldnames or any(not name or not name.strip() for name in reader.fieldnames):
        raise ValueError("CSV headers must not be empty")
    headers = [_clean_header(name) for name in reader.fieldnames]
    dedup_keys = [normalize_alias_token(h) or h.lower() for h in headers]
    if len(dedup_keys) != len(set(dedup_keys)):
        raise ValueError("CSV contains duplicate headers")
    if len(headers) > MAX_COLUMNS:
        raise ValueError(f"Dataset exceeds the {MAX_COLUMNS}-column limit")
    try:
        return [
            {headers[idx]: value for idx, value in enumerate(row.values())}
            for row in reader
        ]
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
    cleaned_rows: list[dict[str, Any]] = []
    for row in value:
        cleaned_row: dict[str, Any] = {}
        seen_tokens: set[str] = set()
        for key, cell in row.items():
            header = _clean_header(str(key))
            if not header:
                raise ValueError("JSON keys must not be empty")
            token = normalize_alias_token(header) or header.lower()
            if token in seen_tokens:
                raise ValueError("JSON contains duplicate keys")
            seen_tokens.add(token)
            cleaned_row[header] = cell
        if len(cleaned_row) > MAX_COLUMNS:
            raise ValueError(f"Dataset exceeds the {MAX_COLUMNS}-column limit")
        cleaned_rows.append(cleaned_row)
    return cleaned_rows


def validate_required_columns(rows: list[dict[str, Any]], required: set[str] = REQUIRED_COLUMNS) -> dict[str, Any]:
    if not rows:
        raise ValueError("Dataset is empty")
    headers = _ordered_columns(rows)
    mapping = inspect_and_map_columns(headers)
    roles = mapping["roles"]

    missing: list[str] = []
    for req in sorted(required):
        if roles.get(req):
            continue
        if req == "revenue" and roles.get("quantity") and roles.get("unit_price"):
            continue
        if req == "cost" and roles.get("quantity") and roles.get("unit_cost"):
            continue
        missing.append(req)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return mapping


def _coerce_numeric_cell(value: Any, as_int: bool = False) -> float | int:
    num = float(value)
    if not math.isfinite(num):
        raise ValueError("Numeric values must be finite")
    if as_int and num.is_integer():
        return int(num)
    return num


def coerce_ecommerce_types(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping = validate_required_columns(rows)
    roles = mapping["roles"]
    col_meta = mapping["columns"]
    headers = _ordered_columns(rows)

    date_col = roles["date"]
    order_col = roles["order_id"]
    product_col = roles["product"]
    rev_col = roles.get("revenue")
    cost_col = roles.get("cost")
    qty_col = roles.get("quantity")
    price_col = roles.get("unit_price")
    ucost_col = roles.get("unit_cost")
    disc_col = roles.get("discount_amount")

    numeric_role_cols = {
        col
        for role_name, col in roles.items()
        if col and role_name in {
            "revenue",
            "cost",
            "quantity",
            "unit_price",
            "unit_cost",
            "discount_amount",
            "ad_spend",
            "new_customers",
            "net_profit",
            "platform_fee",
            "freight_value",
            "tax_amount",
            "operating_expenses",
        }
    }

    converted: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        item: dict[str, Any] = {
            key: (None if row.get(key) == "" else row.get(key))
            for key in headers
            if key in row
        }
        try:
            parsed_date = _parse_iso_date(item.get(date_col))
            if date_col == "date":
                item[date_col] = parsed_date
            else:
                item[date_col] = str(item[date_col]).strip()

            for col in headers:
                if col not in item or item[col] is None:
                    continue
                meta = col_meta.get(col, {})
                declared_type = meta.get("declared_type")
                sem_type = meta.get("semantic_type")
                if col in numeric_role_cols or declared_type in {"float", "integer"} or sem_type in {
                    "numerical_currency",
                    "numerical_quantity",
                    "numerical_ratio",
                    "percentage",
                }:
                    is_int = declared_type == "integer" and col not in {rev_col, cost_col}
                    item[col] = _coerce_numeric_cell(item[col], as_int=is_int)
                elif declared_type == "boolean" and isinstance(item[col], str):
                    lowered = item[col].strip().lower()
                    if lowered in {"true", "1", "yes"}:
                        item[col] = True
                    elif lowered in {"false", "0", "no"}:
                        item[col] = False

            if rev_col and item.get(rev_col) is not None:
                rev_val = float(item[rev_col])
                item[rev_col] = rev_val
            elif qty_col and price_col:
                gross = calculate_gross_sales(float(item[qty_col]), float(item[price_col]))
                disc = float(item.get(disc_col, 0.0) or 0.0) if disc_col else 0.0
                rev_val = calculate_net_sales(gross, disc)
            else:
                raise ValueError("Missing revenue value")

            if cost_col and item.get(cost_col) is not None:
                cost_val = float(item[cost_col])
                item[cost_col] = cost_val
            elif qty_col and ucost_col:
                cost_val = calculate_cogs(float(item[qty_col]), float(item[ucost_col]))
            else:
                raise ValueError("Missing cost value")
        except (TypeError, ValueError) as error:
            msg = str(error)
            if "must be finite" in msg:
                raise ValueError(f"Numeric values must be finite at row {index}") from error
            raise ValueError(f"Invalid value at row {index}: {error}") from error

        if not math.isfinite(rev_val) or not math.isfinite(cost_val):
            raise ValueError(f"Numeric values must be finite at row {index}")
        if rev_val < 0 or cost_val < 0:
            raise ValueError(f"Revenue and cost must be non-negative at row {index}")

        raw_order = item.get(order_col)
        raw_product = item.get(product_col)
        if raw_order is None or raw_product is None or not str(raw_order).strip() or not str(raw_product).strip():
            raise ValueError(f"order_id and product are required at row {index}")
        item[order_col] = str(raw_order).strip()
        item[product_col] = str(raw_product).strip()
        converted.append(item)
    return converted


def build_canonical_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Projects validated rows (with original customer headers) onto the canonical
    5-column View Contract + optional financial attributes for KPI and Chart engines.
    """
    coerced = coerce_ecommerce_types(rows)
    mapping = inspect_and_map_columns(_ordered_columns(coerced))
    roles = mapping["roles"]

    date_col = roles["date"]
    order_col = roles["order_id"]
    product_col = roles["product"]
    rev_col = roles.get("revenue")
    cost_col = roles.get("cost")
    qty_col = roles.get("quantity")
    price_col = roles.get("unit_price")
    ucost_col = roles.get("unit_cost")
    disc_col = roles.get("discount_amount")

    optional_roles = (
        "quantity",
        "ad_spend",
        "new_customers",
        "customer_id",
        "net_profit",
        "platform_fee",
        "freight_value",
        "tax_amount",
        "operating_expenses",
        "sales_id",
    )

    projected: list[dict[str, Any]] = []
    for row in coerced:
        if rev_col and row.get(rev_col) is not None:
            revenue = float(row[rev_col])
        else:
            gross = calculate_gross_sales(float(row[qty_col]), float(row[price_col]))
            discount = float(row.get(disc_col, 0.0) or 0.0) if disc_col else 0.0
            revenue = calculate_net_sales(gross, discount)

        if cost_col and row.get(cost_col) is not None:
            cost = float(row[cost_col])
        else:
            cost = calculate_cogs(float(row[qty_col]), float(row[ucost_col]))

        view_row: dict[str, Any] = {
            "date": _parse_iso_date(row[date_col]),
            "order_id": str(row[order_col]).strip(),
            "product": str(row[product_col]).strip(),
            "revenue": revenue,
            "cost": cost,
        }
        for opt in optional_roles:
            src_col = roles.get(opt)
            if src_col and src_col in row:
                view_row[opt] = row[src_col]
        projected.append(view_row)
    return projected


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
    return coerce_ecommerce_types(rows)


# Backward-compatible name from the original scaffold.
load_records = ingest

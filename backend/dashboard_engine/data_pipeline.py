"""Read, validate, and project e-commerce datasets while preserving original customer headers."""

import io
import json
import math
import re
from datetime import date, datetime
from typing import Any

from semantic.business_rules import calculate_cogs, calculate_gross_sales, calculate_net_sales
from semantic.schema_definition import (
    estimate_learned_cost,
    inspect_and_map_columns,
    normalize_alias_token,
)

REQUIRED_COLUMNS = {"date", "order_id", "product", "revenue", "cost"}
MAX_COLUMNS = 100


class _CoercedRows(list):
    """List subclass tagging rows that have already been validated & coerced."""
    is_coerced: bool = True
    mapping: dict[str, Any] | None = None
    headers: list[str] | None = None


def _column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _clean_header(value: str) -> str:
    cleaned = str(value).strip()
    if cleaned and cleaned.isascii():
        slug = _column_name(cleaned)
        if slug in REQUIRED_COLUMNS:
            return slug
    return cleaned


def _parse_slash_date(text: str) -> str:
    parts = text.split()
    if not parts or len(parts) > 2:
        raise ValueError(f"Invalid date format: {text}")
    date_tokens = parts[0].split("/")
    if len(date_tokens) != 3:
        raise ValueError(f"Invalid slash date: {text}")
    p1, p2, p3 = int(date_tokens[0]), int(date_tokens[1]), int(date_tokens[2])
    if len(parts) == 2:
        time_tokens = parts[1].split(":")
        if len(time_tokens) not in (2, 3):
            raise ValueError(f"Invalid time format: {text}")
        hh, mm = int(time_tokens[0]), int(time_tokens[1])
        ss = int(float(time_tokens[2])) if len(time_tokens) == 3 else 0
        if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
            raise ValueError(f"Time out of range: {text}")
    if p1 >= 1000:
        return date(p1, p2, p3).isoformat()
    if p3 < 100:
        p3 += 2000 if p3 < 70 else 1900
    if p1 > 12:
        return date(p3, p2, p1).isoformat()
    if p2 > 12:
        return date(p3, p1, p2).isoformat()
    return date(p3, p2, p1).isoformat()


def _parse_iso_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Empty date value")
    n = len(text)
    if n == 10 and text[4] == "-" and text[7] == "-":
        return date.fromisoformat(text).isoformat()
    if n == 19 and text[4] == "-" and text[7] == "-" and text[10] in (" ", "T") and text[13] == ":" and text[16] == ":":
        date_part = text[:10]
        date.fromisoformat(date_part)
        int(text[11:13])
        int(text[14:16])
        int(text[17:19])
        return date_part
    if "/" in text:
        return _parse_slash_date(text)
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        return datetime.fromisoformat(normalized).date().isoformat()


class RowList(list):
    """Subclass of list that allows attaching metadata (headers, structural_errors)."""
    headers: list[str] = []
    structural_errors: list[dict[str, Any]] = []


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    if getattr(rows, "headers", None):
        return rows.headers
    first_keys = list(rows[0].keys())
    if all(len(row) == len(first_keys) for row in rows[:20]):
        return first_keys
    return list(dict.fromkeys(key for row in rows for key in row.keys()))


def _parse_resilient_csv_records(text: str) -> list[list[str]]:
    records: list[list[str]] = []
    row: list[str] = []
    cell_chars: list[str] = []
    quoted = False
    n = len(text)
    i = 0

    while i < n:
        c = text[i]
        if c == '"':
            if quoted:
                nxt = text[i + 1] if i + 1 < n else ""
                if nxt == '"':
                    cell_chars.append('"')
                    i += 2
                    continue
                if nxt in (",", "\r", "\n", ""):
                    quoted = False
                    i += 1
                    continue
                # Unescaped quote (e.g. inch mark 12") inside a quoted field
                cell_chars.append('"')
                i += 1
                continue
            elif not cell_chars:
                quoted = True
                i += 1
                continue
            else:
                # Quote inside an unquoted cell (e.g. 12" METAL SIGN)
                cell_chars.append('"')
                i += 1
                continue
        elif c == "," and not quoted:
            row.append("".join(cell_chars))
            cell_chars = []
        elif (c == "\n" or c == "\r") and not quoted:
            if c == "\r" and i + 1 < n and text[i + 1] == "\n":
                i += 1
            row.append("".join(cell_chars))
            cell_chars = []
            if any(v != "" for v in row):
                records.append(row)
            row = []
        else:
            cell_chars.append(c)
        i += 1

    if quoted:
        raise ValueError("Malformed CSV: unclosed quote")
    row.append("".join(cell_chars))
    if any(v != "" for v in row):
        records.append(row)
    return records


def _find_text_merge_index(headers: list[str]) -> int:
    mapping = inspect_and_map_columns(headers)
    prod_col = mapping["roles"].get("product")
    if prod_col and prod_col in headers:
        return headers.index(prod_col)
    for idx, h in enumerate(headers):
        tok = normalize_alias_token(h)
        if any(w in tok for w in ("description", "desc", "product", "name", "title")):
            return idx
    return min(2, len(headers) - 1)


def read_csv(content: bytes) -> list[dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("CSV must use UTF-8 encoding") from error

    records = _parse_resilient_csv_records(text)
    if not records:
        raise ValueError("CSV headers must not be empty")

    raw_headers = records[0]
    if len(raw_headers) > 1 and not str(raw_headers[0]).strip():
        raw_headers[0] = "row_index"
    if not raw_headers or any(not str(name).strip() for name in raw_headers):
        raise ValueError("CSV headers must not be empty")

    headers = [_clean_header(name) for name in raw_headers]
    dedup_keys = [normalize_alias_token(h) or h.lower() for h in headers]
    if len(dedup_keys) != len(set(dedup_keys)):
        raise ValueError("CSV contains duplicate headers")
    if len(headers) > MAX_COLUMNS:
        raise ValueError(f"Dataset exceeds the {MAX_COLUMNS}-column limit")

    num_cols = len(headers)
    merge_idx = _find_text_merge_index(headers)
    rows = RowList()
    structural_errors: list[dict[str, Any]] = []

    for row_idx, r in enumerate(records[1:], start=2):
        if len(r) > num_cols:
            extra = len(r) - num_cols
            merged_val = ", ".join(r[merge_idx : merge_idx + 1 + extra])
            r = r[:merge_idx] + [merged_val] + r[merge_idx + 1 + extra :]
            if len(r) > num_cols:
                actual_len = len(r)
                r = r[:num_cols]
                structural_errors.append({
                    "row_index": row_idx,
                    "actual_columns": actual_len,
                    "expected_columns": num_cols,
                    "issue": "EXTRA_COLUMNS",
                })
        elif len(r) < num_cols:
            actual_len = len(r)
            r = r + [None] * (num_cols - actual_len)
            structural_errors.append({
                "row_index": row_idx,
                "actual_columns": actual_len,
                "expected_columns": num_cols,
                "issue": "MISSING_COLUMNS",
            })
        rows.append({headers[j]: r[j] for j in range(num_cols)})

    # Attach structural errors and headers to rows list as metadata
    rows.headers = headers
    rows.structural_errors = structural_errors
    return rows


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
    res = RowList(cleaned_rows)
    res.headers = list(dict.fromkeys(k for r in res for k in r.keys()))
    res.structural_errors = []
    return res


def validate_required_columns(rows: list[dict[str, Any]], required: set[str] = REQUIRED_COLUMNS) -> dict[str, Any]:
    if not rows:
        raise ValueError("Dataset is empty")
    if getattr(rows, "is_coerced", False) and getattr(rows, "mapping", None) and required == REQUIRED_COLUMNS:
        return rows.mapping
    headers = _ordered_columns(rows)
    mapping = inspect_and_map_columns(headers)
    roles = mapping["roles"]

    has_core_4 = bool(
        roles.get("date")
        and roles.get("order_id")
        and roles.get("product")
        and (roles.get("revenue") or (roles.get("quantity") and roles.get("unit_price")))
    )

    missing: list[str] = []
    for req in sorted(required):
        if roles.get(req):
            continue
        if req == "revenue" and roles.get("quantity") and roles.get("unit_price"):
            continue
        if req == "cost" and ((roles.get("quantity") and roles.get("unit_cost")) or has_core_4):
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
    if getattr(rows, "is_coerced", False):
        return rows
    mapping = validate_required_columns(rows)
    roles = mapping["roles"]
    col_meta = mapping["columns"]
    headers = _ordered_columns(rows)

    date_col = roles["date"]
    order_col = roles["order_id"]
    product_col = roles["product"]
    product_id_col = roles.get("product_id")
    rev_col = roles.get("revenue")
    cost_col = roles.get("cost")
    cat_col = roles.get("category")
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

    numeric_cols_plan: list[tuple[str, bool]] = []
    bool_cols_plan: list[str] = []
    for col in headers:
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
            numeric_cols_plan.append((col, is_int))
        elif declared_type == "boolean":
            bool_cols_plan.append(col)

    converted = _CoercedRows()
    converted.mapping = mapping
    converted.headers = headers

    for index, row in enumerate(rows, start=1):
        item: dict[str, Any] = {
            key: (None if val == "" else val)
            for key, val in row.items()
        }
        try:
            parsed_date = _parse_iso_date(item.get(date_col))
            if date_col == "date":
                item[date_col] = parsed_date
            else:
                item[date_col] = str(item[date_col]).strip()

            for col, is_int in numeric_cols_plan:
                val = item.get(col)
                if val is not None:
                    item[col] = _coerce_numeric_cell(val, as_int=is_int)

            for col in bool_cols_plan:
                val = item.get(col)
                if isinstance(val, str):
                    lowered = val.strip().lower()
                    if lowered in {"true", "1", "yes"}:
                        item[col] = True
                    elif lowered in {"false", "0", "no"}:
                        item[col] = False

            if rev_col and item.get(rev_col) is not None:
                rev_val = float(item[rev_col])
                item[rev_col] = rev_val
            elif qty_col and price_col and item.get(qty_col) is not None and item.get(price_col) is not None:
                q_val = abs(float(item[qty_col]))
                p_val = max(0.0, float(item[price_col]))
                gross = calculate_gross_sales(q_val, p_val)
                disc = max(0.0, float(item.get(disc_col, 0.0) or 0.0)) if disc_col else 0.0
                rev_val = calculate_net_sales(gross, min(gross, disc))
            else:
                raise ValueError("Missing revenue value")

            if cost_col and item.get(cost_col) is not None:
                cost_val = float(item[cost_col])
                item[cost_col] = cost_val
            elif qty_col and ucost_col and item.get(qty_col) is not None and item.get(ucost_col) is not None:
                cost_val = calculate_cogs(abs(float(item[qty_col])), max(0.0, float(item[ucost_col])))
            else:
                cat_val = str(item[cat_col]) if cat_col and item.get(cat_col) is not None else None
                cost_val = estimate_learned_cost(rev_val, category=cat_val)
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
        if (raw_product is None or not str(raw_product).strip()) and product_id_col and item.get(product_id_col):
            raw_product = item.get(product_id_col)
        if raw_order is None or raw_product is None or not str(raw_order).strip() or not str(raw_product).strip():
            raise ValueError(f"order_id and product are required at row {index}")
        item[order_col] = str(raw_order).strip()
        if item.get(product_col) is not None:
            item[product_col] = str(raw_product).strip()
        converted.append(item)
    return converted


def build_canonical_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Projects validated rows (with original customer headers) onto the canonical
    5-column View Contract + optional financial attributes for KPI and Chart engines.
    """
    coerced = coerce_ecommerce_types(rows)
    mapping = getattr(coerced, "mapping", None) or inspect_and_map_columns(_ordered_columns(coerced))
    roles = mapping["roles"]

    date_col = roles["date"]
    order_col = roles["order_id"]
    product_col = roles["product"]
    product_id_col = roles.get("product_id")
    rev_col = roles.get("revenue")
    cost_col = roles.get("cost")
    cat_col = roles.get("category")
    qty_col = roles.get("quantity")
    price_col = roles.get("unit_price")
    ucost_col = roles.get("unit_cost")
    disc_col = roles.get("discount_amount")

    optional_roles = [
        (opt, roles.get(opt))
        for opt in (
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
        if roles.get(opt)
    ]

    projected: list[dict[str, Any]] = []
    for row in coerced:
        if rev_col and row.get(rev_col) is not None:
            revenue = float(row[rev_col])
        else:
            q_val = abs(float(row[qty_col]))
            p_val = max(0.0, float(row[price_col]))
            gross = calculate_gross_sales(q_val, p_val)
            discount = max(0.0, float(row.get(disc_col, 0.0) or 0.0)) if disc_col else 0.0
            revenue = calculate_net_sales(gross, min(gross, discount))

        if cost_col and row.get(cost_col) is not None:
            cost = float(row[cost_col])
        elif qty_col and ucost_col and row.get(qty_col) is not None and row.get(ucost_col) is not None:
            cost = calculate_cogs(abs(float(row[qty_col])), max(0.0, float(row[ucost_col])))
        else:
            cat_val = str(row[cat_col]) if cat_col and row.get(cat_col) is not None else None
            cost = estimate_learned_cost(revenue, category=cat_val)

        raw_d = row[date_col]
        date_iso = (
            raw_d[:10]
            if isinstance(raw_d, str) and len(raw_d) >= 10 and raw_d[4] == "-" and raw_d[7] == "-"
            else _parse_iso_date(raw_d)
        )
        prod_val = row.get(product_col)
        if (prod_val is None or not str(prod_val).strip()) and product_id_col:
            prod_val = row.get(product_id_col)

        view_row: dict[str, Any] = {
            "date": date_iso,
            "order_id": str(row[order_col]),
            "product": str(prod_val),
            "revenue": revenue,
            "cost": cost,
        }
        for opt, src_col in optional_roles:
            if src_col in row:
                view_row[opt] = row[src_col]
        projected.append(view_row)
    result = RowList(projected)
    result.headers = getattr(rows, "headers", [])
    result.structural_errors = getattr(rows, "structural_errors", [])
    return result


def ingest(content: bytes, filename: str, max_rows: int = 500_000) -> list[dict[str, Any]]:
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

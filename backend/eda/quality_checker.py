"""Quality checks report issues; they never silently delete rows."""

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

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
    total_rows = len(rows)
    if not total_rows:
        return {"valid_rows": 0, "invalid_rows": 0, "rate": 1.0}
    headers = list(dict.fromkeys(key for row in rows for key in row.keys()))
    mapping = inspect_and_map_columns(headers)["columns"]
    canonical_to_raw = {
        meta["matched_column"]: raw_col
        for raw_col, meta in mapping.items()
        if meta.get("matched_column")
    }

    safe_globals = {"__builtins__": None, "abs": abs, "min": min, "max": max}
    valid_count = 0

    for r in rows:
        row_dict = dict(r)
        for canon, raw in canonical_to_raw.items():
            if raw in r and canon not in row_dict:
                row_dict[canon] = r[raw]
        
        row_is_valid = True
        for rule in DEFAULT_RULE_ENGINE.spec.hard_constraints:
            try:
                res = eval(rule.expression, safe_globals, row_dict)
                if res is False:
                    row_is_valid = False
                    break
            except Exception:
                continue
        if row_is_valid:
            valid_count += 1

    return {
        "valid_rows": valid_count,
        "invalid_rows": total_rows - valid_count,
        "rate": valid_count / total_rows if total_rows else 1.0,
    }


def _collect_violations(rows: list[dict], resolved_key: str, outliers_by_col: dict) -> list[dict]:
    violations: list[dict] = []
    if not rows:
        return violations

    # 0. Structural CSV parsing errors (column count mismatches)
    structural_errors = getattr(rows, "structural_errors", []) or []
    for err in structural_errors:
        row_i = err.get("row_index", 0)
        act = err.get("actual_columns", 0)
        exp = err.get("expected_columns", 0)
        issue = err.get("issue", "")
        if issue == "MISSING_COLUMNS":
            msg = f"Dòng {row_i} bị thiếu cột ({act}/{exp} cột). Hệ thống đã tự động đệm ô trống để tiếp tục kiểm nghiệm."
        else:
            msg = f"Dòng {row_i} bị thừa cột ({act}/{exp} cột). Hệ thống đã tự động cắt/gộp để tiếp tục kiểm nghiệm."
        violations.append({
            "row_index": row_i,
            "identifier": f"Dòng #{row_i}",
            "category": "Cấu trúc tệp (CSV Malformed)",
            "severity": "CRITICAL",
            "rule": "CSV Column Count Matching",
            "message": msg,
        })
        if len(violations) >= 50:
            break

    headers = list(dict.fromkeys(key for row in rows for key in row.keys()))
    mapping = inspect_and_map_columns(headers)["columns"]
    canonical_to_raw = {
        meta["matched_column"]: raw_col
        for raw_col, meta in mapping.items()
        if meta.get("matched_column")
    }

    # 1. Uniqueness violations (duplicate keys)
    counts = Counter(r.get(resolved_key) for r in rows if r.get(resolved_key) not in (None, ""))
    dup_values = {val for val, cnt in counts.items() if cnt > 1}
    seen_dups: set = set()
    for i, r in enumerate(rows):
        val = r.get(resolved_key)
        if val in dup_values and val not in seen_dups:
            seen_dups.add(val)
            violations.append({
                "row_index": i + 1,
                "identifier": str(val),
                "category": "Tính duy nhất",
                "severity": "WARNING",
                "rule": f"Duplicate {resolved_key}",
                "message": f"Khóa chính '{resolved_key}' bị trùng lặp: giá trị '{val}' xuất hiện {counts[val]} lần.",
            })
            if len(violations) >= 50:
                break

    # 2. Mathematical & Semantic Rule violations
    safe_globals = {"__builtins__": None, "abs": abs, "min": min, "max": max}
    for i, r in enumerate(rows):
        row_dict = dict(r)
        for canon, raw in canonical_to_raw.items():
            if raw in r and canon not in row_dict:
                row_dict[canon] = r[raw]

        for rule in DEFAULT_RULE_ENGINE.spec.hard_constraints:
            try:
                res = eval(rule.expression, safe_globals, row_dict)
                if res is False:
                    violations.append({
                        "row_index": i + 1,
                        "identifier": str(r.get(resolved_key) or f"Dòng {i + 1}"),
                        "category": "Luật kinh doanh",
                        "severity": "CRITICAL",
                        "rule": rule.name,
                        "message": rule.description or f"Vi phạm quy tắc: {rule.expression}",
                    })
                    if len(violations) >= 150:
                        break
            except Exception:
                continue
        if len(violations) >= 150:
            break

    # 3. Missing Value violations
    for i, r in enumerate(rows):
        empty_cols = [k for k, v in r.items() if v in (None, "")]
        if empty_cols:
            violations.append({
                "row_index": i + 1,
                "identifier": str(r.get(resolved_key) or f"Dòng {i + 1}"),
                "category": "Tính đầy đủ",
                "severity": "WARNING",
                "rule": "Missing Values",
                "message": f"Ô trống hoặc thiếu dữ liệu ở các cột: {', '.join(empty_cols[:4])}",
            })
            if len(violations) >= 180:
                break

    # 4. Outlier violations
    for col, out_info in outliers_by_col.items():
        low = out_info.get("lower_bound")
        high = out_info.get("upper_bound")
        if low is None or high is None or not out_info.get("count"):
            continue
        for i, r in enumerate(rows):
            v = r.get(col)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if v < low or v > high:
                    violations.append({
                        "row_index": i + 1,
                        "identifier": str(r.get(resolved_key) or f"Dòng {i + 1}"),
                        "category": "Bất thường (Outlier)",
                        "severity": "INFO",
                        "rule": f"Outlier ({col})",
                        "message": f"Giá trị {v} ở cột '{col}' nằm ngoài dải phân vị chuẩn ({low:.1f} đến {high:.1f}).",
                    })
                    if len(violations) >= 200:
                        break
        if len(violations) >= 200:
            break

    # Sort: CRITICAL first, then WARNING, then INFO
    order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    violations.sort(key=lambda x: order.get(x["severity"], 3))
    return violations[:200]


def _generate_recommendations(score_pct: float, dimensions: dict, violations: list[dict]) -> list[str]:
    recs: list[str] = []
    if score_pct >= 90.0 and not violations:
        recs.append("Dữ liệu đạt chuẩn chất lượng xuất sắc (Tier A), không phát hiện vi phạm luật kinh doanh nào.")
        recs.append("Dữ liệu sẵn sàng cho mọi tác vụ báo cáo, phân tích chuyên sâu và ra quyết định.")
        return recs

    structural_count = sum(1 for v in violations if v.get("category") == "Cấu trúc tệp (CSV Malformed)")
    if structural_count > 0:
        recs.insert(0, f"Phát hiện {structural_count} dòng bị vỡ cấu trúc CSV (lệch số cột do thiếu/thừa dấu phẩy hoặc dấu ngoặc kép). Cần kiểm tra lại các dòng này trên tệp nguồn.")

    critical_count = sum(1 for v in violations if v["severity"] == "CRITICAL" and v.get("category") != "Cấu trúc tệp (CSV Malformed)")
    if critical_count > 0:
        recs.append(f"Phát hiện {critical_count} lỗi sai lệch nghiêm trọng về toán học/luật kinh doanh. Cần kiểm tra lại công thức doanh thu, đơn giá và chiết khấu.")

    if dimensions["uniqueness"]["duplicate_rows"] > 0:
        recs.append(f"Có {dimensions['uniqueness']['duplicate_rows']} dòng bị trùng lặp khóa chính '{dimensions['uniqueness']['primary_key']}'. Nên khử trùng lặp để tránh tính thừa doanh số.")

    if dimensions["completeness"]["missing_rows"] > 0:
        recs.append(f"Có {dimensions['completeness']['missing_rows']} dòng bị khuyết thiếu dữ liệu. Khuyến nghị điền giá trị mặc định hoặc lọc bỏ các dòng rỗng trước khi tổng hợp.")

    if dimensions["outliers"]["outlier_count"] > 0:
        recs.append(f"Phát hiện {dimensions['outliers']['outlier_count']} điểm dữ liệu bất thường (Outlier). Cần rà soát các giao dịch có giá trị đột biến để xác minh tính chính xác.")

    if not recs:
        recs.append("Dữ liệu ở mức độ tin cậy tốt, có thể sử dụng cho phân tích thông thường.")
    return recs


def check_quality(rows: list[dict], rules: list[dict] | None = None) -> dict:
    missing = find_missing(rows)
    duplicates = find_duplicates(rows)
    validity = evaluate_rules(rows, rules) if rules is not None else _evaluate_semantic_rules(rows)
    invalid_rate = 1.0 - validity["rate"]
    structural_count = len(getattr(rows, "structural_errors", []) or [])
    structural_rate = (structural_count / len(rows)) if rows else 0.0
    score = max(0.0, 1.0 - missing["rate"] * 0.4 - duplicates["rate"] * 0.3 - invalid_rate * 0.3 - structural_rate * 0.5)

    ordered_keys = list(dict.fromkeys(key for row in rows for key in row.keys())) if rows else []
    numeric_columns: list[str] = []
    for key in ordered_keys:
        for row in rows:
            val = row.get(key)
            if val is not None and val != "":
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    numeric_columns.append(key)
                break

    outliers_by_col = {column: find_outliers([row.get(column) for row in rows]) for column in numeric_columns}
    total_outliers = sum(o.get("count", 0) for o in outliers_by_col.values())
    resolved_key = _resolve_duplicate_key(rows)

    score_pct = round(score * 100.0, 1)
    dimensions = {
        "completeness": {
            "score": round(max(0.0, 100.0 - missing["rate"] * 100.0), 1),
            "missing_rows": missing["rows"],
            "total_rows": len(rows),
            "rate": round(missing["rate"], 4),
            "status": "PASSED" if missing["rate"] < 0.05 else ("WARNING" if missing["rate"] < 0.2 else "FAILED"),
        },
        "uniqueness": {
            "score": round(max(0.0, 100.0 - duplicates["rate"] * 100.0), 1),
            "duplicate_rows": duplicates["rows"],
            "total_rows": len(rows),
            "primary_key": resolved_key,
            "rate": round(duplicates["rate"], 4),
            "status": "PASSED" if duplicates["rows"] == 0 else "WARNING",
        },
        "validity": {
            "score": round(validity["rate"] * 100.0, 1),
            "valid_rows": validity["valid_rows"],
            "invalid_rows": validity["invalid_rows"],
            "total_rows": len(rows),
            "rate": round(validity["rate"], 4),
            "status": "PASSED" if validity["rate"] >= 0.95 else ("WARNING" if validity["rate"] >= 0.8 else "FAILED"),
        },
        "outliers": {
            "score": round(max(0.0, 100.0 - min(100.0, (total_outliers / max(len(rows), 1)) * 50.0)), 1),
            "outlier_count": total_outliers,
            "columns_with_outliers": sum(1 for o in outliers_by_col.values() if o.get("count", 0) > 0),
            "status": "PASSED" if total_outliers == 0 else "INFO",
        },
    }

    if score_pct >= 90.0:
        status = "PASSED"
        tier = "Tier A (Xuất sắc)"
    elif score_pct >= 80.0:
        status = "PASSED"
        tier = "Tier B (Tốt)"
    elif score_pct >= 70.0:
        status = "WARNING"
        tier = "Tier C (Cảnh báo)"
    else:
        status = "FAILED"
        tier = "Tier D (Kém)"

    violations = _collect_violations(rows, resolved_key, outliers_by_col)
    recommendations = _generate_recommendations(score_pct, dimensions, violations)

    return {
        "score": score,
        "valid": validity,
        "missing": missing,
        "duplicates": duplicates,
        "outliers": outliers_by_col,
        "status": status,
        "tier": tier,
        "dimensions": dimensions,
        "violations": violations,
        "recommendations": recommendations,
    }

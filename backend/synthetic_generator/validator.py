"""Validation metrics for synthetic tabular data.

These scores are diagnostics, not a differential-privacy guarantee.
"""

from collections import Counter
import math
from statistics import mean

import numpy as np

from backend.dashboard_engine.kpi_calculator import calculate_kpis


def _bounded_similarity(left: float, right: float) -> float:
    scale = max(abs(left), abs(right), 1.0)
    return max(0.0, 1.0 - abs(left - right) / scale)


def _matches_type(value: object, expected: str) -> bool:
    if value is None or value == "":
        return False
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    return True


def _ks_similarity(real: list[float], fake: list[float]) -> float:
    values = sorted(set(real + fake))
    if not values:
        return 1.0
    maximum = 0.0
    for threshold in values:
        real_cdf = sum(value <= threshold for value in real) / len(real)
        fake_cdf = sum(value <= threshold for value in fake) / len(fake)
        maximum = max(maximum, abs(real_cdf - fake_cdf))
    return 1.0 - maximum


def _categorical_similarity(real: list[object], fake: list[object]) -> float:
    real_counts, fake_counts = Counter(map(str, real)), Counter(map(str, fake))
    categories = set(real_counts) | set(fake_counts)
    distance = sum(abs(real_counts[key] / len(real) - fake_counts[key] / len(fake)) for key in categories) / 2
    return 1.0 - distance


def _privacy_score(original: list[dict], synthetic: list[dict], numeric: list[str]) -> float:
    if not original or not synthetic:
        return 0.0
    if not numeric:
        original_rows = {tuple(sorted(map(lambda item: (item[0], str(item[1])), row.items()))) for row in original}
        matches = sum(tuple(sorted(map(lambda item: (item[0], str(item[1])), row.items()))) in original_rows for row in synthetic)
        return 1.0 - matches / len(synthetic)
    ranges = {
        column: max(float(row[column]) for row in original) - min(float(row[column]) for row in original)
        for column in numeric
    }
    distances = []
    for fake in synthetic:
        nearest = min(
            math.sqrt(mean(((float(fake[column]) - float(real[column])) / max(ranges[column], 1.0)) ** 2 for column in numeric))
            for real in original
        )
        distances.append(min(1.0, nearest))
    return mean(distances)


def _tstr_regression(original: list[dict], synthetic: list[dict], target: str, numeric: list[str]) -> float | None:
    features = [column for column in numeric if column != target]
    if target not in numeric or not features or len(synthetic) < len(features) + 1 or len(original) < 2:
        return None
    try:
        train_x = np.array([[1.0, *(float(row[column]) for column in features)] for row in synthetic])
        train_y = np.array([float(row[target]) for row in synthetic])
        test_x = np.array([[1.0, *(float(row[column]) for column in features)] for row in original])
        test_y = np.array([float(row[target]) for row in original])
    except (KeyError, TypeError, ValueError):
        return None
    coefficients = np.linalg.lstsq(train_x, train_y, rcond=None)[0]
    predictions = test_x @ coefficients
    denominator = float(np.sum((test_y - np.mean(test_y)) ** 2))
    if denominator == 0:
        return None
    r_squared = 1.0 - float(np.sum((test_y - predictions) ** 2)) / denominator
    return max(0.0, min(1.0, r_squared))


def validate_synthetic(original: list[dict], synthetic: list[dict], schema: dict, target_column: str | None = None) -> dict:
    expected = schema.get("columns", {})
    valid_cells = total_cells = 0
    for row in synthetic:
        for column, definition in expected.items():
            total_cells += 1
            value = row.get(column)
            valid_cells += bool(
                (value in (None, "") and definition.get("nullable", False))
                or _matches_type(value, definition.get("type", "string"))
            )
    validity = valid_cells / total_cells if total_cells else 0.0

    numeric = [key for key, definition in expected.items() if definition.get("type") in {"integer", "float"}]
    similarities = []
    for key, definition in expected.items():
        real_values = [row[key] for row in original if row.get(key) not in (None, "")]
        fake_values = [row[key] for row in synthetic if row.get(key) not in (None, "")]
        if not real_values or not fake_values:
            continue
        if key in numeric:
            similarities.append(_ks_similarity(list(map(float, real_values)), list(map(float, fake_values))))
        elif definition.get("type") != "date" and not key.endswith("_id"):
            similarities.append(_categorical_similarity(real_values, fake_values))
    fidelity = mean(similarities) if similarities else 1.0

    privacy = _privacy_score(original, synthetic, numeric)
    tstr = _tstr_regression(original, synthetic, target_column, numeric) if target_column else None
    if tstr is None:
        original_kpis, synthetic_kpis = calculate_kpis(original), calculate_kpis(synthetic)
        utility = mean(
            _bounded_similarity(float(original_kpis[key]), float(synthetic_kpis[key]))
            for key in ("total_revenue", "total_cost", "net_profit")
        )
        utility_method = "kpi_similarity"
    else:
        utility, utility_method = tstr, "tstr_regression"
    return {
        "validity": validity,
        "fidelity": fidelity,
        "privacy": privacy,
        "utility": utility,
        "details": {
            "fidelity_method": "ks_and_total_variation",
            "privacy_method": "normalized_nearest_record_distance",
            "utility_method": utility_method,
            "target_column": target_column,
            "differential_privacy_guarantee": False,
        },
    }

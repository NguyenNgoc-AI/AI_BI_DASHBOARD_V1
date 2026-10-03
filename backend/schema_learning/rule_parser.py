"""Evaluate declarative rules without eval/exec."""

import operator
from typing import Any

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda left, right: left in right,
    "not_null": lambda left, _right: left is not None and left != "",
}


def validate_rule(rule: dict[str, Any]) -> None:
    if not isinstance(rule.get("field"), str) or rule.get("operator") not in OPERATORS:
        raise ValueError("Rule requires a field and a supported operator")
    if rule["operator"] not in {"not_null"} and "value" not in rule:
        raise ValueError("Rule requires a value")


def parse_rule(rule: dict[str, Any]) -> dict[str, Any]:
    validate_rule(rule)
    return dict(rule)


def evaluate_rule(row: dict[str, Any], rule: dict[str, Any]) -> bool:
    validate_rule(rule)
    try:
        return bool(OPERATORS[rule["operator"]](row.get(rule["field"]), rule.get("value")))
    except (TypeError, ValueError):
        return False


def evaluate_rules(rows: list[dict], rules: list[dict]) -> dict[str, float | int]:
    valid = sum(all(evaluate_rule(row, rule) for rule in rules) for row in rows)
    return {"rows": valid, "rate": valid / len(rows) if rows else 0.0}

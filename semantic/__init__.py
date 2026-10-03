"""
Semantic Module for E-Commerce AI BI Dashboard.
Provides schema definitions, business rules, and financial formulas.
"""

from pathlib import Path
import json
from .business_rules import (
    RuleSeverity,
    ValidationResult,
    BUSINESS_RULES_REGISTRY,
    calculate_gross_sales,
    calculate_net_sales,
    calculate_cogs,
    calculate_gross_profit,
    calculate_gross_margin,
    calculate_net_profit,
    calculate_net_margin,
    calculate_aov,
    calculate_cac,
    calculate_roas,
    calculate_ltv,
    calculate_fulfillment_rate,
    calculate_cancellation_rate,
    calculate_repurchase_rate,
    validate_sales_record,
    validate_product_record,
    validate_order_record,
    validate_financial_record,
    validate_dataset_records,
)

SCHEMA_PATH = Path(__file__).parent / "ecommerce_schema.json"

def load_semantic_schema() -> dict:
    """Loads and returns the standardized E-Commerce Semantic Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

__all__ = [
    "load_semantic_schema",
    "SCHEMA_PATH",
    "RuleSeverity",
    "ValidationResult",
    "BUSINESS_RULES_REGISTRY",
    "calculate_gross_sales",
    "calculate_net_sales",
    "calculate_cogs",
    "calculate_gross_profit",
    "calculate_gross_margin",
    "calculate_net_profit",
    "calculate_net_margin",
    "calculate_aov",
    "calculate_cac",
    "calculate_roas",
    "calculate_ltv",
    "calculate_fulfillment_rate",
    "calculate_cancellation_rate",
    "calculate_repurchase_rate",
    "validate_sales_record",
    "validate_product_record",
    "validate_order_record",
    "validate_financial_record",
    "validate_dataset_records",
]


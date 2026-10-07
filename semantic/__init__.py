"""
Semantic Module for E-Commerce AI BI Dashboard.
Provides generic schema definitions, Pydantic validators, declarative business rules, and financial formulas.
"""

from pathlib import Path
import json

from .schema_definition import (
    GenericSchema,
    TableDefinition,
    ColumnDefinition,
    ForeignKeyDefinition,
    RelationshipDefinition,
    MetricDefinition,
    DimensionDefinition,
    SchemaMetadata,
    DataType,
    SemanticType,
    Cardinality,
    ValueRange,
    validate_schema,
    load_schema,
    export_json_schema,
)

from .business_rules import (
    RuleSeverity,
    ValidationResult,
    DeclarativeRule,
    RulesSpecification,
    BusinessRuleEngine,
    DEFAULT_RULE_ENGINE,
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
RULES_PATH = Path(__file__).parent / "rules.json"

def load_semantic_schema() -> dict:
    """Loads and returns the raw dictionary of the standardized E-Commerce Semantic Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_declarative_rules() -> dict:
    """Loads and returns the raw dictionary of the Declarative Business Rules."""
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

__all__ = [
    # Schema Definitions & Validators
    "GenericSchema",
    "TableDefinition",
    "ColumnDefinition",
    "ForeignKeyDefinition",
    "RelationshipDefinition",
    "MetricDefinition",
    "DimensionDefinition",
    "SchemaMetadata",
    "DataType",
    "SemanticType",
    "Cardinality",
    "ValueRange",
    "validate_schema",
    "load_schema",
    "export_json_schema",
    "load_semantic_schema",
    "SCHEMA_PATH",
    # Business Rules & Calculations
    "RuleSeverity",
    "ValidationResult",
    "DeclarativeRule",
    "RulesSpecification",
    "BusinessRuleEngine",
    "DEFAULT_RULE_ENGINE",
    "BUSINESS_RULES_REGISTRY",
    "RULES_PATH",
    "load_declarative_rules",
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

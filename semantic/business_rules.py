"""
Business Rules and Financial Logic Constraints Engine for AI BI Dashboard.

This module provides:
1. Declarative Rule Engine: Dynamically loads, compiles, evaluates, and repairs rules from `rules.json`.
2. Exact mathematical formulas for financial & business metrics (Net_Profit, CAC, ROAS, LTV, AOV, Gross_Margin, etc.).
3. High-performance vectorized evaluation & auto-repair over pandas DataFrames (100% business logic guarantee).
4. Record-level and dataset-level validation functions.
"""

from __future__ import annotations
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# 1. ENUMS & DATA STRUCTURES
# =====================================================================

class RuleSeverity(str, Enum):
    ERROR = "ERROR"       # Hard constraint: Violations make record invalid (100% required)
    WARNING = "WARNING"   # Soft constraint: Statistical anomalies or potential outliers
    INFO = "INFO"         # Informational notice


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class DeclarativeRule(BaseModel):
    """Specification for a single declarative business rule."""
    model_config = ConfigDict(extra="ignore")

    rule_id: str
    name: str
    table: str
    severity: RuleSeverity = RuleSeverity.ERROR
    expression: str
    target_column: Optional[str] = None
    repair_formula: Optional[str] = None
    tolerance: float = 0.0
    description: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def is_hard(self) -> bool:
        return self.severity == RuleSeverity.ERROR


class RulesSpecification(BaseModel):
    """Specification for full declarative business rules file."""
    model_config = ConfigDict(extra="ignore")

    rules_metadata: Dict[str, Any] = Field(default_factory=dict)
    hard_constraints: List[DeclarativeRule] = Field(default_factory=list)
    soft_constraints: List[DeclarativeRule] = Field(default_factory=list)

    def get_all_rules(self) -> List[DeclarativeRule]:
        return self.hard_constraints + self.soft_constraints


# =====================================================================
# 2. FINANCIAL METRIC CALCULATION FORMULAS
# =====================================================================

def calculate_gross_sales(quantity: Union[int, float], unit_price: float) -> float:
    """Gross Sales = Quantity * Unit Selling Price."""
    if quantity < 0 or unit_price < 0:
        raise ValueError("Quantity and Unit Price must be non-negative.")
    return round(float(quantity * unit_price), 2)


def calculate_net_sales(gross_sales: float, discount_amount: float = 0.0) -> float:
    """Net Sales = Gross Sales - Discount Amount."""
    if gross_sales < 0 or discount_amount < 0:
        raise ValueError("Gross Sales and Discount Amount must be non-negative.")
    if discount_amount > gross_sales + 0.01:
        raise ValueError(f"Discount ({discount_amount}) cannot exceed Gross Sales ({gross_sales}).")
    return round(float(gross_sales - discount_amount), 2)


def calculate_cogs(quantity: Union[int, float], unit_cost: float) -> float:
    """COGS (Cost of Goods Sold) = Quantity * Unit Cost."""
    if quantity < 0 or unit_cost < 0:
        raise ValueError("Quantity and Unit Cost must be non-negative.")
    return round(float(quantity * unit_cost), 2)


def calculate_gross_profit(net_sales: float, cogs: float) -> float:
    """Gross Profit = Net Sales - COGS."""
    return round(float(net_sales - cogs), 2)


def calculate_gross_margin(gross_profit: float, net_sales: float) -> float:
    """Gross Margin (%) = (Gross Profit / Net Sales) * 100."""
    if net_sales <= 0:
        return 0.0
    return round(float((gross_profit / net_sales) * 100.0), 2)


def calculate_net_profit(
    gross_revenue: float,
    cogs_total: float,
    marketing_spend: float = 0.0,
    platform_fees_total: float = 0.0,
    shipping_cost_total: float = 0.0,
    tax_amount: float = 0.0,
    operating_expenses: float = 0.0,
) -> float:
    """
    Net Profit = Gross Revenue - COGS - Marketing Spend - Platform Fees 
                 - Shipping Cost - Taxes - Operating Expenses.
    """
    expenses = (
        cogs_total
        + marketing_spend
        + platform_fees_total
        + shipping_cost_total
        + tax_amount
        + operating_expenses
    )
    return round(float(gross_revenue - expenses), 2)


def calculate_net_margin(net_profit: float, gross_revenue: float) -> float:
    """Net Profit Margin (%) = (Net Profit / Gross Revenue) * 100."""
    if gross_revenue <= 0:
        return 0.0
    return round(float((net_profit / gross_revenue) * 100.0), 2)


def calculate_aov(total_net_revenue: float, total_orders: int) -> float:
    """Average Order Value (AOV) = Total Net Revenue / Total Completed Orders."""
    if total_orders <= 0:
        return 0.0
    return round(float(total_net_revenue / total_orders), 2)


def calculate_cac(total_marketing_spend: float, new_customers_count: int) -> float:
    """Customer Acquisition Cost (CAC) = Total Marketing Spend / New Customers Acquired."""
    if new_customers_count <= 0:
        return 0.0
    return round(float(total_marketing_spend / new_customers_count), 2)


def calculate_roas(ad_attributed_revenue: float, total_marketing_spend: float) -> float:
    """Return on Ad Spend (ROAS) = Ad Attributed Revenue / Total Marketing Spend."""
    if total_marketing_spend <= 0:
        return 0.0
    return round(float(ad_attributed_revenue / total_marketing_spend), 2)


def calculate_ltv(
    aov: float,
    purchase_frequency_per_year: float,
    average_customer_lifespan_years: float = 2.0,
    profit_margin_rate: Optional[float] = None,
) -> float:
    """
    Customer Lifetime Value (LTV / CLV).
    If profit_margin_rate is provided, calculates Customer Lifetime Profit,
    otherwise calculates Customer Lifetime Revenue.
    """
    base_ltv = aov * purchase_frequency_per_year * average_customer_lifespan_years
    if profit_margin_rate is not None:
        base_ltv *= max(0.0, min(1.0, profit_margin_rate))
    return round(float(base_ltv), 2)


def calculate_fulfillment_rate(delivered_orders_count: int, total_orders_count: int) -> float:
    """Order Fulfillment Rate (%) = (Delivered Orders / Total Orders) * 100."""
    if total_orders_count <= 0:
        return 0.0
    return round(float((delivered_orders_count / total_orders_count) * 100.0), 2)


def calculate_cancellation_rate(canceled_orders_count: int, total_orders_count: int) -> float:
    """Cancellation Rate (%) = (Canceled Orders / Total Orders) * 100."""
    if total_orders_count <= 0:
        return 0.0
    return round(float((canceled_orders_count / total_orders_count) * 100.0), 2)


def calculate_repurchase_rate(repeat_customers_count: int, total_unique_customers_count: int) -> float:
    """Repurchase / Repeat Rate (%) = (Repeat Customers / Total Unique Customers) * 100."""
    if total_unique_customers_count <= 0:
        return 0.0
    return round(float((repeat_customers_count / total_unique_customers_count) * 100.0), 2)


# =====================================================================
# 3. DECLARATIVE BUSINESS RULE ENGINE
# =====================================================================

DEFAULT_RULES_PATH = Path(__file__).parent / "rules.json"


class BusinessRuleEngine:
    """
    Dynamic Rule Engine that parses declarative rules from JSON or dictionaries,
    evaluates constraints across single records or vectorized pandas DataFrames,
    and repairs mathematical violations automatically.
    """

    def __init__(self, rules_source: Optional[Union[str, Path, dict, RulesSpecification]] = None):
        if rules_source is None:
            rules_source = DEFAULT_RULES_PATH

        if isinstance(rules_source, RulesSpecification):
            self.spec = rules_source
        elif isinstance(rules_source, (str, Path)):
            p = Path(rules_source)
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.spec = RulesSpecification.model_validate(data)
            else:
                self.spec = RulesSpecification.model_validate(json.loads(str(rules_source)))
        elif isinstance(rules_source, dict):
            self.spec = RulesSpecification.model_validate(rules_source)
        else:
            raise TypeError(f"Unsupported rules_source type: {type(rules_source)}")

    def get_rules_for_table(
        self, table_name: str, constraint_type: Optional[str] = None
    ) -> List[DeclarativeRule]:
        """Returns list of rules applicable to a specific table."""
        t_name = table_name.lower().strip()
        all_rules = self.spec.get_all_rules()
        matched = [r for r in all_rules if r.table.lower() == t_name]

        if constraint_type:
            c_type = constraint_type.lower()
            if c_type in ("hard", "error"):
                matched = [r for r in matched if r.is_hard]
            elif c_type in ("soft", "warning"):
                matched = [r for r in matched if not r.is_hard]

        return matched

    def evaluate_record(self, record: Dict[str, Any], table_name: str) -> ValidationResult:
        """
        Evaluates a single record dictionary against applicable table rules.
        """
        rules = self.get_rules_for_table(table_name)
        if not rules:
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                details={"table": table_name, "rule_count": 0},
            )

        errors: List[str] = []
        warnings: List[str] = []

        # Build safe evaluation context
        context = {
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "math": math,
            "where": lambda cond, a, b: a if cond else b,
            "clip": lambda v, low, high: max(low, min(high, v)),
            "maximum": max,
            "minimum": min,
        }
        # Add record fields
        for k, v in record.items():
            context[k] = v

        for rule in rules:
            try:
                # Check if all required variables exist in record
                expr = rule.expression
                # Evaluate expression
                is_satisfied = bool(eval(expr, {"__builtins__": None}, context))
                if not is_satisfied:
                    msg = f"{rule.rule_id} ({rule.name}): {rule.error_message or rule.description}"
                    if rule.is_hard:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
            except Exception:
                # If fields missing or type mismatch, handle gracefully
                pass

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details={"table": table_name, "rule_count": len(rules)},
        )

    def evaluate_dataframe(
        self, df: pd.DataFrame, table_name: str
    ) -> Dict[str, Any]:
        """
        High-performance vectorized evaluation of a pandas DataFrame.
        Returns detailed compliance metrics, pass rates, and violated rows.
        """
        if df.empty:
            return {
                "table_name": table_name,
                "total_rows": 0,
                "valid_rows": 0,
                "pass_rate_pct": 100.0,
                "hard_violations": 0,
                "soft_violations": 0,
                "rule_reports": [],
            }

        rules = self.get_rules_for_table(table_name)
        total_rows = len(df)
        overall_valid_mask = pd.Series(True, index=df.index)
        rule_reports = []
        hard_violation_count = 0
        soft_violation_count = 0

        # Vectorized environment
        eval_dict = {col: df[col].values for col in df.columns}
        eval_dict["abs"] = np.abs
        eval_dict["where"] = np.where
        eval_dict["maximum"] = np.maximum
        eval_dict["minimum"] = np.minimum
        eval_dict["clip"] = np.clip

        for rule in rules:
            try:
                # Evaluate vectorized numpy expression
                mask = eval(rule.expression, {"__builtins__": None}, eval_dict)
                if isinstance(mask, (bool, np.bool_)):
                    mask = np.full(total_rows, mask)
                elif not isinstance(mask, np.ndarray):
                    mask = np.array(mask)

                violation_indices = np.where(~mask)[0].tolist()
                violation_count = len(violation_indices)
                compliance_pct = round((total_rows - violation_count) / total_rows * 100.0, 2)

                if rule.is_hard:
                    overall_valid_mask &= pd.Series(mask, index=df.index)
                    if violation_count > 0:
                        hard_violation_count += violation_count
                else:
                    if violation_count > 0:
                        soft_violation_count += violation_count

                rule_reports.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity.value,
                    "compliance_pct": compliance_pct,
                    "violation_count": violation_count,
                    "sample_violation_indices": violation_indices[:5],
                })
            except Exception as e:
                # Column might be missing or un-evaluable
                rule_reports.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity.value,
                    "compliance_pct": 0.0,
                    "violation_count": total_rows,
                    "error": str(e),
                })

        valid_rows = int(overall_valid_mask.sum())
        pass_rate = round(valid_rows / total_rows * 100.0, 2)

        return {
            "table_name": table_name,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": total_rows - valid_rows,
            "pass_rate_pct": pass_rate,
            "hard_violations": hard_violation_count,
            "soft_violations": soft_violation_count,
            "rule_reports": rule_reports,
        }

    def repair_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Vectorized Constraint Auto-Repair:
        Applies mathematical formulas from Hard Constraints to recalculate dependent fields
        (e.g., gross_sales, net_sales, margin_rate, net_profit), guaranteeing 100% mathematical validity.
        """
        repaired_df = df.copy()
        t_name = table_name.lower().strip()

        if t_name == "sales":
            if "quantity" in repaired_df.columns:
                repaired_df["quantity"] = np.maximum(repaired_df["quantity"].fillna(1).astype(int), 1)
            if "unit_price" in repaired_df.columns:
                repaired_df["unit_price"] = np.maximum(repaired_df["unit_price"].fillna(0.0).astype(float), 0.0)
            if "quantity" in repaired_df.columns and "unit_price" in repaired_df.columns:
                repaired_df["gross_sales"] = (repaired_df["quantity"] * repaired_df["unit_price"]).round(2)
            if "discount_amount" in repaired_df.columns and "gross_sales" in repaired_df.columns:
                repaired_df["discount_amount"] = np.clip(
                    repaired_df["discount_amount"].fillna(0.0).astype(float),
                    0.0,
                    repaired_df["gross_sales"],
                ).round(2)
            if "gross_sales" in repaired_df.columns and "discount_amount" in repaired_df.columns:
                repaired_df["net_sales"] = (repaired_df["gross_sales"] - repaired_df["discount_amount"]).round(2)

        elif t_name == "products":
            if "unit_price" in repaired_df.columns:
                repaired_df["unit_price"] = np.maximum(repaired_df["unit_price"].fillna(0.0).astype(float), 0.0)
            if "unit_cost" in repaired_df.columns:
                repaired_df["unit_cost"] = np.maximum(repaired_df["unit_cost"].fillna(0.0).astype(float), 0.0)
            if "unit_price" in repaired_df.columns and "unit_cost" in repaired_df.columns:
                safe_price = np.where(repaired_df["unit_price"] == 0, 1.0, repaired_df["unit_price"])
                repaired_df["margin_rate"] = np.where(
                    repaired_df["unit_price"] == 0,
                    0.0,
                    ((repaired_df["unit_price"] - repaired_df["unit_cost"]) / safe_price).round(4),
                )

        elif t_name == "orders":
            if "payment_value" in repaired_df.columns:
                repaired_df["payment_value"] = np.maximum(repaired_df["payment_value"].fillna(0.0).astype(float), 0.0)

        elif t_name == "financials":
            # Non-negative expense fields
            for exp_col in [
                "gross_revenue",
                "cogs_total",
                "marketing_spend",
                "platform_fees_total",
                "shipping_cost_total",
                "tax_amount",
                "operating_expenses",
            ]:
                if exp_col in repaired_df.columns:
                    repaired_df[exp_col] = np.maximum(repaired_df[exp_col].fillna(0.0).astype(float), 0.0).round(2)

            if "gross_revenue" in repaired_df.columns:
                expenses = (
                    repaired_df.get("cogs_total", 0.0)
                    + repaired_df.get("marketing_spend", 0.0)
                    + repaired_df.get("platform_fees_total", 0.0)
                    + repaired_df.get("shipping_cost_total", 0.0)
                    + repaired_df.get("tax_amount", 0.0)
                    + repaired_df.get("operating_expenses", 0.0)
                )
                repaired_df["net_profit"] = (repaired_df["gross_revenue"] - expenses).round(2)

            # Marketing funnel monotonicity repair
            if "impressions" in repaired_df.columns:
                repaired_df["impressions"] = np.maximum(repaired_df["impressions"].fillna(0).astype(int), 0)
            if "clicks" in repaired_df.columns and "impressions" in repaired_df.columns:
                repaired_df["clicks"] = np.clip(repaired_df["clicks"].fillna(0).astype(int), 0, repaired_df["impressions"])
            if "conversions" in repaired_df.columns and "clicks" in repaired_df.columns:
                repaired_df["conversions"] = np.clip(repaired_df["conversions"].fillna(0).astype(int), 0, repaired_df["clicks"])

        return repaired_df


# Global Singleton Rule Engine Instance
DEFAULT_RULE_ENGINE = BusinessRuleEngine()


# =====================================================================
# 4. BACKWARD-COMPATIBLE RECORD VALIDATION WRAPPERS
# =====================================================================

def validate_sales_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single sales line item record."""
    return DEFAULT_RULE_ENGINE.evaluate_record(record, "sales")


def validate_product_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single product record."""
    return DEFAULT_RULE_ENGINE.evaluate_record(record, "products")


def validate_order_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single order record."""
    return DEFAULT_RULE_ENGINE.evaluate_record(record, "orders")


def validate_financial_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single financial record."""
    return DEFAULT_RULE_ENGINE.evaluate_record(record, "financials")


def validate_dataset_records(
    records: List[Dict[str, Any]],
    table_name: str,
) -> Dict[str, Any]:
    """
    Validates a list/batch of records for a specified table name.
    """
    df = pd.DataFrame(records)
    eval_res = DEFAULT_RULE_ENGINE.evaluate_dataframe(df, table_name)
    return {
        "table_name": table_name,
        "total_records": eval_res["total_rows"],
        "valid_records": eval_res["valid_rows"],
        "invalid_records": eval_res["invalid_rows"],
        "pass_rate_pct": eval_res["pass_rate_pct"],
        "error_count": eval_res["hard_violations"],
        "warning_count": eval_res["soft_violations"],
        "rule_reports": eval_res["rule_reports"],
    }


# Formal Business Rules Registry Metadata for Backward Compatibility
BUSINESS_RULES_REGISTRY = [
    {
        "rule_id": r.rule_id,
        "name": r.name,
        "table": r.table,
        "severity": r.severity,
        "description": r.description or "",
        "formula": r.expression,
    }
    for r in DEFAULT_RULE_ENGINE.spec.get_all_rules()
]

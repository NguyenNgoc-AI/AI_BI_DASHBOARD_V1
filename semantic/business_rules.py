"""
Business Rules and Financial Logic Constraints for E-Commerce AI BI Dashboard.

This module provides:
1. Exact mathematical and financial metric formulas (Net_Profit, CAC, ROAS, LTV, AOV, Gross_Margin, etc.).
2. Business constraint definitions and integrity invariants.
3. Record-level and dataset-level validation functions.
4. Formal Rule Registry for rule learning, parsing, and data validation gates.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import math


# =====================================================================
# 1. ENUMS & DATA STRUCTURES
# =====================================================================

class RuleSeverity(str, Enum):
    ERROR = "ERROR"       # Hard constraint: Violations make record invalid
    WARNING = "WARNING"   # Soft constraint: Statistical anomalies or potential outliers
    INFO = "INFO"         # Informational notice


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


# =====================================================================
# 2. FINANCIAL METRIC CALCULATION ENGINES
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
    if discount_amount > gross_sales:
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
# 3. FORMAL BUSINESS RULES REGISTRY (FOR VALIDATORS & SYNTHETIC DATA)
# =====================================================================

BUSINESS_RULES_REGISTRY = [
    {
        "rule_id": "BR_SALES_001",
        "name": "Gross Sales Calculation Invariant",
        "table": "sales",
        "severity": RuleSeverity.ERROR,
        "description": "gross_sales must exactly equal quantity * unit_price within 0.02 tolerance.",
        "formula": "gross_sales == quantity * unit_price",
    },
    {
        "rule_id": "BR_SALES_002",
        "name": "Discount Boundary Invariant",
        "table": "sales",
        "severity": RuleSeverity.ERROR,
        "description": "discount_amount must be between 0 and gross_sales.",
        "formula": "0 <= discount_amount <= gross_sales",
    },
    {
        "rule_id": "BR_SALES_003",
        "name": "Net Sales Calculation Invariant",
        "table": "sales",
        "severity": RuleSeverity.ERROR,
        "description": "net_sales must exactly equal gross_sales - discount_amount within 0.02 tolerance.",
        "formula": "net_sales == gross_sales - discount_amount",
    },
    {
        "rule_id": "BR_SALES_004",
        "name": "Positive Line Item Quantity",
        "table": "sales",
        "severity": RuleSeverity.ERROR,
        "description": "quantity must be a positive integer (>= 1).",
        "formula": "quantity >= 1",
    },
    {
        "rule_id": "BR_SALES_005",
        "name": "Platform Fee Boundary",
        "table": "sales",
        "severity": RuleSeverity.WARNING,
        "description": "platform_fee should be non-negative and typically <= 35% of gross_sales.",
        "formula": "0 <= platform_fee <= 0.35 * gross_sales",
    },
    {
        "rule_id": "BR_PROD_001",
        "name": "Product Pricing & Cost Invariant",
        "table": "products",
        "severity": RuleSeverity.ERROR,
        "description": "unit_price and unit_cost must both be non-negative.",
        "formula": "unit_price >= 0 and unit_cost >= 0",
    },
    {
        "rule_id": "BR_PROD_002",
        "name": "Cost-to-Price Ratio Guard",
        "table": "products",
        "severity": RuleSeverity.WARNING,
        "description": "unit_cost should not exceed 1.5 * unit_price (flags extreme loss-making products).",
        "formula": "unit_cost <= 1.5 * unit_price",
    },
    {
        "rule_id": "BR_ORD_001",
        "name": "Payment Value Non-negative",
        "table": "orders",
        "severity": RuleSeverity.ERROR,
        "description": "payment_value must be >= 0.",
        "formula": "payment_value >= 0",
    },
    {
        "rule_id": "BR_ORD_002",
        "name": "Lifecycle Timestamp Monotonicity",
        "table": "orders",
        "severity": RuleSeverity.ERROR,
        "description": "order_purchase_timestamp <= order_approved_at <= order_delivered_carrier_date <= order_delivered_customer_date.",
        "formula": "purchase <= approved <= carrier <= customer",
    },
    {
        "rule_id": "BR_ORD_003",
        "name": "Delivered Status Completeness",
        "table": "orders",
        "severity": RuleSeverity.ERROR,
        "description": "If order_status is 'delivered', order_delivered_customer_date must not be null.",
        "formula": "order_status == 'delivered' => order_delivered_customer_date is not null",
    },
    {
        "rule_id": "BR_FIN_001",
        "name": "Financial Net Profit Formula Invariant",
        "table": "financials",
        "severity": RuleSeverity.ERROR,
        "description": "net_profit must equal gross_revenue - cogs_total - marketing_spend - platform_fees_total - shipping_cost_total - tax_amount - operating_expenses within 0.05 tolerance.",
        "formula": "net_profit == gross_revenue - sum(all_expenses)",
    },
    {
        "rule_id": "BR_FIN_002",
        "name": "Marketing Funnel Monotonicity",
        "table": "financials",
        "severity": RuleSeverity.ERROR,
        "description": "Ad marketing funnel must satisfy: impressions >= clicks >= conversions >= 0.",
        "formula": "impressions >= clicks >= conversions >= 0",
    },
    {
        "rule_id": "BR_FIN_003",
        "name": "Non-negative Financial Costs",
        "table": "financials",
        "severity": RuleSeverity.ERROR,
        "description": "All expense lines (cogs, marketing, platform fees, shipping, tax, opex) must be >= 0.",
        "formula": "min(expenses) >= 0",
    }
]


# =====================================================================
# 4. RECORD VALIDATOR FUNCTIONS
# =====================================================================

def validate_sales_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single sales line item record against business rules."""
    errors: List[str] = []
    warnings: List[str] = []

    qty = record.get("quantity")
    price = record.get("unit_price")
    gross = record.get("gross_sales")
    discount = record.get("discount_amount", 0.0)
    net = record.get("net_sales")
    platform_fee = record.get("platform_fee", 0.0)

    # Rule BR_SALES_004
    if qty is None or qty < 1:
        errors.append(f"BR_SALES_004: Quantity must be >= 1 (got {qty}).")

    # Rule BR_SALES_001
    if qty is not None and price is not None and gross is not None:
        expected_gross = qty * price
        if not math.isclose(gross, expected_gross, abs_tol=0.05):
            errors.append(
                f"BR_SALES_001: gross_sales ({gross}) != quantity ({qty}) * unit_price ({price}) [expected {expected_gross}]."
            )

    # Rule BR_SALES_002
    if discount is not None and gross is not None:
        if discount < 0:
            errors.append(f"BR_SALES_002: discount_amount cannot be negative (got {discount}).")
        elif discount > gross + 0.01:
            errors.append(
                f"BR_SALES_002: discount_amount ({discount}) exceeds gross_sales ({gross})."
            )

    # Rule BR_SALES_003
    if gross is not None and discount is not None and net is not None:
        expected_net = gross - discount
        if not math.isclose(net, expected_net, abs_tol=0.05):
            errors.append(
                f"BR_SALES_003: net_sales ({net}) != gross_sales ({gross}) - discount ({discount}) [expected {expected_net}]."
            )

    # Rule BR_SALES_005
    if platform_fee is not None and gross is not None and gross > 0:
        if platform_fee < 0:
            errors.append(f"BR_SALES_005: platform_fee cannot be negative (got {platform_fee}).")
        elif platform_fee > 0.40 * gross:
            warnings.append(
                f"BR_SALES_005: High platform_fee ({platform_fee}) exceeds 40% of gross_sales ({gross})."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={"record_type": "sales", "sales_id": record.get("sales_id")},
    )


def validate_product_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single product catalog record."""
    errors: List[str] = []
    warnings: List[str] = []

    price = record.get("unit_price")
    cost = record.get("unit_cost")

    # Rule BR_PROD_001
    if price is None or price < 0:
        errors.append(f"BR_PROD_001: unit_price must be >= 0 (got {price}).")
    if cost is None or cost < 0:
        errors.append(f"BR_PROD_001: unit_cost must be >= 0 (got {cost}).")

    # Rule BR_PROD_002
    if price is not None and cost is not None and price > 0:
        if cost > 1.5 * price:
            warnings.append(
                f"BR_PROD_002: Unit cost ({cost}) is over 150% of unit price ({price}) (loss leader)."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={"record_type": "product", "product_id": record.get("product_id")},
    )


def validate_order_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single order record against lifecycle and financial constraints."""
    errors: List[str] = []
    warnings: List[str] = []

    payment_val = record.get("payment_value")
    status = record.get("order_status")
    delivered_date = record.get("order_delivered_customer_date")

    # Rule BR_ORD_001
    if payment_val is not None and payment_val < 0:
        errors.append(f"BR_ORD_001: payment_value cannot be negative (got {payment_val}).")

    # Rule BR_ORD_003
    if status == "delivered" and (delivered_date is None or str(delivered_date).strip() == ""):
        errors.append(
            "BR_ORD_003: Order status is 'delivered' but order_delivered_customer_date is missing."
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={"record_type": "order", "order_id": record.get("order_id")},
    )


def validate_financial_record(record: Dict[str, Any]) -> ValidationResult:
    """Validates a single periodic financial ledger record."""
    errors: List[str] = []
    warnings: List[str] = []

    gross_rev = record.get("gross_revenue", 0.0)
    cogs = record.get("cogs_total", 0.0)
    mkt = record.get("marketing_spend", 0.0)
    plat = record.get("platform_fees_total", 0.0)
    ship = record.get("shipping_cost_total", 0.0)
    tax = record.get("tax_amount", 0.0)
    opex = record.get("operating_expenses", 0.0)
    net_profit = record.get("net_profit")

    impressions = record.get("impressions")
    clicks = record.get("clicks")
    conversions = record.get("conversions")

    # Rule BR_FIN_003
    for name, val in [
        ("gross_revenue", gross_rev),
        ("cogs_total", cogs),
        ("marketing_spend", mkt),
        ("platform_fees_total", plat),
        ("shipping_cost_total", ship),
        ("tax_amount", tax),
        ("operating_expenses", opex),
    ]:
        if val is not None and val < 0:
            errors.append(f"BR_FIN_003: {name} cannot be negative (got {val}).")

    # Rule BR_FIN_001
    if net_profit is not None:
        expected_profit = gross_rev - (cogs + mkt + plat + ship + tax + opex)
        if not math.isclose(net_profit, expected_profit, abs_tol=0.10):
            errors.append(
                f"BR_FIN_001: net_profit ({net_profit}) != gross_revenue ({gross_rev}) - sum_expenses ({round(gross_rev - expected_profit, 2)}) [expected {round(expected_profit, 2)}]."
            )

    # Rule BR_FIN_002
    if impressions is not None and clicks is not None and conversions is not None:
        if impressions < 0 or clicks < 0 or conversions < 0:
            errors.append("BR_FIN_002: Funnel metrics cannot be negative.")
        if clicks > impressions:
            errors.append(f"BR_FIN_002: clicks ({clicks}) cannot exceed impressions ({impressions}).")
        if conversions > clicks:
            warnings.append(
                f"BR_FIN_002: conversions ({conversions}) exceeds clicks ({clicks}) (unusual attribution)."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        details={"record_type": "financial", "record_id": record.get("financial_record_id")},
    )


# =====================================================================
# 5. DATASET BATCH INTEGRITY VALIDATOR
# =====================================================================

def validate_dataset_records(
    records: List[Dict[str, Any]],
    table_name: str,
) -> Dict[str, Any]:
    """
    Validates a list/batch of records for a specified table name.
    Returns overall pass rate, error list, and warning breakdown.
    """
    validators = {
        "sales": validate_sales_record,
        "products": validate_product_record,
        "orders": validate_order_record,
        "financials": validate_financial_record,
    }

    validator = validators.get(table_name.lower())
    if not validator:
        return {
            "table_name": table_name,
            "total_records": len(records),
            "valid_records": len(records),
            "invalid_records": 0,
            "pass_rate_pct": 100.0,
            "message": f"No custom business validator defined for '{table_name}'. Treated as valid.",
            "error_samples": [],
            "warning_samples": [],
        }

    total = len(records)
    valid_count = 0
    all_errors = []
    all_warnings = []

    for idx, rec in enumerate(records):
        res = validator(rec)
        if res.is_valid:
            valid_count += 1
        else:
            all_errors.append({"row_index": idx, "errors": res.errors, "record": rec})
        if res.warnings:
            all_warnings.append({"row_index": idx, "warnings": res.warnings, "record": rec})

    pass_rate = round((valid_count / total * 100.0), 2) if total > 0 else 100.0

    return {
        "table_name": table_name,
        "total_records": total,
        "valid_records": valid_count,
        "invalid_records": total - valid_count,
        "pass_rate_pct": pass_rate,
        "error_count": len(all_errors),
        "warning_count": len(all_warnings),
        "error_samples": all_errors[:10],
        "warning_samples": all_warnings[:10],
    }

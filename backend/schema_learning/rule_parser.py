"""
Rule Parser and Constraint Enforcement Engine for AI BI Dashboard.

Converts business rules and semantic constraints into vectorized evaluation functions.
Provides:
1. ExecutableConstraint definitions for all 11 registered business rules.
2. Vectorized DataFrame validation and single-record validation.
3. Post-generation Constraint Enforcement (Repair Engine) ensuring 100% mathematical integrity.
4. Comprehensive Validation Reporting.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from semantic.business_rules import (
    BUSINESS_RULES_REGISTRY,
    RuleSeverity,
    ValidationResult,
    validate_financial_record,
    validate_order_record,
    validate_product_record,
    validate_sales_record,
)


@dataclass
class ExecutableConstraint:
    """Represents an executable business rule constraint."""
    rule_id: str
    name: str
    table: str
    severity: RuleSeverity
    description: str
    formula: str
    check_fn: Callable[[pd.DataFrame], pd.Series]
    repair_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None


@dataclass
class RuleViolationSummary:
    """Summary of violations for a single rule."""
    rule_id: str
    rule_name: str
    severity: str
    violation_count: int
    violation_rate_pct: float
    sample_indices: List[int] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Comprehensive validation report for a DataFrame or dataset."""
    total_records: int
    valid_records: int
    invalid_records: int
    overall_pass_rate_pct: float
    has_blocking_errors: bool
    rule_summaries: Dict[str, RuleViolationSummary] = field(default_factory=dict)
    summary_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary."""
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "overall_pass_rate_pct": self.overall_pass_rate_pct,
            "has_blocking_errors": self.has_blocking_errors,
            "rule_summaries": {k: asdict(v) for k, v in self.rule_summaries.items()},
            "summary_message": self.summary_message,
        }


class RuleParser:
    """
    Parses Business Rules into executable vectorized evaluation constraints.
    """

    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.rules_registry = custom_rules or BUSINESS_RULES_REGISTRY
        self.executable_constraints: Dict[str, ExecutableConstraint] = {}
        self._compile_constraints()

    def _compile_constraints(self) -> None:
        """Compiles rule definitions into vectorized Pandas check functions."""
        # BR_SALES_001: gross_sales == quantity * unit_price
        self.executable_constraints["BR_SALES_001"] = ExecutableConstraint(
            rule_id="BR_SALES_001",
            name="Gross Sales Calculation Invariant",
            table="sales",
            severity=RuleSeverity.ERROR,
            description="gross_sales must equal quantity * unit_price within 0.05 tolerance.",
            formula="gross_sales == quantity * unit_price",
            check_fn=self._check_gross_sales,
        )

        # BR_SALES_002: 0 <= discount_amount <= gross_sales
        self.executable_constraints["BR_SALES_002"] = ExecutableConstraint(
            rule_id="BR_SALES_002",
            name="Discount Boundary Invariant",
            table="sales",
            severity=RuleSeverity.ERROR,
            description="discount_amount must be between 0 and gross_sales.",
            formula="0 <= discount_amount <= gross_sales",
            check_fn=self._check_discount_boundary,
        )

        # BR_SALES_003: net_sales == gross_sales - discount_amount
        self.executable_constraints["BR_SALES_003"] = ExecutableConstraint(
            rule_id="BR_SALES_003",
            name="Net Sales Calculation Invariant",
            table="sales",
            severity=RuleSeverity.ERROR,
            description="net_sales must equal gross_sales - discount_amount within 0.05 tolerance.",
            formula="net_sales == gross_sales - discount_amount",
            check_fn=self._check_net_sales,
        )

        # BR_SALES_004: quantity >= 1
        self.executable_constraints["BR_SALES_004"] = ExecutableConstraint(
            rule_id="BR_SALES_004",
            name="Positive Line Item Quantity",
            table="sales",
            severity=RuleSeverity.ERROR,
            description="quantity must be a positive integer (>= 1).",
            formula="quantity >= 1",
            check_fn=self._check_positive_quantity,
        )

        # BR_SALES_005: 0 <= platform_fee <= 0.40 * gross_sales
        self.executable_constraints["BR_SALES_005"] = ExecutableConstraint(
            rule_id="BR_SALES_005",
            name="Platform Fee Boundary",
            table="sales",
            severity=RuleSeverity.WARNING,
            description="platform_fee should be non-negative and <= 40% of gross_sales.",
            formula="0 <= platform_fee <= 0.40 * gross_sales",
            check_fn=self._check_platform_fee,
        )

        # BR_PROD_001: unit_price >= 0 and unit_cost >= 0
        self.executable_constraints["BR_PROD_001"] = ExecutableConstraint(
            rule_id="BR_PROD_001",
            name="Product Pricing & Cost Invariant",
            table="products",
            severity=RuleSeverity.ERROR,
            description="unit_price and unit_cost must both be non-negative.",
            formula="unit_price >= 0 and unit_cost >= 0",
            check_fn=self._check_product_price_cost,
        )

        # BR_PROD_002: unit_cost <= 1.5 * unit_price
        self.executable_constraints["BR_PROD_002"] = ExecutableConstraint(
            rule_id="BR_PROD_002",
            name="Cost-to-Price Ratio Guard",
            table="products",
            severity=RuleSeverity.WARNING,
            description="unit_cost should not exceed 1.5 * unit_price.",
            formula="unit_cost <= 1.5 * unit_price",
            check_fn=self._check_cost_to_price_ratio,
        )

        # BR_ORD_001: payment_value >= 0
        self.executable_constraints["BR_ORD_001"] = ExecutableConstraint(
            rule_id="BR_ORD_001",
            name="Payment Value Non-negative",
            table="orders",
            severity=RuleSeverity.ERROR,
            description="payment_value must be >= 0.",
            formula="payment_value >= 0",
            check_fn=self._check_payment_value,
        )

        # BR_ORD_002: purchase <= approved <= carrier <= customer
        self.executable_constraints["BR_ORD_002"] = ExecutableConstraint(
            rule_id="BR_ORD_002",
            name="Lifecycle Timestamp Monotonicity",
            table="orders",
            severity=RuleSeverity.ERROR,
            description="order_purchase_timestamp <= order_approved_at <= order_delivered_carrier_date <= order_delivered_customer_date.",
            formula="purchase <= approved <= carrier <= customer",
            check_fn=self._check_lifecycle_timestamps,
        )

        # BR_ORD_003: delivered => order_delivered_customer_date not null
        self.executable_constraints["BR_ORD_003"] = ExecutableConstraint(
            rule_id="BR_ORD_003",
            name="Delivered Status Completeness",
            table="orders",
            severity=RuleSeverity.ERROR,
            description="If order_status is 'delivered', order_delivered_customer_date must not be null.",
            formula="order_status == 'delivered' => order_delivered_customer_date is not null",
            check_fn=self._check_delivered_completeness,
        )

        # BR_FIN_001: net_profit == gross_revenue - sum(expenses)
        self.executable_constraints["BR_FIN_001"] = ExecutableConstraint(
            rule_id="BR_FIN_001",
            name="Financial Net Profit Formula Invariant",
            table="financials",
            severity=RuleSeverity.ERROR,
            description="net_profit must equal gross_revenue - sum(all_expenses) within 0.10 tolerance.",
            formula="net_profit == gross_revenue - sum(all_expenses)",
            check_fn=self._check_net_profit,
        )

        # BR_FIN_002: impressions >= clicks >= conversions >= 0
        self.executable_constraints["BR_FIN_002"] = ExecutableConstraint(
            rule_id="BR_FIN_002",
            name="Marketing Funnel Monotonicity",
            table="financials",
            severity=RuleSeverity.ERROR,
            description="Ad marketing funnel must satisfy: impressions >= clicks >= conversions >= 0.",
            formula="impressions >= clicks >= conversions >= 0",
            check_fn=self._check_funnel_monotonicity,
        )

        # BR_FIN_003: Non-negative Financial Costs
        self.executable_constraints["BR_FIN_003"] = ExecutableConstraint(
            rule_id="BR_FIN_003",
            name="Non-negative Financial Costs",
            table="financials",
            severity=RuleSeverity.ERROR,
            description="All expense lines must be >= 0.",
            formula="min(expenses) >= 0",
            check_fn=self._check_non_negative_costs,
        )

        # Declarative Specification Aliases (HR_* / SR_* mappings)
        declarative_mappings = {
            "HR_SALES_001": "BR_SALES_001",
            "HR_SALES_002": "BR_SALES_002",
            "HR_SALES_003": "BR_SALES_003",
            "HR_SALES_004": "BR_SALES_004",
            "SR_SALES_001": "BR_SALES_005",
            "HR_PROD_001": "BR_PROD_001",
            "SR_PROD_001": "BR_PROD_002",
            "HR_ORD_001": "BR_ORD_001",
            "HR_ORD_002": "BR_ORD_002",
            "HR_FIN_001": "BR_FIN_001",
            "HR_FIN_002": "BR_FIN_002",
            "HR_FIN_003": "BR_FIN_003",
        }
        for decl_id, legacy_id in declarative_mappings.items():
            if legacy_id in self.executable_constraints and decl_id not in self.executable_constraints:
                base = self.executable_constraints[legacy_id]
                self.executable_constraints[decl_id] = ExecutableConstraint(
                    rule_id=decl_id,
                    name=base.name,
                    table=base.table,
                    severity=base.severity,
                    description=base.description,
                    formula=base.formula,
                    check_fn=base.check_fn,
                    repair_fn=base.repair_fn,
                )

    # -----------------------------------------------------------------
    # Vectorized Check Functions
    # -----------------------------------------------------------------

    @staticmethod
    def _check_gross_sales(df: pd.DataFrame) -> pd.Series:
        required = ["gross_sales", "quantity", "unit_price"]
        if not all(c in df.columns for c in required):
            return pd.Series(True, index=df.index)
        expected = df["quantity"] * df["unit_price"]
        return (df["gross_sales"] - expected).abs() <= 0.05

    @staticmethod
    def _check_discount_boundary(df: pd.DataFrame) -> pd.Series:
        if "discount_amount" not in df.columns:
            return pd.Series(True, index=df.index)
        gross = df["gross_sales"] if "gross_sales" in df.columns else (df["quantity"] * df["unit_price"] if "quantity" in df.columns and "unit_price" in df.columns else 1e9)
        return (df["discount_amount"] >= 0) & (df["discount_amount"] <= gross + 0.02)

    @staticmethod
    def _check_net_sales(df: pd.DataFrame) -> pd.Series:
        required = ["net_sales", "gross_sales", "discount_amount"]
        if not all(c in df.columns for c in required):
            return pd.Series(True, index=df.index)
        expected = df["gross_sales"] - df["discount_amount"]
        return (df["net_sales"] - expected).abs() <= 0.05

    @staticmethod
    def _check_positive_quantity(df: pd.DataFrame) -> pd.Series:
        if "quantity" not in df.columns:
            return pd.Series(True, index=df.index)
        return (df["quantity"] >= 1) & (df["quantity"] == df["quantity"].round())

    @staticmethod
    def _check_platform_fee(df: pd.DataFrame) -> pd.Series:
        if "platform_fee" not in df.columns:
            return pd.Series(True, index=df.index)
        gross = df["gross_sales"] if "gross_sales" in df.columns else 1e9
        return (df["platform_fee"] >= 0) & (df["platform_fee"] <= 0.40 * gross + 0.01)

    @staticmethod
    def _check_product_price_cost(df: pd.DataFrame) -> pd.Series:
        valid = pd.Series(True, index=df.index)
        if "unit_price" in df.columns:
            valid = valid & (df["unit_price"] >= 0)
        if "unit_cost" in df.columns:
            valid = valid & (df["unit_cost"] >= 0)
        return valid

    @staticmethod
    def _check_cost_to_price_ratio(df: pd.DataFrame) -> pd.Series:
        if "unit_price" in df.columns and "unit_cost" in df.columns:
            # Only test rows where price > 0
            has_price = df["unit_price"] > 0
            return ~has_price | (df["unit_cost"] <= 1.5 * df["unit_price"])
        return pd.Series(True, index=df.index)

    @staticmethod
    def _check_payment_value(df: pd.DataFrame) -> pd.Series:
        if "payment_value" not in df.columns:
            return pd.Series(True, index=df.index)
        return df["payment_value"] >= 0

    @staticmethod
    def _check_lifecycle_timestamps(df: pd.DataFrame) -> pd.Series:
        p_col = "order_purchase_timestamp"
        a_col = "order_approved_at"
        c_col = "order_delivered_carrier_date"
        d_col = "order_delivered_customer_date"

        cols = [c for c in [p_col, a_col, c_col, d_col] if c in df.columns]
        if len(cols) < 2:
            return pd.Series(True, index=df.index)

        dts = {col: pd.to_datetime(df[col], errors="coerce") for col in cols}
        valid = pd.Series(True, index=df.index)

        if p_col in dts and a_col in dts:
            mask = dts[p_col].notna() & dts[a_col].notna()
            valid = valid & (~mask | (dts[p_col] <= dts[a_col]))

        if a_col in dts and c_col in dts:
            mask = dts[a_col].notna() & dts[c_col].notna()
            valid = valid & (~mask | (dts[a_col] <= dts[c_col]))

        if c_col in dts and d_col in dts:
            mask = dts[c_col].notna() & dts[d_col].notna()
            valid = valid & (~mask | (dts[c_col] <= dts[d_col]))

        return valid

    @staticmethod
    def _check_delivered_completeness(df: pd.DataFrame) -> pd.Series:
        if "order_status" not in df.columns or "order_delivered_customer_date" not in df.columns:
            return pd.Series(True, index=df.index)
        is_delivered = df["order_status"].astype(str).str.lower() == "delivered"
        has_delivery_date = df["order_delivered_customer_date"].notna() & (df["order_delivered_customer_date"].astype(str).str.strip() != "")
        return ~is_delivered | has_delivery_date

    @staticmethod
    def _check_net_profit(df: pd.DataFrame) -> pd.Series:
        if "net_profit" not in df.columns:
            return pd.Series(True, index=df.index)
        
        # Check if calculating from gross_profit or net_sales/gross_revenue
        if "gross_profit" in df.columns:
            base_profit = df["gross_profit"]
        elif "net_sales" in df.columns:
            cogs = df["cogs"] if "cogs" in df.columns else 0.0
            base_profit = df["net_sales"] - cogs
        elif "gross_revenue" in df.columns:
            cogs_tot = df["cogs_total"] if "cogs_total" in df.columns else 0.0
            base_profit = df["gross_revenue"] - cogs_tot
        else:
            return pd.Series(True, index=df.index)

        mkt = df["marketing_spend"] if "marketing_spend" in df.columns else 0.0
        plat = df["platform_fees_total"] if "platform_fees_total" in df.columns else (df["platform_fee"] if "platform_fee" in df.columns else 0.0)
        ship = df["shipping_cost_total"] if "shipping_cost_total" in df.columns else 0.0
        tax = df["tax_amount"] if "tax_amount" in df.columns else 0.0
        opex = df["operating_expenses"] if "operating_expenses" in df.columns else 0.0

        expected_profit = base_profit - (mkt + plat + ship + tax + opex)
        return (df["net_profit"] - expected_profit).abs() <= 0.05

    @staticmethod
    def _check_funnel_monotonicity(df: pd.DataFrame) -> pd.Series:
        has_imp = "impressions" in df.columns
        has_clk = "clicks" in df.columns
        has_conv = "conversions" in df.columns

        valid = pd.Series(True, index=df.index)
        if has_imp and has_clk:
            mask = df["impressions"].notna() & df["clicks"].notna()
            valid = valid & (~mask | ((df["clicks"] <= df["impressions"]) & (df["clicks"] >= 0)))

        if has_clk and has_conv:
            mask = df["clicks"].notna() & df["conversions"].notna()
            valid = valid & (~mask | ((df["conversions"] <= df["clicks"]) & (df["conversions"] >= 0)))

        return valid

    @staticmethod
    def _check_non_negative_costs(df: pd.DataFrame) -> pd.Series:
        cost_cols = [
            "cogs_total", "cogs", "marketing_spend", "platform_fees_total", "platform_fee",
            "shipping_cost_total", "freight_value", "tax_amount", "operating_expenses"
        ]
        valid = pd.Series(True, index=df.index)
        for col in cost_cols:
            if col in df.columns:
                valid = valid & (df[col] >= 0)
        return valid


class ConstraintEngine:
    """
    Evaluates DataFrames against business rules and enforces mathematical constraints.
    """

    def __init__(self, parser: Optional[RuleParser] = None):
        self.parser = parser or RuleParser()

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        rules: Optional[List[str]] = None,
    ) -> ValidationReport:
        """
        Runs vectorized validation on a DataFrame across all (or specified) rules.
        """
        total = len(df)
        if total == 0:
            return ValidationReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                overall_pass_rate_pct=100.0,
                has_blocking_errors=False,
                summary_message="DataFrame is empty.",
            )

        overall_valid_mask = pd.Series(True, index=df.index)
        rule_summaries: Dict[str, RuleViolationSummary] = {}
        has_blocking_error = False

        constraints = self.parser.executable_constraints
        target_rule_ids = rules or list(constraints.keys())

        for rule_id in target_rule_ids:
            if rule_id not in constraints:
                continue
            constraint = constraints[rule_id]
            try:
                valid_mask = constraint.check_fn(df)
                violation_mask = ~valid_mask
                violation_count = int(violation_mask.sum())
                violation_rate = round(float(violation_count / total * 100.0), 2)
                sample_idx = df.index[violation_mask].tolist()[:10]

                if constraint.severity == RuleSeverity.ERROR:
                    overall_valid_mask = overall_valid_mask & valid_mask
                    if violation_count > 0:
                        has_blocking_error = True

                rule_summaries[rule_id] = RuleViolationSummary(
                    rule_id=rule_id,
                    rule_name=constraint.name,
                    severity=constraint.severity.value,
                    violation_count=violation_count,
                    violation_rate_pct=violation_rate,
                    sample_indices=sample_idx,
                )
            except Exception as e:
                rule_summaries[rule_id] = RuleViolationSummary(
                    rule_id=rule_id,
                    rule_name=constraint.name,
                    severity=constraint.severity.value,
                    violation_count=0,
                    violation_rate_pct=0.0,
                    sample_indices=[],
                )

        valid_count = int(overall_valid_mask.sum())
        invalid_count = total - valid_count
        pass_rate = round(float(valid_count / total * 100.0), 2)

        msg = f"Validation completed: {valid_count}/{total} records valid ({pass_rate}% pass rate)."

        return ValidationReport(
            total_records=total,
            valid_records=valid_count,
            invalid_records=invalid_count,
            overall_pass_rate_pct=pass_rate,
            has_blocking_errors=has_blocking_error,
            rule_summaries=rule_summaries,
            summary_message=msg,
        )

    def enforce_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Repairs mathematical inconsistencies and enforces invariants on generated data:
        1. Non-negativity of prices and costs.
        2. Positive integer quantity.
        3. gross_sales = quantity * unit_price.
        4. discount_amount bounded by [0, gross_sales].
        5. net_sales = gross_sales - discount_amount.
        6. cogs = quantity * unit_cost.
        7. gross_profit = net_sales - cogs.
        8. gross_margin_pct = (gross_profit / net_sales) * 100.
        9. platform_fee bounded by [0, 0.35 * gross_sales].
        10. Timestamp ordering (monotonic lifecycle dates).
        11. Financial net_profit = gross_revenue - expenses.
        12. Funnel monotonicity: impressions >= clicks >= conversions >= 0.
        """
        repaired = df.copy()

        # 1. Quantities: integer >= 1
        if "quantity" in repaired.columns:
            repaired["quantity"] = np.maximum(1, repaired["quantity"].fillna(1).round().astype(int))

        # 2. Unit price & Unit cost >= 0
        if "unit_price" in repaired.columns:
            repaired["unit_price"] = np.maximum(0.0, repaired["unit_price"].fillna(0.0)).round(2)
        if "unit_cost" in repaired.columns:
            repaired["unit_cost"] = np.maximum(0.0, repaired["unit_cost"].fillna(0.0)).round(2)

        # 3. Gross Sales = quantity * unit_price
        if "quantity" in repaired.columns and "unit_price" in repaired.columns:
            repaired["gross_sales"] = (repaired["quantity"] * repaired["unit_price"]).round(2)

        # 4. Discount Amount: 0 <= discount <= gross_sales
        if "discount_amount" in repaired.columns:
            repaired["discount_amount"] = np.maximum(0.0, repaired["discount_amount"].fillna(0.0)).round(2)
            if "gross_sales" in repaired.columns:
                repaired["discount_amount"] = np.minimum(repaired["gross_sales"], repaired["discount_amount"])

        # 5. Net Sales = gross_sales - discount_amount
        if "gross_sales" in repaired.columns and "discount_amount" in repaired.columns:
            repaired["net_sales"] = (repaired["gross_sales"] - repaired["discount_amount"]).round(2)

        # 6. COGS = quantity * unit_cost
        if "quantity" in repaired.columns and "unit_cost" in repaired.columns:
            repaired["cogs"] = (repaired["quantity"] * repaired["unit_cost"]).round(2)

        # 7. Gross Profit = net_sales - cogs
        if "net_sales" in repaired.columns and "cogs" in repaired.columns:
            repaired["gross_profit"] = (repaired["net_sales"] - repaired["cogs"]).round(2)

        # 8. Gross Margin Pct = (gross_profit / net_sales) * 100
        if "gross_profit" in repaired.columns and "net_sales" in repaired.columns:
            safe_net = np.where(repaired["net_sales"] > 0, repaired["net_sales"], np.nan)
            repaired["gross_margin_pct"] = np.where(
                np.isnan(safe_net), 0.0, ((repaired["gross_profit"] / safe_net) * 100.0).round(2)
            )

        # 9. Platform Fee: [0, 0.35 * gross_sales]
        if "platform_fee" in repaired.columns:
            repaired["platform_fee"] = np.maximum(0.0, repaired["platform_fee"].fillna(0.0)).round(2)
            if "gross_sales" in repaired.columns:
                repaired["platform_fee"] = np.minimum(0.35 * repaired["gross_sales"], repaired["platform_fee"]).round(2)

        # 10. Freight Value & Operating Expenses >= 0
        for col in ["freight_value", "tax_amount", "operating_expenses", "marketing_spend", "payment_value"]:
            if col in repaired.columns:
                repaired[col] = np.maximum(0.0, repaired[col].fillna(0.0)).round(2)

        # 11. Timestamps Monotonicity
        p_col = "order_purchase_timestamp"
        a_col = "order_approved_at"
        c_col = "order_delivered_carrier_date"
        d_col = "order_delivered_customer_date"

        if all(c in repaired.columns for c in [p_col, a_col, c_col, d_col]):
            p_dt = pd.to_datetime(repaired[p_col], errors="coerce")
            a_dt = pd.to_datetime(repaired[a_col], errors="coerce")
            c_dt = pd.to_datetime(repaired[c_col], errors="coerce")
            d_dt = pd.to_datetime(repaired[d_col], errors="coerce")

            # Monotonic clamp
            a_dt = a_dt.combine_first(p_dt + pd.Timedelta(minutes=15))
            a_dt = np.maximum(p_dt, a_dt)

            c_dt = c_dt.combine_first(a_dt + pd.Timedelta(hours=24))
            c_dt = np.maximum(a_dt, c_dt)

            d_dt = d_dt.combine_first(c_dt + pd.Timedelta(days=3))
            d_dt = np.maximum(c_dt, d_dt)

            repaired[p_col] = p_dt.dt.strftime("%Y-%m-%d %H:%M:%S")
            repaired[a_col] = a_dt.dt.strftime("%Y-%m-%d %H:%M:%S")
            repaired[c_col] = c_dt.dt.strftime("%Y-%m-%d %H:%M:%S")
            repaired[d_col] = d_dt.dt.strftime("%Y-%m-%d %H:%M:%S")

        # 12. Financials Net Profit Invariant
        if "net_profit" in repaired.columns:
            if "gross_profit" in repaired.columns:
                base_profit = repaired["gross_profit"]
            elif "net_sales" in repaired.columns:
                cogs = repaired["cogs"] if "cogs" in repaired.columns else 0.0
                base_profit = repaired["net_sales"] - cogs
            elif "gross_revenue" in repaired.columns:
                cogs_tot = repaired["cogs_total"] if "cogs_total" in repaired.columns else 0.0
                base_profit = repaired["gross_revenue"] - cogs_tot
            else:
                base_profit = pd.Series(0.0, index=repaired.index)

            mkt_tot = repaired["marketing_spend"] if "marketing_spend" in repaired.columns else 0.0
            plat_tot = repaired["platform_fees_total"] if "platform_fees_total" in repaired.columns else (repaired["platform_fee"] if "platform_fee" in repaired.columns else 0.0)
            ship_tot = repaired["shipping_cost_total"] if "shipping_cost_total" in repaired.columns else 0.0
            tax_tot = repaired["tax_amount"] if "tax_amount" in repaired.columns else 0.0
            opex_tot = repaired["operating_expenses"] if "operating_expenses" in repaired.columns else 0.0

            total_expenses = mkt_tot + plat_tot + ship_tot + tax_tot + opex_tot
            repaired["net_profit"] = (base_profit - total_expenses).round(2)

            if "net_margin_pct" in repaired.columns:
                base_rev = repaired["gross_sales"] if "gross_sales" in repaired.columns else (repaired["gross_revenue"] if "gross_revenue" in repaired.columns else (repaired["net_sales"] if "net_sales" in repaired.columns else 0.0))
                safe_rev = np.where(base_rev > 0, base_rev, np.nan)
                repaired["net_margin_pct"] = np.where(
                    np.isnan(safe_rev), 0.0, ((repaired["net_profit"] / safe_rev) * 100.0).round(2)
                )

        # 13. Marketing Funnel Monotonicity
        if all(c in repaired.columns for c in ["impressions", "clicks", "conversions"]):
            repaired["impressions"] = np.maximum(0, repaired["impressions"].fillna(0).round().astype(int))
            repaired["clicks"] = np.minimum(repaired["impressions"], np.maximum(0, repaired["clicks"].fillna(0).round().astype(int)))
            repaired["conversions"] = np.minimum(repaired["clicks"], np.maximum(0, repaired["conversions"].fillna(0).round().astype(int)))

        return repaired

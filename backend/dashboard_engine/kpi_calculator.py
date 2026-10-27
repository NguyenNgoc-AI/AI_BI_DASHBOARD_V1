"""Pure e-commerce KPI calculations connected with semantic business rules."""

from backend.dashboard_engine.data_pipeline import REQUIRED_COLUMNS, build_canonical_view
from semantic.business_rules import calculate_net_profit


def _sum(rows: list[dict], field: str) -> float:
    return sum(float(row.get(field, 0) or 0) for row in rows)


def _ensure_canonical_rows(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    first_keys = set(rows[0].keys())
    if REQUIRED_COLUMNS <= first_keys:
        return rows
    return build_canonical_view(rows)


def calculate_kpis(rows: list[dict]) -> dict[str, float | int | None]:
    view_rows = _ensure_canonical_rows(rows)
    revenue = round(_sum(view_rows, "revenue"), 2)
    cost = round(_sum(view_rows, "cost"), 2)
    orders = len({row["order_id"] for row in view_rows})
    ad_spend = _sum(view_rows, "ad_spend") if any(row.get("ad_spend") is not None for row in view_rows) else None
    new_customers = _sum(view_rows, "new_customers") if any(row.get("new_customers") is not None for row in view_rows) else None
    customers = {row["customer_id"] for row in view_rows if row.get("customer_id") not in (None, "")}

    if any(row.get("net_profit") is not None for row in view_rows):
        net_profit = round(_sum(view_rows, "net_profit"), 2)
    elif any(
        any(row.get(col) is not None for row in view_rows)
        for col in ("platform_fee", "tax_amount", "operating_expenses")
    ):
        net_profit = calculate_net_profit(
            gross_revenue=revenue,
            cogs_total=cost,
            marketing_spend=ad_spend or 0.0,
            platform_fees_total=_sum(view_rows, "platform_fee"),
            shipping_cost_total=0.0,
            tax_amount=_sum(view_rows, "tax_amount"),
            operating_expenses=_sum(view_rows, "operating_expenses"),
        )
    else:
        net_profit = round(revenue - cost, 2)

    return {
        "total_revenue": revenue,
        "total_cost": cost,
        "net_profit": net_profit,
        "order_count": orders,
        "average_order_value": revenue / orders if orders else None,
        "cac": ad_spend / new_customers if ad_spend is not None and new_customers else None,
        "roas": revenue / ad_spend if ad_spend else None,
        "ltv": revenue / len(customers) if customers else None,
    }

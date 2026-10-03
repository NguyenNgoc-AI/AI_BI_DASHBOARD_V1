"""Pure e-commerce KPI calculations."""


def _sum(rows: list[dict], field: str) -> float:
    return sum(float(row.get(field, 0) or 0) for row in rows)


def calculate_kpis(rows: list[dict]) -> dict[str, float | int | None]:
    revenue = _sum(rows, "revenue")
    cost = _sum(rows, "cost")
    orders = len({row["order_id"] for row in rows})
    ad_spend = _sum(rows, "ad_spend") if any("ad_spend" in row for row in rows) else None
    new_customers = _sum(rows, "new_customers") if any("new_customers" in row for row in rows) else None
    customers = {row["customer_id"] for row in rows if row.get("customer_id") not in (None, "")}
    return {
        "total_revenue": revenue,
        "total_cost": cost,
        "net_profit": revenue - cost,
        "order_count": orders,
        "average_order_value": revenue / orders if orders else None,
        "cac": ad_spend / new_customers if ad_spend is not None and new_customers else None,
        "roas": revenue / ad_spend if ad_spend else None,
        "ltv": revenue / len(customers) if customers else None,
    }

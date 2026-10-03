"""Ràng buộc nghiệp vụ tài chính E-commerce."""


def net_profit(revenue: float, cogs: float, marketing_cost: float = 0, platform_cost: float = 0) -> float:
    return revenue - cogs - marketing_cost - platform_cost

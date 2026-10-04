"""
Synthetic Generator Model for E-Commerce Business Intelligence.

Implements a Hierarchical Conditional Synthetic Data Generator that generates realistic,
privacy-preserving e-commerce transactions based on learned statistical schema profiles.
"""

from datetime import datetime, timedelta
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from backend.schema_learning.schema_extractor import LearnedSchemaProfile


class SyntheticGeneratorModel:
    """
    Hierarchical Conditional Synthetic Generator for E-Commerce Data.
    Uses learned univariate distributions, conditional probabilities, and temporal patterns.
    """

    def __init__(
        self,
        profile: Optional[LearnedSchemaProfile] = None,
        profile_path: Optional[Union[str, Path]] = None,
        random_state: int = 42,
    ):
        self.random_state = random_state
        self.rng = np.random.RandomState(random_state)

        if profile is not None:
            self.profile = profile
        elif profile_path is not None:
            self.profile = LearnedSchemaProfile.load(profile_path)
        else:
            default_path = Path("data/generated/learned_seed_profile.json")
            if default_path.exists():
                self.profile = LearnedSchemaProfile.load(default_path)
            else:
                raise ValueError("A valid LearnedSchemaProfile or profile_path must be provided.")

        self._init_distributions()

    def _init_distributions(self) -> None:
        """Pre-computes and caches sampling structures for fast vectorized generation."""
        self.cat_dists = self.profile.distributions.get("categorical", {})
        self.num_dists = self.profile.distributions.get("numerical", {})
        self.temp_dists = self.profile.distributions.get("temporal", {})
        self.hierarchies = self.profile.hierarchies
        self.temp_patterns = self.profile.temporal_patterns

    def _sample_categorical(self, col_name: str, size: int, fallback_values: Optional[List[str]] = None) -> np.ndarray:
        """Samples categorical column values based on learned probabilities."""
        if col_name in self.cat_dists and "categories" in self.cat_dists[col_name]:
            cats = list(self.cat_dists[col_name]["categories"].keys())
            probs = [self.cat_dists[col_name]["categories"][c]["probability"] for c in cats]
            total_p = sum(probs)
            if total_p > 0:
                probs = [p / total_p for p in probs]
                return self.rng.choice(cats, size=size, p=probs)

        if fallback_values:
            return self.rng.choice(fallback_values, size=size)
        return np.array(["Unknown"] * size)

    def _sample_conditional_subcategory(self, categories: np.ndarray) -> np.ndarray:
        """Samples sub_category conditionally on selected category."""
        sub_cats = []
        cat_to_sub = self.hierarchies.get("category_to_subcategory", {})

        for cat in categories:
            if cat in cat_to_sub and cat_to_sub[cat]:
                subs = list(cat_to_sub[cat].keys())
                probs = list(cat_to_sub[cat].values())
                total_p = sum(probs)
                probs = [p / total_p for p in probs]
                sub_cats.append(self.rng.choice(subs, p=probs))
            else:
                sub_cats.append(f"{cat} General")

        return np.array(sub_cats)

    def _sample_conditional_city(self, states: np.ndarray) -> np.ndarray:
        """Samples city conditionally on selected state."""
        cities = []
        state_to_city = self.hierarchies.get("state_to_city", {})

        for st in states:
            if st in state_to_city and state_to_city[st]:
                city_list = list(state_to_city[st].keys())
                probs = list(state_to_city[st].values())
                total_p = sum(probs)
                probs = [p / total_p for p in probs]
                cities.append(self.rng.choice(city_list, p=probs))
            else:
                cities.append("Capital City")

        return np.array(cities)

    def _sample_conditional_payment(self, segments: np.ndarray) -> np.ndarray:
        """Samples payment_type conditionally on customer_segment."""
        payments = []
        seg_to_pay = self.hierarchies.get("segment_to_payment_type", {})
        default_pays = ["credit_card", "debit_card", "boleto", "e_wallet"]

        for seg in segments:
            if seg in seg_to_pay and seg_to_pay[seg]:
                plist = list(seg_to_pay[seg].keys())
                probs = list(seg_to_pay[seg].values())
                total_p = sum(probs)
                probs = [p / total_p for p in probs]
                payments.append(self.rng.choice(plist, p=probs))
            else:
                payments.append(self.rng.choice(default_pays))

        return np.array(payments)

    def _sample_pricing_by_category(self, categories: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Samples unit_price, unit_cost, and margin_rate conditioned on product category."""
        pricing_patterns = self.hierarchies.get("category_pricing_patterns", {})
        
        prices = np.zeros(len(categories))
        costs = np.zeros(len(categories))
        margin_rates = np.zeros(len(categories))

        for idx, cat in enumerate(categories):
            pattern = pricing_patterns.get(cat, {})
            mean_price = pattern.get("mean_unit_price", 85.0)
            std_price = max(5.0, pattern.get("std_unit_price", 35.0))
            mean_margin = pattern.get("mean_margin_rate", 0.45)

            # Sample price using log-normal distribution centered near mean_price
            mu = math.log(max(10.0, mean_price)) - 0.5 * (0.4 ** 2)
            sampled_price = float(np.clip(self.rng.lognormal(mu, 0.45), 4.99, 1500.0))
            
            # Sample margin rate with realistic variation (0.15 to 0.75)
            sampled_margin = float(np.clip(mean_margin + self.rng.normal(0.0, 0.08), 0.15, 0.80))
            sampled_cost = float(np.clip(sampled_price * (1.0 - sampled_margin), 1.0, sampled_price * 0.95))

            prices[idx] = round(sampled_price, 2)
            costs[idx] = round(sampled_cost, 2)
            margin_rates[idx] = round(sampled_margin, 4)

        return prices, costs, margin_rates

    def _generate_timestamps(self, size: int) -> Dict[str, List[str]]:
        """Generates realistic temporal sequence for order lifecycle milestones."""
        temp_col = self.temp_dists.get("order_purchase_timestamp", {})
        min_ts_str = temp_col.get("min_timestamp", "2017-01-01 00:00:00")
        max_ts_str = temp_col.get("max_timestamp", "2018-09-01 00:00:00")

        min_dt = datetime.strptime(min_ts_str, "%Y-%m-%d %H:%M:%S")
        max_dt = datetime.strptime(max_ts_str, "%Y-%m-%d %H:%M:%S")
        total_seconds = max(86400, int((max_dt - min_dt).total_seconds()))

        # Sample random purchase timestamps
        random_offsets = self.rng.uniform(0, total_seconds, size=size)
        purchase_dts = [min_dt + timedelta(seconds=float(offset)) for offset in random_offsets]

        # Duration deltas from learned patterns
        p_app_mean = self.temp_patterns.get("purchase_to_approved_hours", {}).get("mean", 10.5)
        a_car_mean = self.temp_patterns.get("approved_to_carrier_hours", {}).get("mean", 32.0)
        c_del_mean = self.temp_patterns.get("carrier_to_delivered_days", {}).get("mean", 8.5)
        p_est_mean = self.temp_patterns.get("purchase_to_estimated_days", {}).get("mean", 22.0)

        approved_dts = []
        carrier_dts = []
        customer_dts = []
        estimated_dts = []

        for p_dt in purchase_dts:
            # 1. Purchase -> Approved (minutes to hours)
            app_hours = max(0.1, self.rng.exponential(scale=p_app_mean))
            a_dt = p_dt + timedelta(hours=app_hours)
            approved_dts.append(a_dt)

            # 2. Approved -> Carrier (12 to 72 hours)
            car_hours = max(1.0, self.rng.exponential(scale=a_car_mean))
            c_dt = a_dt + timedelta(hours=car_hours)
            carrier_dts.append(c_dt)

            # 3. Carrier -> Customer Delivered (2 to 25 days)
            del_days = max(1.0, self.rng.lognormal(mean=math.log(max(2.0, c_del_mean)), sigma=0.4))
            d_dt = c_dt + timedelta(days=del_days)
            customer_dts.append(d_dt)

            # 4. Estimated Delivery Date
            est_days = max(del_days + 2.0, self.rng.normal(loc=p_est_mean, scale=4.0))
            e_dt = p_dt + timedelta(days=est_days)
            estimated_dts.append(e_dt)

        fmt = "%Y-%m-%d %H:%M:%S"
        return {
            "order_purchase_timestamp": [dt.strftime(fmt) for dt in purchase_dts],
            "order_approved_at": [dt.strftime(fmt) for dt in approved_dts],
            "order_delivered_carrier_date": [dt.strftime(fmt) for dt in carrier_dts],
            "order_delivered_customer_date": [dt.strftime(fmt) for dt in customer_dts],
            "order_estimated_delivery_date": [dt.strftime("%Y-%m-%d 00:00:00") for dt in estimated_dts],
        }

    def generate(self, n_samples: int = 50000) -> pd.DataFrame:
        """
        Generates N synthetic e-commerce transaction records.
        Returns a raw synthetic DataFrame before constraint post-processing.
        """
        # 1. IDs (Unique synthetic tokens)
        sales_ids = [f"SYN_SALE_{i+1:07d}" for i in range(n_samples)]
        order_ids = [f"SYN_ORD_{self.rng.randint(1000000, 9999999)}" for _ in range(n_samples)]
        customer_ids = [f"SYN_CUST_{self.rng.randint(100000, 999999)}" for _ in range(n_samples)]
        product_ids = [f"SYN_SKU_{self.rng.randint(10000, 99999)}" for _ in range(n_samples)]

        # 2. Customer Attributes
        segments = self._sample_categorical(
            "customer_segment", n_samples, ["Consumer", "Corporate", "Home Office"]
        )
        states = self._sample_categorical(
            "state", n_samples, ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "PE", "CE"]
        )
        cities = self._sample_conditional_city(states)
        countries = np.array(["Brazil"] * n_samples)
        zip_codes = self.rng.randint(1000, 99999, size=n_samples).astype(str)

        # 3. Product Catalog Attributes
        categories = self._sample_categorical(
            "category", n_samples, ["Electronics", "Home & Kitchen", "Computers & Accessories", "Beauty & Fashion", "Sports & Outdoors"]
        )
        sub_categories = self._sample_conditional_subcategory(categories)
        unit_prices, unit_costs, margin_rates = self._sample_pricing_by_category(categories)

        # 4. Sales Line Item Metrics
        quantities = self.rng.choice([1, 1, 1, 1, 2, 2, 3, 4], size=n_samples)
        gross_sales = (quantities * unit_prices).round(2)

        # Realistic Discounts (40% orders have discounts between 5% and 20%)
        has_discount = self.rng.rand(n_samples) < 0.38
        discount_rates = self.rng.uniform(0.05, 0.20, size=n_samples)
        discounts = np.where(has_discount, (gross_sales * discount_rates).round(2), 0.0)
        discounts = np.minimum(discounts, gross_sales)

        net_sales = (gross_sales - discounts).round(2)
        cogs = (quantities * unit_costs).round(2)
        gross_profits = (net_sales - cogs).round(2)
        gross_margins = np.where(net_sales > 0, ((gross_profits / net_sales) * 100.0).round(2), 0.0)

        # Freight & Platform Fee
        freight_values = self.rng.uniform(8.50, 45.00, size=n_samples).round(2)
        platform_fee_rates = self.rng.uniform(0.06, 0.12, size=n_samples)
        platform_fees = (net_sales * platform_fee_rates).round(2)

        # 5. Order Milestones & Lifecycle
        order_statuses = self._sample_categorical("order_status", n_samples, ["delivered", "shipped", "invoiced"])
        timestamps = self._generate_timestamps(n_samples)
        payment_types = self._sample_conditional_payment(segments)
        payment_installments = self.rng.choice([1, 1, 1, 2, 3, 4, 6, 10], size=n_samples)
        payment_values = (gross_sales + freight_values).round(2)

        # 6. Financial & Marketing Attributed Metrics
        marketing_channels = self._sample_categorical(
            "marketing_channel", n_samples, ["Facebook Ads", "Google Ads", "TikTok Ads", "Organic Search", "Direct Traffic", "Email Marketing"]
        )
        
        marketing_spends = np.zeros(n_samples)
        for idx, chan in enumerate(marketing_channels):
            if chan in ["Facebook Ads", "Google Ads", "TikTok Ads"]:
                marketing_spends[idx] = round(float(self.rng.uniform(2.50, 8.50)), 2)
            elif chan == "Email Marketing":
                marketing_spends[idx] = round(float(self.rng.uniform(0.30, 1.50)), 2)
            else:
                marketing_spends[idx] = 0.0

        tax_amounts = (net_sales * 0.08).round(2)
        operating_expenses = (net_sales * 0.04 + 1.00).round(2)
        net_profits = (gross_profits - platform_fees - marketing_spends - tax_amounts - operating_expenses).round(2)
        net_margins = np.where(gross_sales > 0, ((net_profits / gross_sales) * 100.0).round(2), 0.0)

        # 7. Funnel Metrics (Impressions -> Clicks -> Conversions)
        impressions = np.where(
            marketing_spends > 0,
            (marketing_spends * self.rng.uniform(150, 300)).astype(int),
            0
        )
        clicks = (impressions * self.rng.uniform(0.02, 0.08)).astype(int)
        conversions = np.minimum(clicks, np.where(clicks > 0, self.rng.randint(1, 4, size=n_samples), 0))

        # Build Consolidated DataFrame
        df_synthetic = pd.DataFrame({
            "sales_id": sales_ids,
            "order_id": order_ids,
            "customer_id": customer_ids,
            "customer_segment": segments,
            "city": cities,
            "state": states,
            "country": countries,
            "zip_code": zip_codes,
            "product_id": product_ids,
            "category": categories,
            "sub_category": sub_categories,
            "quantity": quantities,
            "unit_price": unit_prices,
            "unit_cost": unit_costs,
            "margin_rate": margin_rates,
            "gross_sales": gross_sales,
            "discount_amount": discounts,
            "net_sales": net_sales,
            "cogs": cogs,
            "gross_profit": gross_profits,
            "gross_margin_pct": gross_margins,
            "freight_value": freight_values,
            "platform_fee": platform_fees,
            "order_status": order_statuses,
            "order_purchase_timestamp": timestamps["order_purchase_timestamp"],
            "order_approved_at": timestamps["order_approved_at"],
            "order_delivered_carrier_date": timestamps["order_delivered_carrier_date"],
            "order_delivered_customer_date": timestamps["order_delivered_customer_date"],
            "order_estimated_delivery_date": timestamps["order_estimated_delivery_date"],
            "payment_type": payment_types,
            "payment_installments": payment_installments,
            "payment_value": payment_values,
            "marketing_channel": marketing_channels,
            "marketing_spend": marketing_spends,
            "tax_amount": tax_amounts,
            "operating_expenses": operating_expenses,
            "net_profit": net_profits,
            "net_margin_pct": net_margins,
        })

        return df_synthetic

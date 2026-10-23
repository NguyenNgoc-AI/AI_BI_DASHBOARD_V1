"""
ETL Pipeline: Build Standardized Unified E-Commerce Dataset (Seed & Holdout)
Consolidates raw Olist E-Commerce, Amazon Margins, and Marketing Ad Spend
into standardized, fully consistent Seed Data (70%) and Real Holdout Set (30%).
"""

import os
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

# Mapping Portuguese Olist categories to standard English categories & sub-categories
CATEGORY_MAPPING: Dict[str, Tuple[str, str, float]] = {
    # format: category_name: (Standard Category, Sub-Category, Default Margin Rate)
    "cama_mesa_banho": ("Home & Kitchen", "Bed & Bath", 0.52),
    "moveis_decoracao": ("Home & Kitchen", "Furniture & Decor", 0.48),
    "utilidades_domesticas": ("Home & Kitchen", "Kitchenware", 0.55),
    "esporte_lazer": ("Sports & Outdoors", "Fitness & Recreation", 0.50),
    "beleza_saude": ("Health & Personal Care", "Beauty & Healthcare", 0.62),
    "perfumaria": ("Beauty & Fashion", "Perfumes & Fragrances", 0.65),
    "fashion_bolsas_e_acessorios": ("Beauty & Fashion", "Bags & Accessories", 0.58),
    "fashion_calcados": ("Beauty & Fashion", "Footwear", 0.55),
    "fashion_roupa_feminina": ("Beauty & Fashion", "Women Clothing", 0.60),
    "fashion_roupa_masculina": ("Beauty & Fashion", "Men Clothing", 0.58),
    "informatica_acessorios": ("Computers & Accessories", "Computer Peripherals", 0.42),
    "telefonia": ("Electronics", "Mobile Phones & Accessories", 0.38),
    "relogios_presentes": ("Beauty & Fashion", "Watches & Gifts", 0.60),
    "brinquedos": ("Toys & Games", "Toys & Hobbies", 0.50),
    "bebes": ("Home & Kitchen", "Baby Care", 0.45),
    "automotivo": ("Automotive", "Car Accessories & Parts", 0.45),
    "papelaria": ("Office Products", "Stationery & Office Supplies", 0.55),
    "ferramentas_jardim": ("Home & Kitchen", "Garden Tools", 0.46),
    "pet_shop": ("Health & Personal Care", "Pet Supplies", 0.52),
    "eletronicos": ("Electronics", "Consumer Electronics", 0.40),
    "audio": ("Electronics", "Audio & Headphones", 0.48),
    "livros_interesse_geral": ("Books", "General Interest", 0.40),
    "livros_tecnicos": ("Books", "Technical & Educational", 0.42),
    "consoles_games": ("Electronics", "Gaming & Consoles", 0.35),
    "eletrodomesticos": ("Home & Kitchen", "Major Appliances", 0.38),
    "eletroportateis": ("Home & Kitchen", "Small Appliances", 0.45),
    "malas_e_acessorios": ("Beauty & Fashion", "Luggage & Travel", 0.52),
    "construcao_ferramentas_construcao": ("Home & Kitchen", "Building Hardware", 0.42),
    "alimentos_bebidas": ("Home & Kitchen", "Food & Beverages", 0.35),
    "bebidas": ("Home & Kitchen", "Beverages", 0.38),
    "instrumentos_musicais": ("Electronics", "Musical Instruments", 0.45),
}

DEFAULT_CATEGORY_INFO = ("Home & Kitchen", "General Merchandise", 0.45)

CUSTOMER_SEGMENTS = ["Consumer", "Corporate", "Home Office", "VIP"]
SEGMENT_PROBS = [0.70, 0.18, 0.08, 0.04]

MARKETING_CHANNELS = [
    "Facebook Ads",
    "Google Ads",
    "TikTok Ads",
    "Organic Search",
    "Direct Traffic",
    "Email Marketing",
]
CHANNEL_PROBS = [0.32, 0.28, 0.15, 0.12, 0.08, 0.05]


def run_etl_pipeline(
    raw_dir: Path,
    output_seed_path: Path,
    output_holdout_path: Path,
    sample_size: int = 50000,
    random_state: int = 42,
):
    print("=" * 60)
    print("STARTING UNIFIED E-COMMERCE DATASET ETL PIPELINE")
    print("=" * 60)

    np.random.seed(random_state)

    # 1. Load raw Olist datasets
    olist_dir = raw_dir / "olist_ecommerce"
    print("Loading raw Olist datasets...")
    df_orders = pd.read_csv(olist_dir / "olist_orders_dataset.csv")
    df_items = pd.read_csv(olist_dir / "olist_order_items_dataset.csv")
    df_payments = pd.read_csv(olist_dir / "olist_order_payments_dataset.csv")
    df_products = pd.read_csv(olist_dir / "olist_products_dataset.csv")
    df_customers = pd.read_csv(olist_dir / "olist_customers_dataset.csv")

    print(f"  Raw Orders: {len(df_orders):,}")
    print(f"  Raw Items: {len(df_items):,}")
    print(f"  Raw Payments: {len(df_payments):,}")
    print(f"  Raw Products: {len(df_products):,}")
    print(f"  Raw Customers: {len(df_customers):,}")

    # 2. Aggregate Payments to 1 row per order
    print("Aggregating order payments...")
    df_payments_agg = (
        df_payments.groupby("order_id")
        .agg(
            payment_type=("payment_type", "first"),
            payment_installments=("payment_installments", "max"),
            payment_value=("payment_value", "sum"),
        )
        .reset_index()
    )

    # 3. Process Product Category Mappings
    print("Standardizing product metadata & category margins...")
    product_cat_map = {}
    for _, row in df_products.iterrows():
        p_id = row["product_id"]
        cat_raw = str(row.get("product_category_name", ""))
        if cat_raw in CATEGORY_MAPPING:
            cat, subcat, margin = CATEGORY_MAPPING[cat_raw]
        else:
            cat, subcat, margin = DEFAULT_CATEGORY_INFO
        product_cat_map[p_id] = (cat, subcat, margin)

    # 4. Join Items -> Orders -> Customers -> Payments
    print("Merging relational entities...")
    df = df_items.merge(df_orders, on="order_id", how="inner")
    df = df.merge(df_customers, on="customer_id", how="inner")
    df = df.merge(df_payments_agg, on="order_id", how="left")

    print(f"  Merged transaction item rows: {len(df):,}")

    # Filter out invalid orders without purchase timestamps
    df = df[df["order_purchase_timestamp"].notna()].copy()

    # If dataset is larger than target sample, sample systematically while preserving distribution
    if sample_size and len(df) > sample_size:
        print(f"Sampling {sample_size:,} transaction rows with random_state={random_state}...")
        df = df.sample(n=sample_size, random_state=random_state).reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)

    # 5. Enrich with Synthetic Financial Fields strictly obeying Business Rules
    print("Computing financial metrics and business invariants...")
    num_rows = len(df)

    sales_id = [f"SALE_{i+1:07d}" for i in range(num_rows)]
    customer_segments = np.random.choice(CUSTOMER_SEGMENTS, size=num_rows, p=SEGMENT_PROBS)
    marketing_channels = np.random.choice(MARKETING_CHANNELS, size=num_rows, p=CHANNEL_PROBS)

    categories = []
    sub_categories = []
    unit_prices = []
    unit_costs = []
    margin_rates = []
    quantities = []
    gross_sales_list = []
    discounts = []
    net_sales_list = []
    cogs_list = []
    gross_profits = []
    gross_margins = []
    platform_fees = []
    marketing_spends = []
    tax_amounts = []
    operating_expenses_list = []
    net_profits = []
    net_margins = []

    for idx, row in df.iterrows():
        p_id = row["product_id"]
        cat, subcat, base_margin = product_cat_map.get(p_id, DEFAULT_CATEGORY_INFO)

        # Quantity
        qty = 1  # Base item row in Olist represents 1 item unit
        price = round(float(row["price"]), 2)
        if price <= 0:
            price = 9.99

        # Margin variation ± 5%
        jitter = np.random.uniform(-0.05, 0.05)
        margin_rate = round(float(np.clip(base_margin + jitter, 0.15, 0.85)), 4)
        cost = round(float(price * (1.0 - margin_rate)), 2)
        if cost <= 0:
            cost = round(price * 0.5, 2)

        # Gross sales
        gross = round(float(qty * price), 2)

        # Realistic discount: 60% orders no discount, 40% get 5% to 20% discount
        has_discount = np.random.rand() < 0.40
        if has_discount:
            disc_rate = np.random.uniform(0.05, 0.20)
            disc = round(float(gross * disc_rate), 2)
        else:
            disc = 0.0
        disc = min(disc, gross)

        net_sales = round(float(gross - disc), 2)
        cogs = round(float(qty * cost), 2)
        gross_profit = round(float(net_sales - cogs), 2)
        gross_margin_pct = round(float((gross_profit / net_sales * 100.0) if net_sales > 0 else 0.0), 2)

        # Platform fee (6% to 12% of net sales)
        plat_rate = np.random.uniform(0.06, 0.12)
        plat_fee = round(float(net_sales * plat_rate), 2)

        # Attributed Marketing spend by channel
        chan = marketing_channels[idx]
        if chan in ["Facebook Ads", "Google Ads", "TikTok Ads"]:
            mkt_spend = round(float(np.random.uniform(2.50, 8.00)), 2)
        elif chan == "Email Marketing":
            mkt_spend = round(float(np.random.uniform(0.30, 1.20)), 2)
        else:  # Organic / Direct
            mkt_spend = 0.0

        # Tax (8% VAT/Sales tax)
        tax = round(float(net_sales * 0.08), 2)

        # Allocated Operating Expenses (4% + fixed $1.00)
        opex = round(float(net_sales * 0.04 + 1.00), 2)

        # Net profit = Gross profit - platform_fee - marketing_spend - tax - opex
        net_profit = round(float(gross_profit - plat_fee - mkt_spend - tax - opex), 2)
        net_margin_pct = round(float((net_profit / gross * 100.0) if gross > 0 else 0.0), 2)

        categories.append(cat)
        sub_categories.append(subcat)
        unit_prices.append(price)
        unit_costs.append(cost)
        margin_rates.append(margin_rate)
        quantities.append(qty)
        gross_sales_list.append(gross)
        discounts.append(disc)
        net_sales_list.append(net_sales)
        cogs_list.append(cogs)
        gross_profits.append(gross_profit)
        gross_margins.append(gross_margin_pct)
        platform_fees.append(plat_fee)
        marketing_spends.append(mkt_spend)
        tax_amounts.append(tax)
        operating_expenses_list.append(opex)
        net_profits.append(net_profit)
        net_margins.append(net_margin_pct)

    # Fix payment_value nulls
    default_pay = pd.Series([g + f for g, f in zip(gross_sales_list, df["freight_value"].fillna(0.0))], index=df.index)
    payment_vals = df["payment_value"].fillna(default_pay).round(2).values

    # 6. Format Consolidated DataFrame
    df_clean = pd.DataFrame(
        {
            "sales_id": sales_id,
            "order_id": df["order_id"].values,
            "customer_id": df["customer_id"].values,
            "customer_segment": customer_segments,
            "city": df["customer_city"].fillna("Unknown").values,
            "state": df["customer_state"].fillna("Unknown").values,
            "country": "Brazil",
            "zip_code": df["customer_zip_code_prefix"].fillna(0).astype(int).astype(str).values,
            "product_id": df["product_id"].values,
            "category": categories,
            "sub_category": sub_categories,
            "quantity": quantities,
            "unit_price": unit_prices,
            "unit_cost": unit_costs,
            "margin_rate": margin_rates,
            "gross_sales": gross_sales_list,
            "discount_amount": discounts,
            "net_sales": net_sales_list,
            "cogs": cogs_list,
            "gross_profit": gross_profits,
            "gross_margin_pct": gross_margins,
            "freight_value": df["freight_value"].fillna(0.0).round(2).values,
            "platform_fee": platform_fees,
            "order_status": df["order_status"].fillna("delivered").values,
            "order_purchase_timestamp": df["order_purchase_timestamp"].values,
            "order_approved_at": df["order_approved_at"].values,
            "order_delivered_carrier_date": df["order_delivered_carrier_date"].values,
            "order_delivered_customer_date": df["order_delivered_customer_date"].values,
            "order_estimated_delivery_date": df["order_estimated_delivery_date"].values,
            "payment_type": df["payment_type"].fillna("credit_card").values,
            "payment_installments": df["payment_installments"].fillna(1).astype(int).values,
            "payment_value": payment_vals,
            "marketing_channel": marketing_channels,
            "marketing_spend": marketing_spends,
            "tax_amount": tax_amounts,
            "operating_expenses": operating_expenses_list,
            "net_profit": net_profits,
            "net_margin_pct": net_margins,
        }
    )


    # 7. Split 70% Seed Data and 30% Holdout Test Set
    print("\nSplitting dataset into 70% Seed Data and 30% Holdout Set...")
    total_records = len(df_clean)
    indices = np.arange(total_records)
    np.random.shuffle(indices)

    split_idx = int(total_records * 0.70)
    seed_indices = indices[:split_idx]
    holdout_indices = indices[split_idx:]

    df_seed = df_clean.iloc[seed_indices].reset_index(drop=True)
    df_holdout = df_clean.iloc[holdout_indices].reset_index(drop=True)

    # Save to CSV files
    output_seed_path.parent.mkdir(parents=True, exist_ok=True)
    output_holdout_path.parent.mkdir(parents=True, exist_ok=True)

    df_seed.to_csv(output_seed_path, index=False, encoding="utf-8")
    df_holdout.to_csv(output_holdout_path, index=False, encoding="utf-8")

    print(f"Successfully saved:")
    print(f"  [70%] Seed Dataset:    {output_seed_path} ({len(df_seed):,} rows, {os.path.getsize(output_seed_path) / (1024*1024):.2f} MB)")
    print(f"  [30%] Holdout Dataset: {output_holdout_path} ({len(df_holdout):,} rows, {os.path.getsize(output_holdout_path) / (1024*1024):.2f} MB)")

    return df_seed, df_holdout


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    RAW_DATA_DIR = PROJECT_ROOT / "data" / "sample_dataset" / "raw_sources"
    SEED_OUT = PROJECT_ROOT / "data" / "sample_dataset" / "ecommerce_seed.csv"
    HOLDOUT_OUT = PROJECT_ROOT / "data" / "warehouse" / "real_holdout.csv"

    run_etl_pipeline(
        raw_dir=RAW_DATA_DIR,
        output_seed_path=SEED_OUT,
        output_holdout_path=HOLDOUT_OUT,
        sample_size=50000,
        random_state=42,
    )

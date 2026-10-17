"""
Unit tests for Benchmark Seed Data, Real Holdout Set, and Backend Mock Data (Task 3).
"""

import unittest
import pandas as pd
from pathlib import Path
from semantic.business_rules import BusinessRuleEngine

BASE_DIR = Path(__file__).parent.parent
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"
HOLDOUT_PATH = BASE_DIR / "data" / "warehouse" / "real_holdout.csv"
SYNTHETIC_PATH = BASE_DIR / "data" / "generated" / "synthetic_ecommerce.csv"


class TestBenchmarkData(unittest.TestCase):
    def setUp(self):
        self.engine = BusinessRuleEngine()

    def test_datasets_exist_and_row_counts(self):
        """Verify that all 3 datasets exist with expected volume."""
        self.assertTrue(SEED_PATH.exists(), f"Seed data not found: {SEED_PATH}")
        self.assertTrue(HOLDOUT_PATH.exists(), f"Holdout data not found: {HOLDOUT_PATH}")
        self.assertTrue(SYNTHETIC_PATH.exists(), f"Synthetic data not found: {SYNTHETIC_PATH}")

        seed_df = pd.read_csv(SEED_PATH)
        holdout_df = pd.read_csv(HOLDOUT_PATH)
        synthetic_df = pd.read_csv(SYNTHETIC_PATH)

        self.assertEqual(len(seed_df), 35000, "Seed dataset must contain exactly 35,000 records.")
        self.assertEqual(len(holdout_df), 15000, "Holdout dataset must contain exactly 15,000 records.")
        self.assertEqual(len(synthetic_df), 50000, "Mock Synthetic dataset must contain exactly 50,000 records.")

    def test_schema_uniformity_38_columns(self):
        """Verify all 3 datasets share the exact same 38-column schema."""
        seed_cols = list(pd.read_csv(SEED_PATH, nrows=1).columns)
        holdout_cols = list(pd.read_csv(HOLDOUT_PATH, nrows=1).columns)
        synthetic_cols = list(pd.read_csv(SYNTHETIC_PATH, nrows=1).columns)

        self.assertEqual(len(seed_cols), 38, "Schema must have exactly 38 columns.")
        self.assertEqual(seed_cols, holdout_cols, "Seed and Holdout schemas must match identically.")
        self.assertEqual(seed_cols, synthetic_cols, "Seed and Synthetic schemas must match identically.")

    def test_mock_data_100_percent_rule_compliance(self):
        """Verify that synthetic mock data handed over to Backend has 100% pass rate on hard sales & product constraints."""
        synthetic_df = pd.read_csv(SYNTHETIC_PATH)
        eval_sales = self.engine.evaluate_dataframe(synthetic_df, "sales")
        eval_prod = self.engine.evaluate_dataframe(synthetic_df, "products")

        self.assertEqual(eval_sales["hard_violations"], 0)
        self.assertEqual(eval_sales["pass_rate_pct"], 100.0)
        self.assertEqual(eval_prod["hard_violations"], 0)
        self.assertEqual(eval_prod["pass_rate_pct"], 100.0)

    def test_seed_and_holdout_isolation_no_leakage(self):
        """Verify that Seed Data and Holdout Set are completely isolated with 0 record ID overlap."""
        seed_sales_ids = set(pd.read_csv(SEED_PATH, usecols=["sales_id"])["sales_id"])
        holdout_sales_ids = set(pd.read_csv(HOLDOUT_PATH, usecols=["sales_id"])["sales_id"])

        intersection = seed_sales_ids.intersection(holdout_sales_ids)
        self.assertEqual(len(intersection), 0, f"Found {len(intersection)} leaking IDs between Seed and Holdout!")


if __name__ == "__main__":
    unittest.main()


"""
Unit tests for Task 5: Dynamic Schema Extractor and Constraint Parser / Repair Engine.
Verifies statistical profile learning, conditional probabilities, correlation matrices,
vectorized constraint validation, mathematical auto-repair, and 100k-row performance benchmark.
"""

import time
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from backend.schema_learning.schema_extractor import (
    SchemaExtractor,
    LearnedSchemaProfile,
)
from backend.schema_learning.rule_parser import (
    RuleParser,
    ConstraintEngine,
    ValidationReport,
    ExecutableConstraint,
)

BASE_DIR = Path(__file__).parent.parent
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"
SYNTHETIC_PATH = BASE_DIR / "data" / "generated" / "synthetic_ecommerce.csv"


class TestSchemaLearning(unittest.TestCase):
    def setUp(self):
        self.extractor = SchemaExtractor(dataset_name="test_ecommerce")
        self.engine = ConstraintEngine()

    def test_schema_extractor_profile_and_hierarchies(self):
        """Test extracting full LearnedSchemaProfile, conditional hierarchies, and correlations."""
        self.assertTrue(SEED_PATH.exists(), f"Seed dataset not found: {SEED_PATH}")
        profile = self.extractor.extract(SEED_PATH)

        self.assertIsInstance(profile, LearnedSchemaProfile)
        self.assertEqual(profile.total_records, 35000)
        self.assertEqual(profile.total_columns, 38)

        # Verify hierarchical conditional probabilities
        self.assertIn("category_to_subcategory", profile.hierarchies)
        self.assertIn("state_to_city", profile.hierarchies)
        self.assertIn("category_pricing_patterns", profile.hierarchies)
        self.assertIn("segment_to_payment_type", profile.hierarchies)

        # Check Category -> Subcategory probability sum ~ 1.0
        cat_sub = profile.hierarchies["category_to_subcategory"]
        self.assertGreater(len(cat_sub), 0)
        first_cat = list(cat_sub.keys())[0]
        prob_sum = sum(cat_sub[first_cat].values())
        self.assertAlmostEqual(prob_sum, 1.0, delta=0.05)

        # Verify correlation matrices
        self.assertIn("pearson", profile.correlation_matrices)
        self.assertIn("spearman", profile.correlation_matrices)
        self.assertIn("unit_price", profile.correlation_matrices["pearson"])

    def test_learned_profile_save_and_load_roundtrip(self):
        """Test serializing LearnedSchemaProfile to JSON and reloading with complete fidelity."""
        profile = self.extractor.extract(SEED_PATH)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            profile.save(tmp_path)
            self.assertTrue(tmp_path.exists())

            loaded = LearnedSchemaProfile.load(tmp_path)
            self.assertEqual(loaded.dataset_name, profile.dataset_name)
            self.assertEqual(loaded.total_records, profile.total_records)
            self.assertEqual(loaded.total_columns, profile.total_columns)
            self.assertEqual(len(loaded.column_profiles), len(profile.column_profiles))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_rule_parser_and_declarative_support(self):
        """Test compiling constraints and supporting both BR_* and HR_* / SR_* rule IDs."""
        parser = RuleParser()
        constraints = parser.executable_constraints

        # Check legacy and declarative rule IDs exist
        self.assertIn("BR_SALES_001", constraints)
        self.assertIn("HR_SALES_001", constraints)
        self.assertIn("BR_FIN_001", constraints)
        self.assertIn("HR_FIN_001", constraints)

        self.assertIsInstance(constraints["HR_SALES_001"], ExecutableConstraint)

    def test_constraint_engine_vectorized_validation_and_reporting(self):
        """Test vectorized validation on valid vs corrupted DataFrames."""
        # Intentionally broken DataFrame
        broken_df = pd.DataFrame({
            "quantity": [2, 0, 5, 1],
            "unit_price": [50.0, 20.0, 10.0, -10.0],
            "gross_sales": [999.0, 0.0, 50.0, -10.0],       # Broken math
            "discount_amount": [1500.0, 5.0, 5.0, 0.0],     # Exceeds gross
            "net_sales": [0.0, -5.0, 45.0, 0.0],           # Broken math
            "cogs": [20.0, 0.0, 10.0, 0.0],
            "gross_profit": [80.0, 0.0, 35.0, 0.0],
            "net_profit": [500.0, 0.0, 20.0, 0.0],
        })

        report = self.engine.validate_dataframe(broken_df)
        self.assertIsInstance(report, ValidationReport)
        self.assertLess(report.overall_pass_rate_pct, 100.0)
        self.assertTrue(report.has_blocking_errors)

    def test_constraint_engine_auto_repair_100_percent_validity(self):
        """Test that enforce_constraints mathematically repairs corrupted records to 100% compliance."""
        broken_df = pd.DataFrame({
            "quantity": [2, 0, 5, -3],
            "unit_price": [50.0, 20.0, 10.0, -10.0],
            "unit_cost": [30.0, 15.0, 5.0, -5.0],
            "gross_sales": [999.0, 0.0, 50.0, -10.0],
            "discount_amount": [1500.0, 5.0, 2.0, 0.0],
            "net_sales": [0.0, -5.0, 48.0, 0.0],
            "cogs": [10.0, 0.0, 25.0, 0.0],
            "gross_profit": [0.0, 0.0, 23.0, 0.0],
            "gross_margin_pct": [0.0, 0.0, 50.0, 0.0],
            "marketing_spend": [10.0, -5.0, 2.0, 0.0],
            "platform_fee": [50.0, 2.0, 1.0, 0.0],
            "tax_amount": [5.0, 0.0, 1.0, 0.0],
            "operating_expenses": [5.0, 0.0, 1.0, 0.0],
            "net_profit": [-999.0, 0.0, 100.0, 0.0],
            "net_margin_pct": [0.0, 0.0, 10.0, 0.0],
            "impressions": [100, 50, 200, 10],
            "clicks": [150, 20, 50, 5],                    # Row 0: clicks > impressions
            "conversions": [200, 30, 10, 2],                # Row 0 & 1: conversions > clicks
        })

        repaired_df = self.engine.enforce_constraints(broken_df)

        # Verify mathematical consistency
        self.assertTrue((repaired_df["gross_sales"] == (repaired_df["quantity"] * repaired_df["unit_price"]).round(2)).all())
        self.assertTrue((repaired_df["net_sales"] == (repaired_df["gross_sales"] - repaired_df["discount_amount"]).round(2)).all())
        self.assertTrue((repaired_df["discount_amount"] <= repaired_df["gross_sales"]).all())
        self.assertTrue((repaired_df["clicks"] <= repaired_df["impressions"]).all())
        self.assertTrue((repaired_df["conversions"] <= repaired_df["clicks"]).all())

        # Validate with engine
        report = self.engine.validate_dataframe(repaired_df)
        self.assertEqual(report.overall_pass_rate_pct, 100.0)

    def test_vectorized_performance_100k_rows_benchmark(self):
        """Benchmark test verifying that 100,000 rows can be validated and auto-repaired in < 2.0s."""
        self.assertTrue(SYNTHETIC_PATH.exists(), f"Synthetic data not found: {SYNTHETIC_PATH}")
        base_df = pd.read_csv(SYNTHETIC_PATH)

        # Scale up to exactly 100,000 records
        df_100k = pd.concat([base_df, base_df], ignore_index=True)
        self.assertEqual(len(df_100k), 100000)

        # Intentionally corrupt some fields across all 100,000 rows
        df_100k["gross_sales"] = 999.99
        df_100k["net_profit"] = -100.0

        t_start = time.time()
        repaired_df = self.engine.enforce_constraints(df_100k)
        report = self.engine.validate_dataframe(repaired_df)
        elapsed_sec = time.time() - t_start

        self.assertLess(elapsed_sec, 2.0, f"Processing 100k rows took {elapsed_sec:.3f}s (exceeded 2.0s limit).")
        self.assertEqual(report.overall_pass_rate_pct, 100.0)
        self.assertEqual(len(repaired_df), 100000)


if __name__ == "__main__":
    unittest.main()


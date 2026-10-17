"""
Unit tests for Generic Data Profiler and Quality Checker (Task 4).
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from backend.eda.profiling import GenericDataProfiler
from backend.eda.quality_checker import GenericQualityChecker

BASE_DIR = Path(__file__).parent.parent
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"


class TestProfilingAndQuality(unittest.TestCase):
    def setUp(self):
        self.profiler = GenericDataProfiler(dataset_name="test_data")
        self.checker = GenericQualityChecker(dataset_name="test_data")

    def test_generic_data_profiler_on_sample_df(self):
        """Test profiling arbitrary DataFrames with mixed types."""
        sample_df = pd.DataFrame({
            "order_id": ["ORD_01", "ORD_02", "ORD_03", "ORD_04"],
            "unit_price": [10.0, 20.0, 30.0, 40.0],
            "quantity": [1, 2, 3, 4],
            "category": ["Electronics", "Electronics", "Books", "Books"],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "is_active": [True, True, False, True],
        })

        profile = self.profiler.profile(sample_df)
        self.assertIn("summary", profile)
        self.assertEqual(profile["summary"]["total_rows"], 4)
        self.assertEqual(profile["summary"]["total_columns"], 6)

        # Check numeric stats
        price_stats = profile["columns"]["unit_price"]["stats"]
        self.assertEqual(price_stats["mean"], 25.0)
        self.assertEqual(price_stats["min"], 10.0)
        self.assertEqual(price_stats["max"], 40.0)

        # Check categorical stats
        cat_stats = profile["columns"]["category"]["stats"]
        self.assertEqual(cat_stats["distinct_count"], 2)
        self.assertIn("value_frequencies", cat_stats)

        # Check correlation matrix
        self.assertIn("correlation_matrix", profile)
        self.assertGreater(len(profile["top_correlations"]), 0)

    def test_profiler_save_and_load_profile(self):
        """Test serializing and deserializing LearnedProfile JSON."""
        sample_df = pd.DataFrame({"val": [1, 2, 3, 4, 5]})
        profile = self.profiler.profile(sample_df)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "profile.json"
            self.profiler.save_profile(profile, out_file)
            self.assertTrue(out_file.exists())

            loaded = GenericDataProfiler.load_profile(out_file)
            self.assertEqual(loaded["summary"]["total_rows"], 5)

    def test_quality_checker_clean_and_corrupted_df(self):
        """Test Quality Checker correctly distinguishes between clean and corrupted data."""
        # Clean sales DF
        clean_df = pd.DataFrame({
            "sales_id": ["S1", "S2", "S3"],
            "quantity": [1, 2, 3],
            "unit_price": [10.0, 20.0, 30.0],
            "gross_sales": [10.0, 40.0, 90.0],
            "discount_amount": [0.0, 5.0, 10.0],
            "net_sales": [10.0, 35.0, 80.0],
        })
        audit_clean = self.checker.check_quality(clean_df, primary_key="sales_id")
        self.assertEqual(audit_clean["overall_status"], "PASSED")
        self.assertGreaterEqual(audit_clean["data_quality_score"], 90.0)

        # Corrupted sales DF (nulls, duplicates, broken gross_sales formula)
        corrupted_df = pd.DataFrame({
            "sales_id": ["S1", "S1", None],  # Duplicate PK and null
            "quantity": [1, 2, None],
            "unit_price": [10.0, 20.0, 30.0],
            "gross_sales": [999.0, 40.0, 90.0],  # Math error
            "discount_amount": [0.0, 500.0, 10.0],  # Discount > gross
            "net_sales": [10.0, 35.0, 80.0],
        })
        audit_corrupted = self.checker.check_quality(corrupted_df, primary_key="sales_id")
        self.assertLess(audit_corrupted["data_quality_score"], 90.0)
        self.assertGreater(audit_corrupted["dimensions"]["completeness"]["null_cells"], 0)
        self.assertGreater(audit_corrupted["dimensions"]["uniqueness"]["primary_key_duplicates"], 0)

    def test_profiler_and_checker_on_seed_dataset(self):
        """Test running profiler and quality checker on official seed dataset."""
        if SEED_PATH.exists():
            seed_df = pd.read_csv(SEED_PATH)
            profile = self.profiler.profile(seed_df)
            self.assertEqual(profile["summary"]["total_rows"], 35000)
            self.assertEqual(profile["summary"]["total_columns"], 38)

            audit = self.checker.check_quality(seed_df, primary_key="sales_id")
            self.assertEqual(audit["overall_status"], "PASSED")
            self.assertGreaterEqual(audit["data_quality_score"], 90.0)


if __name__ == "__main__":
    unittest.main()


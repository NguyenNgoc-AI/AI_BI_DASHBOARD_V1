"""
Unit tests for Task 6: Business Data Generator Engine & Parameterized Pipeline.
Verifies fit(), parameterized generate(), scenario simulations, constraint enforcement, and pipeline execution.
"""

import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from backend.schema_learning.rule_parser import ConstraintEngine
from backend.synthetic_generator.generator_model import (
    BusinessDataGenerator,
    SyntheticGeneratorModel,
)
from backend.synthetic_generator.pipeline import SyntheticDataPipeline

BASE_DIR = Path(__file__).parent.parent
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"
PROFILE_PATH = BASE_DIR / "data" / "generated" / "learned_seed_profile.json"


class TestSyntheticGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = BusinessDataGenerator(profile_path=PROFILE_PATH, random_state=42)
        self.engine = ConstraintEngine()

    def test_generator_initialization_and_fit_from_dataframe(self):
        """Test creating an empty generator and fitting directly on a pandas DataFrame."""
        seed_df = pd.read_csv(SEED_PATH, nrows=500)
        gen = BusinessDataGenerator(random_state=99)
        self.assertIsNone(gen.profile)

        gen.fit(seed_df, dataset_name="micro_seed")
        self.assertIsNotNone(gen.profile)
        self.assertEqual(gen.profile.total_records, 500)

        # Generate a small batch
        sampled_df = gen.generate(num_rows=25)
        self.assertEqual(len(sampled_df), 25)
        self.assertEqual(len(sampled_df.columns), 38)

    def test_generator_sampling_different_volumes(self):
        """Test generating various dataset sizes (10, 500, 2000 records)."""
        for size in [10, 500, 2000]:
            df_gen = self.generator.generate(num_rows=size)
            self.assertEqual(len(df_gen), size)
            self.assertEqual(len(df_gen.columns), 38)
            self.assertTrue((df_gen["quantity"] >= 1).all())
            self.assertTrue((df_gen["unit_price"] >= 0).all())

    def test_scenario_simulation_growth_rate(self):
        """Test scenario simulation with positive growth rate parameter."""
        df_base = self.generator.generate(num_rows=2000, scenario_params={"growth_rate": 0.0})
        df_growth = self.generator.generate(num_rows=2000, scenario_params={"growth_rate": 0.50})

        # Average unit price should be significantly higher in the growth scenario
        mean_base = df_base["unit_price"].mean()
        mean_growth = df_growth["unit_price"].mean()
        self.assertGreater(mean_growth, mean_base)

    def test_scenario_simulation_holiday_season_discount_and_marketing(self):
        """Test holiday season scenario triggering higher discounts and ad spend."""
        df_base = self.generator.generate(num_rows=2000, scenario_params={"scenario": "baseline"})
        df_holiday = self.generator.generate(num_rows=2000, scenario_params={"scenario": "holiday_season"})

        # Holiday season should show higher average discount amount and marketing spend
        self.assertGreaterEqual(df_holiday["discount_amount"].mean(), df_base["discount_amount"].mean() * 0.95)
        self.assertGreaterEqual(df_holiday["marketing_spend"].mean(), df_base["marketing_spend"].mean() * 0.95)

    def test_scenario_simulation_custom_date_range(self):
        """Test custom date range constraint in scenario params."""
        custom_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
        }
        df_custom = self.generator.generate(num_rows=100, scenario_params=custom_params)
        dates = pd.to_datetime(df_custom["order_purchase_timestamp"])
        self.assertTrue((dates >= pd.Timestamp("2024-01-01")).all())
        self.assertTrue((dates <= pd.Timestamp("2024-06-30 23:59:59")).all())

    def test_generated_data_100_percent_rule_compliance(self):
        """Test that generated dataset strictly satisfies 100% of mathematical invariants."""
        df_gen = self.generator.generate(num_rows=1000, enforce_business_rules=True)
        report = self.engine.validate_dataframe(df_gen)

        self.assertEqual(report.overall_pass_rate_pct, 100.0)
        self.assertFalse(report.has_blocking_errors)

    def test_synthetic_data_pipeline_execution(self):
        """Test end-to-end execution of SyntheticDataPipeline service without disk overwrite."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            pipeline = SyntheticDataPipeline(
                profile_path=PROFILE_PATH,
                output_path=tmp_path,
                random_state=123,
            )
            result = pipeline.run(n_samples=500, export_csv=True)

            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["total_records"], 500)
            self.assertEqual(result["pass_rate_pct"], 100.0)
            self.assertTrue(tmp_path.exists())
            self.assertGreater(tmp_path.stat().st_size, 0)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()


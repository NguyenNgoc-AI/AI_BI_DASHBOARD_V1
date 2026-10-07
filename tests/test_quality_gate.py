"""
Unit tests for Task 7: Automated Quality Gate & 4-Pillar Validation Engine.
Verifies Validity, Fidelity (KS-Test), Privacy (DCR), and Utility (TSTR vs TRTR) evaluations.
"""

import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from eval.fidelity_eval import FidelityEvaluator, FidelityReport
from eval.privacy_eval import PrivacyEvaluator, PrivacyReport
from eval.utility_eval import UtilityEvaluator, UtilityReport
from backend.synthetic_generator.validator import SyntheticDataQualityGate, QualityGateResult

BASE_DIR = Path(__file__).parent.parent
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"
SYNTHETIC_PATH = BASE_DIR / "data" / "generated" / "synthetic_ecommerce.csv"
HOLDOUT_PATH = BASE_DIR / "data" / "warehouse" / "real_holdout.csv"


class TestQualityGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed_df = pd.read_csv(SEED_PATH)
        cls.syn_df = pd.read_csv(SYNTHETIC_PATH)
        cls.holdout_df = pd.read_csv(HOLDOUT_PATH)

    def test_fidelity_evaluator(self):
        """Test statistical distribution fidelity calculation (KS-Test & TVD)."""
        evaluator = FidelityEvaluator()
        report = evaluator.evaluate(self.seed_df, self.syn_df, sample_size=2000)

        self.assertIsInstance(report, FidelityReport)
        self.assertGreater(report.overall_fidelity_score, 75.0)
        self.assertGreater(report.numerical_fidelity_score, 75.0)
        self.assertGreater(report.categorical_fidelity_score, 75.0)
        self.assertGreater(report.correlation_similarity_score, 70.0)
        self.assertGreaterEqual(report.evaluated_columns_count, 15)

    def test_privacy_evaluator(self):
        """Test privacy evaluation (zero exact match, zero ID leakage, DCR distance)."""
        evaluator = PrivacyEvaluator(sample_size=1000)
        report = evaluator.evaluate(self.seed_df, self.syn_df)

        self.assertIsInstance(report, PrivacyReport)
        self.assertEqual(report.exact_match_count, 0)
        self.assertEqual(report.exact_match_rate_pct, 0.0)
        self.assertEqual(report.id_leakage_count, 0)
        self.assertGreater(report.overall_privacy_score, 80.0)
        self.assertGreater(report.mean_dcr, 0.0)

    def test_utility_evaluator(self):
        """Test machine learning utility retention (TSTR vs TRTR on holdout test set)."""
        evaluator = UtilityEvaluator(sample_size=2000)
        report = evaluator.evaluate(self.seed_df, self.syn_df, self.holdout_df)

        self.assertIsInstance(report, UtilityReport)
        self.assertGreater(report.overall_utility_score, 70.0)
        self.assertIn("net_sales_prediction", report.tasks)
        self.assertIn("customer_segment_prediction", report.tasks)

        # Check retention score between 0 and 100
        for task_res in report.tasks.values():
            self.assertGreaterEqual(task_res.utility_retention_pct, 0.0)
            self.assertLessEqual(task_res.utility_retention_pct, 100.0)

    def test_quality_gate_full_evaluation(self):
        """Test master Quality Gate aggregation and SQI score calculation."""
        gate = SyntheticDataQualityGate(min_pass_sqi=80.0)
        result = gate.evaluate(self.syn_df, self.seed_df, self.holdout_df)

        self.assertIsInstance(result, QualityGateResult)
        self.assertEqual(result.validity_score, 100.0)
        self.assertGreaterEqual(result.synthetic_quality_index, 80.0)
        self.assertEqual(result.gate_status, "PASSED")
        self.assertIn(result.quality_tier, ["Tier A (Excellent)", "Tier B (Good / Production-Ready)"])

    def test_quality_gate_markdown_generation(self):
        """Test rendering Quality Gate Result to Markdown audit report."""
        gate = SyntheticDataQualityGate()
        result = gate.evaluate(self.syn_df, self.seed_df, self.holdout_df)
        md_text = gate.generate_markdown_report(result)

        self.assertIn("SYNTHETIC DATA QUALITY AUDIT", md_text)
        self.assertIn("Validity", md_text)
        self.assertIn("Fidelity", md_text)
        self.assertIn("Privacy", md_text)
        self.assertIn("Utility", md_text)
        self.assertIn("PASSED", md_text)


if __name__ == "__main__":
    unittest.main()


"""
Unit tests for Declarative Business Rules and Rule Engine (Task 2).
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from semantic.business_rules import (
    BusinessRuleEngine,
    RuleSeverity,
    DeclarativeRule,
    calculate_gross_sales,
    calculate_net_sales,
    calculate_gross_profit,
    calculate_net_profit,
    calculate_aov,
    calculate_cac,
    calculate_roas,
    calculate_ltv,
    validate_sales_record,
    validate_product_record,
    validate_order_record,
    validate_financial_record,
)

RULES_FILE = Path(__file__).parent.parent / "semantic" / "rules.json"


class TestBusinessRules(unittest.TestCase):
    def setUp(self):
        self.engine = BusinessRuleEngine(RULES_FILE)

    def test_rules_loading_and_classification(self):
        """Test that rules are loaded and correctly classified into hard and soft constraints."""
        hard_rules = self.engine.get_rules_for_table("sales", constraint_type="hard")
        soft_rules = self.engine.get_rules_for_table("sales", constraint_type="soft")
        
        self.assertGreaterEqual(len(hard_rules), 4)
        self.assertGreaterEqual(len(soft_rules), 1)
        
        rule_ids = [r.rule_id for r in hard_rules]
        self.assertIn("HR_SALES_001", rule_ids)
        self.assertIn("HR_SALES_002", rule_ids)
        self.assertIn("HR_SALES_003", rule_ids)

    def test_record_level_evaluation_valid_and_invalid(self):
        """Test single record validation using the declarative rule engine."""
        # Valid sales record
        valid_sales = {
            "quantity": 2,
            "unit_price": 50.0,
            "gross_sales": 100.0,
            "discount_amount": 10.0,
            "net_sales": 90.0,
            "platform_fee": 5.0,
        }
        res_valid = self.engine.evaluate_record(valid_sales, "sales")
        self.assertTrue(res_valid.is_valid)
        self.assertEqual(len(res_valid.errors), 0)

        # Invalid sales record (gross_sales calculation wrong, discount exceeds gross)
        invalid_sales = {
            "quantity": 2,
            "unit_price": 50.0,
            "gross_sales": 80.0,       # Wrong: should be 100
            "discount_amount": 120.0,   # Wrong: exceeds gross
            "net_sales": 90.0,
            "platform_fee": 5.0,
        }
        res_invalid = self.engine.evaluate_record(invalid_sales, "sales")
        self.assertFalse(res_invalid.is_valid)
        self.assertGreaterEqual(len(res_invalid.errors), 1)

    def test_dataframe_vectorized_evaluation_and_repair(self):
        """Test high-performance DataFrame evaluation and auto-repair."""
        # Create a DataFrame with intentionally broken records
        broken_df = pd.DataFrame({
            "quantity": [2, 0, 5, 10],                     # Row 1 has qty=0 (violation)
            "unit_price": [50.0, 20.0, 10.0, -5.0],        # Row 3 has unit_price < 0
            "gross_sales": [999.0, 0.0, 50.0, -50.0],       # Inconsistent gross_sales
            "discount_amount": [1500.0, 5.0, 5.0, 0.0],     # Discount > gross
            "net_sales": [0.0, -5.0, 45.0, 0.0],           # Inconsistent net_sales
            "platform_fee": [5.0, 2.0, 1.0, 0.0],
        })

        # Evaluate before repair: Should have violations
        eval_before = self.engine.evaluate_dataframe(broken_df, "sales")
        self.assertLess(eval_before["pass_rate_pct"], 100.0)
        self.assertGreater(eval_before["hard_violations"], 0)

        # Auto-Repair DataFrame
        repaired_df = self.engine.repair_dataframe(broken_df, "sales")

        # Evaluate after repair: Must be 100% compliant with Hard Constraints
        eval_after = self.engine.evaluate_dataframe(repaired_df, "sales")
        self.assertEqual(eval_after["hard_violations"], 0)
        self.assertEqual(eval_after["pass_rate_pct"], 100.0)
        
        # Verify repaired mathematical values
        self.assertEqual(repaired_df.loc[0, "gross_sales"], 100.0)
        self.assertEqual(repaired_df.loc[0, "discount_amount"], 100.0) # Clipped to gross_sales
        self.assertEqual(repaired_df.loc[0, "net_sales"], 0.0)
        self.assertEqual(repaired_df.loc[1, "quantity"], 1) # Minimum quantity 1

    def test_financial_metric_formulas(self):
        """Test financial metric helper calculations."""
        self.assertEqual(calculate_gross_sales(3, 25.5), 76.5)
        self.assertEqual(calculate_net_sales(100.0, 15.0), 85.0)
        self.assertEqual(calculate_gross_profit(85.0, 40.0), 45.0)
        self.assertEqual(calculate_net_profit(1000.0, 400.0, 100.0, 50.0, 50.0, 50.0, 100.0), 250.0)
        self.assertEqual(calculate_aov(1000.0, 20), 50.0)
        self.assertEqual(calculate_cac(500.0, 25), 20.0)
        self.assertEqual(calculate_roas(3000.0, 600.0), 5.0)
        self.assertEqual(calculate_ltv(50.0, 4.0, 2.0), 400.0)


if __name__ == "__main__":
    unittest.main()


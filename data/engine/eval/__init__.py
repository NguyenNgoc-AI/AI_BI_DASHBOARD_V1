"""
Evaluation and Benchmarking Package for Synthetic Data.

Exports:
- FidelityEvaluator, FidelityReport (eval/fidelity_eval.py)
- PrivacyEvaluator, PrivacyReport (eval/privacy_eval.py)
- UtilityEvaluator, UtilityReport (eval/utility_eval.py)
"""

from eval.fidelity_eval import ColumnFidelityResult, FidelityEvaluator, FidelityReport
from eval.privacy_eval import PrivacyEvaluator, PrivacyReport
from eval.utility_eval import MLTaskEvaluationResult, UtilityEvaluator, UtilityReport

__all__ = [
    "FidelityEvaluator",
    "FidelityReport",
    "ColumnFidelityResult",
    "PrivacyEvaluator",
    "PrivacyReport",
    "UtilityEvaluator",
    "UtilityReport",
    "MLTaskEvaluationResult",
]

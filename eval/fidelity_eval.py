"""
Fidelity Evaluator for Synthetic Data Quality Gate (Task 7).

Evaluates statistical distribution fidelity between real seed data and synthetic data:
1. Kolmogorov-Smirnov (KS-Test) for continuous numerical variables.
2. Total Variation Distance (TVD) for discrete/categorical variables.
3. Correlation Matrix Alignment (Frobenius similarity of Pearson matrices).
"""

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ColumnFidelityResult:
    """Fidelity metric for a single column."""
    column_name: str
    column_type: str  # 'numerical' or 'categorical'
    test_statistic: float  # KS statistic (0-1) or TVD (0-1)
    p_value: Optional[float]
    fidelity_score: float  # 0 to 100 (100 = identical distribution)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FidelityReport:
    """Consolidated statistical fidelity evaluation report."""
    overall_fidelity_score: float  # 0 to 100
    numerical_fidelity_score: float
    categorical_fidelity_score: float
    correlation_similarity_score: float
    evaluated_columns_count: int
    column_results: Dict[str, ColumnFidelityResult] = field(default_factory=dict)
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary."""
        return {
            "overall_fidelity_score": self.overall_fidelity_score,
            "numerical_fidelity_score": self.numerical_fidelity_score,
            "categorical_fidelity_score": self.categorical_fidelity_score,
            "correlation_similarity_score": self.correlation_similarity_score,
            "evaluated_columns_count": self.evaluated_columns_count,
            "column_results": {k: asdict(v) for k, v in self.column_results.items()},
            "identified_issues": self.identified_issues,
        }


class FidelityEvaluator:
    """
    Evaluates distribution similarity between real and synthetic DataFrames.
    """

    def __init__(self, correlation_weight: float = 0.20):
        self.correlation_weight = correlation_weight

    def evaluate(
        self,
        real_df: pd.DataFrame,
        synthetic_df: pd.DataFrame,
        sample_size: int = 10000,
    ) -> FidelityReport:
        """
        Runs comprehensive statistical distribution checks across all common columns.
        """
        # Subsample for fast, stable computation
        real_sub = real_df.sample(n=min(len(real_df), sample_size), random_state=42)
        syn_sub = synthetic_df.sample(n=min(len(synthetic_df), sample_size), random_state=42)

        column_results: Dict[str, ColumnFidelityResult] = {}
        issues: List[str] = []

        num_scores: List[float] = []
        cat_scores: List[float] = []

        common_cols = [c for c in real_df.columns if c in synthetic_df.columns]
        ignored_cols = {"sales_id", "order_id", "customer_id", "product_id", "zip_code"}

        for col in common_cols:
            if col in ignored_cols or col.endswith("_id") or "timestamp" in col or "date" in col:
                continue

            real_series = real_sub[col].dropna()
            syn_series = syn_sub[col].dropna()

            if real_series.empty or syn_series.empty:
                continue

            # 1. Numerical Variables: 2-Sample KS-Test
            if pd.api.types.is_numeric_dtype(real_series) and pd.api.types.is_numeric_dtype(syn_series):
                real_vals = real_series.values.astype(float)
                syn_vals = syn_series.values.astype(float)

                if np.std(real_vals) < 1e-9 and np.std(syn_vals) < 1e-9:
                    ks_stat = 0.0
                    p_val = 1.0
                else:
                    ks_res = stats.ks_2samp(real_vals, syn_vals)
                    ks_stat = float(ks_res.statistic)
                    p_val = float(ks_res.pvalue)

                # Fidelity: 1.0 - KS statistic
                col_fidelity = round(max(0.0, (1.0 - ks_stat)) * 100.0, 2)
                num_scores.append(col_fidelity)

                if col_fidelity < 70.0:
                    issues.append(f"Low numerical fidelity on '{col}': {col_fidelity}% (KS-stat: {ks_stat:.4f})")

                column_results[col] = ColumnFidelityResult(
                    column_name=col,
                    column_type="numerical",
                    test_statistic=round(ks_stat, 4),
                    p_value=round(p_val, 6) if not math.isnan(p_val) else 0.0,
                    fidelity_score=col_fidelity,
                    details={
                        "real_mean": round(float(np.mean(real_vals)), 2),
                        "syn_mean": round(float(np.mean(syn_vals)), 2),
                        "real_std": round(float(np.std(real_vals)), 2),
                        "syn_std": round(float(np.std(syn_vals)), 2),
                    },
                )

            # 2. Categorical Variables: Total Variation Distance (TVD)
            else:
                real_counts = real_series.astype(str).value_counts(normalize=True)
                syn_counts = syn_series.astype(str).value_counts(normalize=True)

                all_cats = set(real_counts.index).union(set(syn_counts.index))
                tvd = 0.5 * sum(abs(real_counts.get(cat, 0.0) - syn_counts.get(cat, 0.0)) for cat in all_cats)
                tvd = float(min(1.0, max(0.0, tvd)))

                col_fidelity = round((1.0 - tvd) * 100.0, 2)
                cat_scores.append(col_fidelity)

                if col_fidelity < 75.0:
                    issues.append(f"Categorical distribution drift on '{col}': {col_fidelity}% (TVD: {tvd:.4f})")

                column_results[col] = ColumnFidelityResult(
                    column_name=col,
                    column_type="categorical",
                    test_statistic=round(tvd, 4),
                    p_value=None,
                    fidelity_score=col_fidelity,
                    details={"unique_categories": len(all_cats), "tvd": round(tvd, 4)},
                )

        avg_num = round(float(np.mean(num_scores)), 2) if num_scores else 100.0
        avg_cat = round(float(np.mean(cat_scores)), 2) if cat_scores else 100.0

        # 3. Correlation Matrix Alignment
        corr_sim = self._compute_correlation_similarity(real_sub, syn_sub)

        overall_score = round(
            (1.0 - self.correlation_weight) * (0.5 * avg_num + 0.5 * avg_cat)
            + self.correlation_weight * corr_sim,
            2,
        )

        return FidelityReport(
            overall_fidelity_score=overall_score,
            numerical_fidelity_score=avg_num,
            categorical_fidelity_score=avg_cat,
            correlation_similarity_score=corr_sim,
            evaluated_columns_count=len(column_results),
            column_results=column_results,
            identified_issues=issues,
        )

    def _compute_correlation_similarity(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> float:
        """Computes similarity of Pearson correlation matrices between real and synthetic data."""
        num_cols = [
            c for c in real_df.select_dtypes(include=[np.number]).columns
            if c in syn_df.columns and not c.endswith("_id") and c != "zip_code"
        ]
        if len(num_cols) < 2:
            return 100.0

        real_corr = real_df[num_cols].fillna(0).corr(method="pearson").fillna(0).values
        syn_corr = syn_df[num_cols].fillna(0).corr(method="pearson").fillna(0).values

        # Mean Absolute Error of correlations
        diff = np.abs(real_corr - syn_corr)
        mae = float(np.mean(diff))
        # Correlation similarity score: 100 - (MAE * 50)
        score = round(max(0.0, min(100.0, (1.0 - mae) * 100.0)), 2)
        return score


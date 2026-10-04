"""
Fidelity Evaluation Module for Synthetic Data.

Evaluates statistical fidelity between Real (Seed/Holdout) and Synthetic datasets:
1. Two-Sample Kolmogorov-Smirnov (KS) Test for numerical distributions.
2. Total Variation Distance (TVD) for categorical distributions.
3. Correlation Matrix Similarity (Pearson & Spearman cross-correlations).
4. Overall Fidelity Score calculation.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ColumnFidelityResult:
    """Fidelity metric for a single column."""
    column_name: str
    column_type: str  # 'numerical' or 'categorical'
    metric_name: str  # 'ks_test' or 'total_variation_distance'
    distance_statistic: float  # KS stat (0-1) or TVD (0-1), lower is closer
    similarity_score_pct: float  # (1 - distance) * 100, higher is better
    p_value: Optional[float] = None
    status: str = "PASS"  # PASS, WARNING, FAIL


@dataclass
class FidelityReport:
    """Comprehensive statistical fidelity report."""
    overall_fidelity_score: float  # 0 to 100
    numerical_fidelity_score: float
    categorical_fidelity_score: float
    correlation_similarity_score: float
    total_evaluated_columns: int
    passed_columns_count: int
    warning_columns_count: int
    failed_columns_count: int
    column_results: Dict[str, ColumnFidelityResult] = field(default_factory=dict)
    correlation_matrices: Dict[str, Any] = field(default_factory=dict)
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary format."""
        return {
            "overall_fidelity_score": self.overall_fidelity_score,
            "numerical_fidelity_score": self.numerical_fidelity_score,
            "categorical_fidelity_score": self.categorical_fidelity_score,
            "correlation_similarity_score": self.correlation_similarity_score,
            "total_evaluated_columns": self.total_evaluated_columns,
            "passed_columns_count": self.passed_columns_count,
            "warning_columns_count": self.warning_columns_count,
            "failed_columns_count": self.failed_columns_count,
            "column_results": {k: asdict(v) for k, v in self.column_results.items()},
            "identified_issues": self.identified_issues,
        }


class FidelityEvaluator:
    """
    Evaluates statistical similarity and distribution fidelity between real and synthetic data.
    """

    def __init__(
        self,
        ks_fail_threshold: float = 0.25,
        ks_warn_threshold: float = 0.15,
        tvd_fail_threshold: float = 0.30,
        tvd_warn_threshold: float = 0.15,
    ):
        self.ks_fail_threshold = ks_fail_threshold
        self.ks_warn_threshold = ks_warn_threshold
        self.tvd_fail_threshold = tvd_fail_threshold
        self.tvd_warn_threshold = tvd_warn_threshold

    def evaluate_numerical_column(
        self, real_series: pd.Series, syn_series: pd.Series, col_name: str
    ) -> ColumnFidelityResult:
        """Performs two-sample Kolmogorov-Smirnov test."""
        real_clean = pd.to_numeric(real_series, errors="coerce").dropna().values
        syn_clean = pd.to_numeric(syn_series, errors="coerce").dropna().values

        if len(real_clean) == 0 or len(syn_clean) == 0:
            return ColumnFidelityResult(
                column_name=col_name,
                column_type="numerical",
                metric_name="ks_test",
                distance_statistic=1.0,
                similarity_score_pct=0.0,
                status="FAIL",
            )

        # Compute KS Statistic
        ks_stat, p_val = stats.ks_2samp(real_clean, syn_clean)
        ks_stat = float(ks_stat)
        similarity = round(max(0.0, (1.0 - ks_stat) * 100.0), 2)

        status = "PASS"
        if ks_stat > self.ks_fail_threshold:
            status = "FAIL"
        elif ks_stat > self.ks_warn_threshold:
            status = "WARNING"

        return ColumnFidelityResult(
            column_name=col_name,
            column_type="numerical",
            metric_name="ks_test",
            distance_statistic=round(ks_stat, 4),
            similarity_score_pct=similarity,
            p_value=round(float(p_val), 6),
            status=status,
        )

    def evaluate_categorical_column(
        self, real_series: pd.Series, syn_series: pd.Series, col_name: str
    ) -> ColumnFidelityResult:
        """Performs Total Variation Distance (TVD) on category probability distributions."""
        real_counts = real_series.dropna().astype(str).value_counts(normalize=True)
        syn_counts = syn_series.dropna().astype(str).value_counts(normalize=True)

        all_cats = set(real_counts.index).union(set(syn_counts.index))
        if not all_cats:
            return ColumnFidelityResult(
                column_name=col_name,
                column_type="categorical",
                metric_name="total_variation_distance",
                distance_statistic=1.0,
                similarity_score_pct=0.0,
                status="FAIL",
            )

        # TVD = 0.5 * sum(|P(x) - Q(x)|)
        tvd = 0.5 * sum(abs(real_counts.get(c, 0.0) - syn_counts.get(c, 0.0)) for c in all_cats)
        tvd = float(tvd)
        similarity = round(max(0.0, (1.0 - tvd) * 100.0), 2)

        status = "PASS"
        if tvd > self.tvd_fail_threshold:
            status = "FAIL"
        elif tvd > self.tvd_warn_threshold:
            status = "WARNING"

        return ColumnFidelityResult(
            column_name=col_name,
            column_type="categorical",
            metric_name="total_variation_distance",
            distance_statistic=round(tvd, 4),
            similarity_score_pct=similarity,
            status=status,
        )

    def evaluate_correlation_similarity(
        self, real_df: pd.DataFrame, syn_df: pd.DataFrame, num_cols: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluates Pearson correlation matrix similarity between real and synthetic data.
        Returns correlation similarity score (0-100) and matrix differences.
        """
        valid_cols = [c for c in num_cols if c in real_df.columns and c in syn_df.columns]
        if len(valid_cols) < 2:
            return 100.0, {}

        real_corr = real_df[valid_cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson").fillna(0).values
        syn_corr = syn_df[valid_cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson").fillna(0).values

        # Mean Absolute Error across upper triangle of correlation matrices
        triu_idx = np.triu_indices_from(real_corr, k=1)
        if len(triu_idx[0]) == 0:
            return 100.0, {}

        real_triu = real_corr[triu_idx]
        syn_triu = syn_corr[triu_idx]

        corr_mae = float(np.mean(np.abs(real_triu - syn_triu)))
        # Similarity score: 100 * (1 - MAE / 2.0) since corr range delta is at most 2.0
        corr_sim = round(max(0.0, (1.0 - (corr_mae / 2.0)) * 100.0), 2)

        return corr_sim, {
            "evaluated_features_count": len(valid_cols),
            "correlation_mae": round(corr_mae, 4),
            "max_correlation_difference": round(float(np.max(np.abs(real_triu - syn_triu))), 4),
        }

    def evaluate(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> FidelityReport:
        """
        Performs full fidelity evaluation across all shared columns.
        """
        common_cols = [c for c in real_df.columns if c in syn_df.columns]
        ignore_cols = ["sales_id", "order_id", "customer_id", "product_id", "zip_code"]

        column_results: Dict[str, ColumnFidelityResult] = {}
        num_scores = []
        cat_scores = []
        issues: List[str] = []

        num_cols = []
        for col in common_cols:
            if col in ignore_cols or "id" in col.lower():
                continue

            real_series = real_df[col]
            syn_series = syn_df[col]

            # Check if numerical
            is_numeric = pd.api.types.is_numeric_dtype(real_series) and pd.api.types.is_numeric_dtype(syn_series)
            if is_numeric:
                num_cols.append(col)
                res = self.evaluate_numerical_column(real_series, syn_series, col)
                column_results[col] = res
                num_scores.append(res.similarity_score_pct)
                if res.status == "FAIL":
                    issues.append(f"Numerical distribution divergence on '{col}': KS-stat={res.distance_statistic} (Similarity: {res.similarity_score_pct}%).")
                elif res.status == "WARNING":
                    issues.append(f"Minor distribution shift on '{col}': KS-stat={res.distance_statistic}.")
            else:
                # Treat as categorical / discrete (skip all datetime/timestamp/time/at columns)
                if any(k in col.lower() for k in ["date", "timestamp", "time", "_at", "created_at"]):
                    continue
                res = self.evaluate_categorical_column(real_series, syn_series, col)
                column_results[col] = res
                cat_scores.append(res.similarity_score_pct)
                if res.status == "FAIL":
                    issues.append(f"Categorical frequency mismatch on '{col}': TVD={res.distance_statistic} (Similarity: {res.similarity_score_pct}%).")

        corr_sim, corr_details = self.evaluate_correlation_similarity(real_df, syn_df, num_cols)
        if corr_details.get("correlation_mae", 0.0) > 0.25:
            issues.append(f"Correlation matrix divergence: Mean Absolute Error = {corr_details['correlation_mae']}.")

        avg_num = round(float(np.mean(num_scores)), 2) if num_scores else 100.0
        avg_cat = round(float(np.mean(cat_scores)), 2) if cat_scores else 100.0

        # Weighted Overall Fidelity Score (40% Numerical, 30% Categorical, 30% Correlation)
        overall_fidelity = round(0.40 * avg_num + 0.30 * avg_cat + 0.30 * corr_sim, 2)

        pass_cnt = sum(1 for r in column_results.values() if r.status == "PASS")
        warn_cnt = sum(1 for r in column_results.values() if r.status == "WARNING")
        fail_cnt = sum(1 for r in column_results.values() if r.status == "FAIL")

        return FidelityReport(
            overall_fidelity_score=overall_fidelity,
            numerical_fidelity_score=avg_num,
            categorical_fidelity_score=avg_cat,
            correlation_similarity_score=corr_sim,
            total_evaluated_columns=len(column_results),
            passed_columns_count=pass_cnt,
            warning_columns_count=warn_cnt,
            failed_columns_count=fail_cnt,
            column_results=column_results,
            correlation_matrices=corr_details,
            identified_issues=issues,
        )

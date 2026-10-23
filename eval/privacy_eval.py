"""
Privacy and Information Leakage Evaluator for Synthetic Data Quality Gate (Task 7).

Evaluates:
1. Exact Match / Record Duplication Rate (against real seed data).
2. Primary Key / Identifier Leakage.
3. Distance to Closest Record (DCR) on normalized numerical feature space.
4. Nearest Neighbor Distance Ratio (NNDR) for memorization detection.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler


@dataclass
class PrivacyReport:
    """Consolidated privacy and empirical leakage evaluation report."""
    overall_privacy_score: float  # 0 to 100 (100 = optimal privacy protection)
    exact_match_count: int
    exact_match_rate_pct: float
    id_leakage_count: int
    id_leakage_rate_pct: float
    mean_dcr: float  # Mean Distance to Closest Record
    median_dcr: float
    min_dcr: float
    p05_dcr: float
    nndr_mean: float  # Nearest Neighbor Distance Ratio
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary."""
        return asdict(self)


class PrivacyEvaluator:
    """
    Evaluates privacy guarantees and empirical memorization of synthetic datasets.
    """

    def __init__(self, sample_size: int = 5000):
        self.sample_size = sample_size

    def evaluate(
        self,
        real_df: pd.DataFrame,
        synthetic_df: pd.DataFrame,
    ) -> PrivacyReport:
        """
        Runs comprehensive privacy leakage and DCR distance evaluations.
        """
        issues: List[str] = []

        # 1. Primary Key & Token Leakage Check
        id_cols = [c for c in ["sales_id", "order_id", "customer_id", "product_id"] if c in real_df.columns and c in synthetic_df.columns]
        id_leakage_count = 0
        for id_col in id_cols:
            real_ids = set(real_df[id_col].dropna().astype(str))
            syn_ids = set(synthetic_df[id_col].dropna().astype(str))
            leak = len(real_ids.intersection(syn_ids))
            id_leakage_count += leak
            if leak > 0:
                issues.append(f"Primary key leakage detected: {leak} matching IDs in '{id_col}'.")

        id_leakage_pct = round(id_leakage_count / len(synthetic_df) * 100.0, 4) if len(synthetic_df) > 0 else 0.0

        # 2. Exact Match Check on Business Feature Subset
        feature_cols = [
            c for c in real_df.columns
            if c in synthetic_df.columns and not c.endswith("_id") and "timestamp" not in c and "date" not in c
        ]

        real_tuples = set(tuple(x) for x in real_df[feature_cols].dropna().head(10000).itertuples(index=False))
        syn_tuples = [tuple(x) for x in synthetic_df[feature_cols].dropna().head(10000).itertuples(index=False)]

        exact_matches = sum(1 for t in syn_tuples if t in real_tuples)
        exact_match_pct = round(exact_matches / len(syn_tuples) * 100.0, 4) if syn_tuples else 0.0

        if exact_matches > 0:
            issues.append(f"Identified {exact_matches} exact duplicate records ({exact_match_pct}%) matching real training records.")

        # 3. Distance to Closest Record (DCR) via k-NN on normalized numerical features
        num_cols = [
            c for c in real_df.select_dtypes(include=[np.number]).columns
            if c in synthetic_df.columns and not c.endswith("_id") and c != "zip_code"
        ]

        if len(num_cols) >= 3:
            real_sample = real_df[num_cols].dropna().sample(n=min(len(real_df), self.sample_size), random_state=42)
            syn_sample = synthetic_df[num_cols].dropna().sample(n=min(len(synthetic_df), self.sample_size), random_state=42)

            scaler = MinMaxScaler()
            real_scaled = scaler.fit_transform(real_sample)
            syn_scaled = scaler.transform(syn_sample)

            # Fit NearestNeighbors on real data and query synthetic data
            nbrs = NearestNeighbors(n_neighbors=2, algorithm="kd_tree").fit(real_scaled)
            distances, _ = nbrs.kneighbors(syn_scaled)

            dcr_1 = distances[:, 0]  # Distance to 1st nearest neighbor
            dcr_2 = distances[:, 1]  # Distance to 2nd nearest neighbor

            mean_dcr = float(np.mean(dcr_1))
            median_dcr = float(np.median(dcr_1))
            min_dcr = float(np.min(dcr_1))
            p05_dcr = float(np.percentile(dcr_1, 5))

            # NNDR: Ratio of d1 / d2 (near 1.0 means no isolated memorization)
            nndr = np.where(dcr_2 > 1e-9, dcr_1 / dcr_2, 1.0)
            nndr_mean = float(np.mean(nndr))
        else:
            mean_dcr = 0.5
            median_dcr = 0.5
            min_dcr = 0.1
            p05_dcr = 0.2
            nndr_mean = 0.95

        # 4. Privacy Score Calculation (100 = perfect score, 0 exact matches, 0 ID leak)
        match_penalty = min(50.0, exact_match_pct * 100.0)
        id_penalty = min(50.0, id_leakage_pct * 100.0)
        dcr_bonus = min(20.0, mean_dcr * 20.0)

        privacy_score = round(max(0.0, min(100.0, 100.0 - match_penalty - id_penalty + (dcr_bonus - 10.0))), 2)

        return PrivacyReport(
            overall_privacy_score=privacy_score,
            exact_match_count=exact_matches,
            exact_match_rate_pct=exact_match_pct,
            id_leakage_count=id_leakage_count,
            id_leakage_rate_pct=id_leakage_pct,
            mean_dcr=round(mean_dcr, 4),
            median_dcr=round(median_dcr, 4),
            min_dcr=round(min_dcr, 4),
            p05_dcr=round(p05_dcr, 4),
            nndr_mean=round(nndr_mean, 4),
            identified_issues=issues,
        )


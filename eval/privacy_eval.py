"""
Privacy Evaluation Module for Synthetic Data.

Evaluates data privacy risks, identity leakage, and memorization:
1. Exact Record Match Rate against Real Seed and Holdout datasets.
2. Identifier & Quasi-Identifier Collision / Leakage Detection.
3. Distance to Closest Record (DCR) analysis using normalized Euclidean distance.
4. Overall Privacy Score & Risk Assessment.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler


@dataclass
class PrivacyReport:
    """Comprehensive data privacy and leakage evaluation report."""
    overall_privacy_score: float  # 0 to 100, higher is safer
    exact_match_count: int
    exact_match_rate_pct: float
    real_id_leak_count: int
    quasi_identifier_collision_count: int
    dcr_5th_percentile: float  # Distance to Closest Record (5th percentile)
    dcr_median: float
    dcr_min: float
    is_memorization_detected: bool
    privacy_risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    details: Dict[str, Any] = field(default_factory=dict)
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts privacy report to dictionary format."""
        return {
            "overall_privacy_score": self.overall_privacy_score,
            "exact_match_count": self.exact_match_count,
            "exact_match_rate_pct": self.exact_match_rate_pct,
            "real_id_leak_count": self.real_id_leak_count,
            "quasi_identifier_collision_count": self.quasi_identifier_collision_count,
            "dcr_5th_percentile": self.dcr_5th_percentile,
            "dcr_median": self.dcr_median,
            "dcr_min": self.dcr_min,
            "is_memorization_detected": self.is_memorization_detected,
            "privacy_risk_level": self.privacy_risk_level,
            "details": self.details,
            "identified_issues": self.identified_issues,
        }


class PrivacyEvaluator:
    """
    Evaluates privacy guarantees of synthetic datasets against real training seed and holdout data.
    """

    def __init__(
        self,
        dcr_sample_size: int = 2000,
        dcr_memorization_threshold: float = 0.01,
        random_state: int = 42,
    ):
        self.dcr_sample_size = dcr_sample_size
        self.dcr_memorization_threshold = dcr_memorization_threshold
        self.random_state = random_state

    def check_exact_matches(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> Tuple[int, float]:
        """
        Checks for exact full-row duplicate records between real and synthetic data.
        """
        eval_cols = [c for c in real_df.columns if c in syn_df.columns and not c.endswith("_id")]
        if not eval_cols:
            return 0, 0.0

        real_tuples = set(tuple(x) for x in real_df[eval_cols].astype(str).values)
        syn_tuples = [tuple(x) for x in syn_df[eval_cols].astype(str).values]

        exact_matches = sum(1 for t in syn_tuples if t in real_tuples)
        match_rate = round(float(exact_matches / len(syn_df) * 100.0), 4) if len(syn_df) > 0 else 0.0

        return exact_matches, match_rate

    def check_identifier_leaks(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> int:
        """
        Checks if real primary key identifier strings (e.g. real customer_id, order_id) appear in synthetic data.
        """
        id_cols = [c for c in ["customer_id", "order_id", "product_id", "sales_id"] if c in real_df.columns and c in syn_df.columns]
        leaks = 0

        for col in id_cols:
            real_ids = set(real_df[col].dropna().astype(str).unique())
            syn_ids = set(syn_df[col].dropna().astype(str).unique())
            overlap = len(real_ids.intersection(syn_ids))
            leaks += overlap

        return leaks

    def check_quasi_identifier_collisions(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> int:
        """
        Checks for collision across key quasi-identifiers: [city, state, category, payment_value, quantity].
        """
        qi_cols = [c for c in ["city", "state", "category", "payment_value", "quantity"] if c in real_df.columns and c in syn_df.columns]
        if len(qi_cols) < 3:
            return 0

        real_qi = set(tuple(x) for x in real_df[qi_cols].astype(str).values)
        syn_qi = [tuple(x) for x in syn_df[qi_cols].astype(str).values]

        collisions = sum(1 for t in syn_qi if t in real_qi)
        return collisions

    def compute_distance_to_closest_record(
        self, real_df: pd.DataFrame, syn_df: pd.DataFrame
    ) -> Tuple[float, float, float, bool]:
        """
        Computes Distance to Closest Record (DCR) on scaled numerical features using Euclidean metric.
        Returns: (dcr_5th_percentile, dcr_median, dcr_min, is_memorization_detected).
        """
        num_cols = real_df.select_dtypes(include=[np.number]).columns.intersection(
            syn_df.select_dtypes(include=[np.number]).columns
        ).tolist()

        # Exclude synthetic index/ID columns if numeric
        num_cols = [c for c in num_cols if "id" not in c.lower()]
        if len(num_cols) < 2:
            return 1.0, 1.0, 1.0, False

        scaler = MinMaxScaler()
        real_clean = real_df[num_cols].dropna()
        syn_clean = syn_df[num_cols].dropna()

        if len(real_clean) == 0 or len(syn_clean) == 0:
            return 1.0, 1.0, 1.0, False

        # Fit scaler on real data and transform both
        scaler.fit(real_clean)
        real_scaled = scaler.transform(real_clean)
        syn_scaled = scaler.transform(syn_clean)

        # Sample synthetic records if dataset is large for computational efficiency
        sample_size = min(self.dcr_sample_size, len(syn_scaled))
        rng = np.random.RandomState(self.random_state)
        sample_indices = rng.choice(len(syn_scaled), size=sample_size, replace=False)
        syn_sample = syn_scaled[sample_indices]

        # Nearest neighbor query in real data
        nn = NearestNeighbors(n_neighbors=1, metric="euclidean", algorithm="auto")
        nn.fit(real_scaled)
        distances, _ = nn.kneighbors(syn_sample)
        distances = distances.flatten()

        dcr_min = float(np.min(distances))
        dcr_p05 = float(np.percentile(distances, 5))
        dcr_median = float(np.median(distances))

        is_memorization = bool(dcr_p05 < self.dcr_memorization_threshold)

        return round(dcr_p05, 4), round(dcr_median, 4), round(dcr_min, 4), is_memorization

    def evaluate(self, real_df: pd.DataFrame, syn_df: pd.DataFrame) -> PrivacyReport:
        """
        Executes full privacy evaluation suite.
        """
        exact_matches, exact_rate = self.check_exact_matches(real_df, syn_df)
        real_id_leaks = self.check_identifier_leaks(real_df, syn_df)
        qi_collisions = self.check_quasi_identifier_collisions(real_df, syn_df)
        dcr_p05, dcr_med, dcr_min, is_memo = self.compute_distance_to_closest_record(real_df, syn_df)

        issues: List[str] = []
        privacy_penalty = 0.0

        if exact_matches > 0:
            privacy_penalty += min(40.0, exact_matches * 5.0)
            issues.append(f"Exact record duplicate risk: {exact_matches} rows ({exact_rate}%) match real records exactly.")

        if real_id_leaks > 0:
            privacy_penalty += min(30.0, real_id_leaks * 10.0)
            issues.append(f"Identity disclosure risk: {real_id_leaks} real identifier strings found in synthetic data.")

        if is_memo:
            privacy_penalty += 30.0
            issues.append(f"Potential memorization detected: DCR 5th percentile ({dcr_p05}) < threshold ({self.dcr_memorization_threshold}).")

        overall_privacy = round(max(0.0, 100.0 - privacy_penalty), 2)

        if overall_privacy >= 90.0:
            risk_level = "LOW"
        elif overall_privacy >= 75.0:
            risk_level = "MEDIUM"
        elif overall_privacy >= 50.0:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return PrivacyReport(
            overall_privacy_score=overall_privacy,
            exact_match_count=exact_matches,
            exact_match_rate_pct=exact_rate,
            real_id_leak_count=real_id_leaks,
            quasi_identifier_collision_count=qi_collisions,
            dcr_5th_percentile=dcr_p05,
            dcr_median=dcr_med,
            dcr_min=dcr_min,
            is_memorization_detected=is_memo,
            privacy_risk_level=risk_level,
            details={
                "dcr_sample_size": self.dcr_sample_size,
                "dcr_memorization_threshold": self.dcr_memorization_threshold,
            },
            identified_issues=issues,
        )

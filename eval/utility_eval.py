"""
Machine Learning Utility Evaluator (TSTR vs TRTR) for Synthetic Data Quality Gate (Task 7).

Evaluates whether machine learning models trained on synthetic data perform comparably
to models trained on real data when tested on a held-out real evaluation dataset:
1. TSTR (Train on Synthetic, Test on Real Holdout).
2. TRTR (Train on Real Seed, Test on Real Holdout).
3. Utility Retention Ratio = (TSTR_Score / TRTR_Score) * 100.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import f1_score, r2_score, mean_absolute_error, accuracy_score
from sklearn.preprocessing import StandardScaler


@dataclass
class MLTaskEvaluationResult:
    """Evaluation metrics for a single downstream machine learning task."""
    task_name: str
    task_type: str  # 'regression' or 'classification'
    target_column: str
    metric_name: str  # 'r2', 'f1_weighted', 'accuracy'
    trtr_score: float  # Baseline model trained on real seed data
    tstr_score: float  # Model trained on synthetic data
    utility_retention_pct: float  # (tstr / trtr) * 100
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UtilityReport:
    """Consolidated downstream machine learning utility report."""
    overall_utility_score: float  # Average retention percentage (0 to 100)
    regression_utility_score: float
    classification_utility_score: float
    tasks: Dict[str, MLTaskEvaluationResult] = field(default_factory=dict)
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to dictionary."""
        return {
            "overall_utility_score": self.overall_utility_score,
            "regression_utility_score": self.regression_utility_score,
            "classification_utility_score": self.classification_utility_score,
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "identified_issues": self.identified_issues,
        }


class UtilityEvaluator:
    """
    Evaluates empirical downstream machine learning utility using the TSTR paradigm.
    """

    def __init__(self, sample_size: int = 10000):
        self.sample_size = sample_size

    def evaluate(
        self,
        real_train_df: pd.DataFrame,
        synthetic_train_df: pd.DataFrame,
        real_holdout_df: pd.DataFrame,
    ) -> UtilityReport:
        """
        Runs TSTR and TRTR benchmark models and measures performance retention on holdout set.
        """
        issues: List[str] = []
        tasks: Dict[str, MLTaskEvaluationResult] = {}

        # 1. Regression Task: Predicting 'net_sales'
        reg_features = [
            c for c in ["quantity", "unit_price", "unit_cost", "freight_value", "platform_fee"]
            if c in real_train_df.columns and c in synthetic_train_df.columns and c in real_holdout_df.columns
        ]

        if "net_sales" in real_train_df.columns and len(reg_features) >= 3:
            reg_res = self._evaluate_regression_task(
                real_train_df, synthetic_train_df, real_holdout_df, reg_features, target_col="net_sales"
            )
            tasks["net_sales_prediction"] = reg_res
            if reg_res.utility_retention_pct < 75.0:
                issues.append(f"Low regression utility on '{reg_res.target_column}': {reg_res.utility_retention_pct:.2f}% retention.")

        # 2. Classification Task: Predicting 'customer_segment'
        clf_features = [
            c for c in ["gross_sales", "unit_price", "freight_value", "payment_value"]
            if c in real_train_df.columns and c in synthetic_train_df.columns and c in real_holdout_df.columns
        ]

        if "customer_segment" in real_train_df.columns and len(clf_features) >= 2:
            clf_res = self._evaluate_classification_task(
                real_train_df, synthetic_train_df, real_holdout_df, clf_features, target_col="customer_segment"
            )
            tasks["customer_segment_prediction"] = clf_res
            if clf_res.utility_retention_pct < 70.0:
                issues.append(f"Low classification utility on '{clf_res.target_column}': {clf_res.utility_retention_pct:.2f}% retention.")

        # Compute overall utility score
        retentions = [t.utility_retention_pct for t in tasks.values()]
        overall_score = round(float(np.mean(retentions)), 2) if retentions else 100.0

        reg_scores = [t.utility_retention_pct for t in tasks.values() if t.task_type == "regression"]
        clf_scores = [t.utility_retention_pct for t in tasks.values() if t.task_type == "classification"]

        avg_reg = round(float(np.mean(reg_scores)), 2) if reg_scores else 100.0
        avg_clf = round(float(np.mean(clf_scores)), 2) if clf_scores else 100.0

        return UtilityReport(
            overall_utility_score=overall_score,
            regression_utility_score=avg_reg,
            classification_utility_score=avg_clf,
            tasks=tasks,
            identified_issues=issues,
        )

    def _evaluate_regression_task(
        self,
        real_train: pd.DataFrame,
        syn_train: pd.DataFrame,
        real_test: pd.DataFrame,
        features: List[str],
        target_col: str,
    ) -> MLTaskEvaluationResult:
        """Trains Ridge regression on real vs synthetic and evaluates on real test set."""
        X_real = real_train[features].dropna().head(self.sample_size)
        y_real = real_train.loc[X_real.index, target_col].values

        X_syn = syn_train[features].dropna().head(self.sample_size)
        y_syn = syn_train.loc[X_syn.index, target_col].values

        X_test = real_test[features].dropna().head(self.sample_size)
        y_test = real_test.loc[X_test.index, target_col].values

        scaler = StandardScaler()
        X_real_scaled = scaler.fit_transform(X_real)
        X_test_scaled = scaler.transform(X_test)

        scaler_syn = StandardScaler()
        X_syn_scaled = scaler_syn.fit_transform(X_syn)
        X_test_syn_scaled = scaler_syn.transform(X_test)

        # 1. TRTR Model (Baseline)
        model_trtr = Ridge(alpha=1.0)
        model_trtr.fit(X_real_scaled, y_real)
        preds_trtr = model_trtr.predict(X_test_scaled)
        r2_trtr = max(0.01, float(r2_score(y_test, preds_trtr)))

        # 2. TSTR Model
        model_tstr = Ridge(alpha=1.0)
        model_tstr.fit(X_syn_scaled, y_syn)
        preds_tstr = model_tstr.predict(X_test_syn_scaled)
        r2_tstr = max(0.0, float(r2_score(y_test, preds_tstr)))

        # Retention
        retention = round(min(100.0, (r2_tstr / r2_trtr) * 100.0), 2)

        return MLTaskEvaluationResult(
            task_name="Net Sales Regression",
            task_type="regression",
            target_column=target_col,
            metric_name="r2_score",
            trtr_score=round(r2_trtr, 4),
            tstr_score=round(r2_tstr, 4),
            utility_retention_pct=retention,
            details={
                "mae_trtr": round(float(mean_absolute_error(y_test, preds_trtr)), 2),
                "mae_tstr": round(float(mean_absolute_error(y_test, preds_tstr)), 2),
            },
        )

    def _evaluate_classification_task(
        self,
        real_train: pd.DataFrame,
        syn_train: pd.DataFrame,
        real_test: pd.DataFrame,
        features: List[str],
        target_col: str,
    ) -> MLTaskEvaluationResult:
        """Trains Logistic Regression on real vs synthetic and evaluates weighted F1 on real test."""
        X_real = real_train[features].dropna().head(self.sample_size)
        y_real = real_train.loc[X_real.index, target_col].astype(str).values

        X_syn = syn_train[features].dropna().head(self.sample_size)
        y_syn = syn_train.loc[X_syn.index, target_col].astype(str).values

        X_test = real_test[features].dropna().head(self.sample_size)
        y_test = real_test.loc[X_test.index, target_col].astype(str).values

        scaler = StandardScaler()
        X_real_scaled = scaler.fit_transform(X_real)
        X_test_scaled = scaler.transform(X_test)

        scaler_syn = StandardScaler()
        X_syn_scaled = scaler_syn.fit_transform(X_syn)
        X_test_syn_scaled = scaler_syn.transform(X_test)

        # 1. TRTR Model (Baseline)
        model_trtr = LogisticRegression(max_iter=300, random_state=42)
        model_trtr.fit(X_real_scaled, y_real)
        preds_trtr = model_trtr.predict(X_test_scaled)
        f1_trtr = max(0.01, float(f1_score(y_test, preds_trtr, average="weighted", zero_division=0)))

        # 2. TSTR Model
        model_tstr = LogisticRegression(max_iter=300, random_state=42)
        model_tstr.fit(X_syn_scaled, y_syn)
        preds_tstr = model_tstr.predict(X_test_syn_scaled)
        f1_tstr = max(0.0, float(f1_score(y_test, preds_tstr, average="weighted", zero_division=0)))

        retention = round(min(100.0, (f1_tstr / f1_trtr) * 100.0), 2)

        return MLTaskEvaluationResult(
            task_name="Customer Segment Classification",
            task_type="classification",
            target_column=target_col,
            metric_name="weighted_f1_score",
            trtr_score=round(f1_trtr, 4),
            tstr_score=round(f1_tstr, 4),
            utility_retention_pct=retention,
            details={
                "accuracy_trtr": round(float(accuracy_score(y_test, preds_trtr)), 4),
                "accuracy_tstr": round(float(accuracy_score(y_test, preds_tstr)), 4),
            },
        )


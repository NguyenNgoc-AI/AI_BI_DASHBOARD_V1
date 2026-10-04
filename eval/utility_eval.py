"""
Utility Evaluation Module for Synthetic Data (TSTR vs TRTR Framework).

Evaluates the machine learning and analytical utility of synthetic data on a Real Holdout dataset:
1. TSTR (Train on Synthetic, Test on Real) vs TRTR (Train on Real, Test on Real).
2. Downstream Regression Task: Net Profit / Net Sales prediction.
3. Downstream Classification Task: Customer Segment classification.
4. Overall Utility Score calculation based on relative performance retention.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder


@dataclass
class MLTaskEvaluationResult:
    """Evaluation metrics for a specific ML task."""
    task_name: str
    task_type: str  # 'regression' or 'classification'
    target_column: str
    tstr_score: float  # Score from model trained on synthetic, tested on real holdout
    trtr_score: float  # Score from baseline model trained on real seed, tested on real holdout
    utility_ratio_pct: float  # (TSTR / TRTR) * 100
    metrics: Dict[str, Any] = field(default_factory=dict)
    status: str = "PASS"  # PASS, WARNING, FAIL


@dataclass
class UtilityReport:
    """Comprehensive utility evaluation report."""
    overall_utility_score: float  # 0 to 100
    regression_utility_score: float
    classification_utility_score: float
    tasks: Dict[str, MLTaskEvaluationResult] = field(default_factory=dict)
    identified_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts utility report to dictionary format."""
        return {
            "overall_utility_score": self.overall_utility_score,
            "regression_utility_score": self.regression_utility_score,
            "classification_utility_score": self.classification_utility_score,
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "identified_issues": self.identified_issues,
        }


class UtilityEvaluator:
    """
    Evaluates Machine Learning utility of synthetic data using the TSTR / TRTR framework on Holdout data.
    """

    def __init__(
        self,
        random_state: int = 42,
        utility_pass_threshold_pct: float = 75.0,
        utility_warn_threshold_pct: float = 60.0,
    ):
        self.random_state = random_state
        self.utility_pass_threshold_pct = utility_pass_threshold_pct
        self.utility_warn_threshold_pct = utility_warn_threshold_pct

    def _prepare_features(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        cat_cols: List[str],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Aligns, encodes, and prepares feature matrices for training and testing."""
        num_cols = [c for c in feature_cols if c not in cat_cols]

        train_num = train_df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
        test_num = test_df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values

        if cat_cols:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            train_cat = encoder.fit_transform(train_df[cat_cols].astype(str).fillna("Unknown"))
            test_cat = encoder.transform(test_df[cat_cols].astype(str).fillna("Unknown"))

            X_train = np.hstack([train_num, train_cat])
            X_test = np.hstack([test_num, test_cat])
        else:
            X_train = train_num
            X_test = test_num

        return X_train, X_test

    def evaluate_regression_task(
        self,
        real_train_df: pd.DataFrame,
        syn_train_df: pd.DataFrame,
        real_holdout_df: pd.DataFrame,
        target_col: str = "net_profit",
    ) -> MLTaskEvaluationResult:
        """
        Evaluates TSTR vs TRTR on predicting continuous target (e.g. net_profit or net_sales).
        """
        feature_cols = [
            "quantity", "unit_price", "freight_value", "category", "payment_type", "marketing_channel"
        ]
        feature_cols = [c for c in feature_cols if c in real_train_df.columns and c in syn_train_df.columns and c in real_holdout_df.columns]
        cat_cols = [c for c in ["category", "payment_type", "marketing_channel"] if c in feature_cols]

        # Prepare TRTR data (Train Real -> Test Real Holdout)
        X_real_train, X_holdout = self._prepare_features(real_train_df, real_holdout_df, feature_cols, cat_cols)
        y_real_train = real_train_df[target_col].fillna(0).values
        y_holdout = real_holdout_df[target_col].fillna(0).values

        # Prepare TSTR data (Train Synthetic -> Test Real Holdout)
        X_syn_train, _ = self._prepare_features(syn_train_df, real_holdout_df, feature_cols, cat_cols)
        y_syn_train = syn_train_df[target_col].fillna(0).values

        # Train TRTR Model
        model_trtr = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=self.random_state, n_jobs=-1)
        model_trtr.fit(X_real_train, y_real_train)
        y_pred_trtr = model_trtr.predict(X_holdout)
        r2_trtr = max(0.01, float(r2_score(y_holdout, y_pred_trtr)))
        mae_trtr = float(mean_absolute_error(y_holdout, y_pred_trtr))

        # Train TSTR Model
        model_tstr = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=self.random_state, n_jobs=-1)
        model_tstr.fit(X_syn_train, y_syn_train)
        y_pred_tstr = model_tstr.predict(X_holdout)
        r2_tstr = max(0.0, float(r2_score(y_holdout, y_pred_tstr)))
        mae_tstr = float(mean_absolute_error(y_holdout, y_pred_tstr))

        # Utility Ratio
        ratio_pct = round(min(100.0, max(0.0, (r2_tstr / r2_trtr) * 100.0)), 2)

        status = "PASS" if ratio_pct >= self.utility_pass_threshold_pct else ("WARNING" if ratio_pct >= self.utility_warn_threshold_pct else "FAIL")

        return MLTaskEvaluationResult(
            task_name=f"Regression_{target_col}",
            task_type="regression",
            target_column=target_col,
            tstr_score=round(r2_tstr, 4),
            trtr_score=round(r2_trtr, 4),
            utility_ratio_pct=ratio_pct,
            metrics={
                "tstr_r2": round(r2_tstr, 4),
                "trtr_r2": round(r2_trtr, 4),
                "tstr_mae": round(mae_tstr, 2),
                "trtr_mae": round(mae_trtr, 2),
            },
            status=status,
        )

    def evaluate_classification_task(
        self,
        real_train_df: pd.DataFrame,
        syn_train_df: pd.DataFrame,
        real_holdout_df: pd.DataFrame,
        target_col: str = "customer_segment",
    ) -> MLTaskEvaluationResult:
        """
        Evaluates TSTR vs TRTR on classifying customer segment.
        """
        feature_cols = [
            "quantity", "gross_sales", "unit_price", "payment_value", "payment_type", "state"
        ]
        feature_cols = [c for c in feature_cols if c in real_train_df.columns and c in syn_train_df.columns and c in real_holdout_df.columns]
        cat_cols = [c for c in ["payment_type", "state"] if c in feature_cols]

        X_real_train, X_holdout = self._prepare_features(real_train_df, real_holdout_df, feature_cols, cat_cols)
        y_real_train = real_train_df[target_col].astype(str).fillna("Unknown").values
        y_holdout = real_holdout_df[target_col].astype(str).fillna("Unknown").values

        X_syn_train, _ = self._prepare_features(syn_train_df, real_holdout_df, feature_cols, cat_cols)
        y_syn_train = syn_train_df[target_col].astype(str).fillna("Unknown").values

        # TRTR Classifier
        clf_trtr = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=self.random_state, n_jobs=-1)
        clf_trtr.fit(X_real_train, y_real_train)
        y_pred_trtr = clf_trtr.predict(X_holdout)
        f1_trtr = max(0.01, float(f1_score(y_holdout, y_pred_trtr, average="weighted", zero_division=0)))
        acc_trtr = float(accuracy_score(y_holdout, y_pred_trtr))

        # TSTR Classifier
        clf_tstr = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=self.random_state, n_jobs=-1)
        clf_tstr.fit(X_syn_train, y_syn_train)
        y_pred_tstr = clf_tstr.predict(X_holdout)
        f1_tstr = float(f1_score(y_holdout, y_pred_tstr, average="weighted", zero_division=0))
        acc_tstr = float(accuracy_score(y_holdout, y_pred_tstr))

        ratio_pct = round(min(100.0, max(0.0, (f1_tstr / f1_trtr) * 100.0)), 2)
        status = "PASS" if ratio_pct >= self.utility_pass_threshold_pct else ("WARNING" if ratio_pct >= self.utility_warn_threshold_pct else "FAIL")

        return MLTaskEvaluationResult(
            task_name=f"Classification_{target_col}",
            task_type="classification",
            target_column=target_col,
            tstr_score=round(f1_tstr, 4),
            trtr_score=round(f1_trtr, 4),
            utility_ratio_pct=ratio_pct,
            metrics={
                "tstr_weighted_f1": round(f1_tstr, 4),
                "trtr_weighted_f1": round(f1_trtr, 4),
                "tstr_accuracy": round(acc_tstr, 4),
                "trtr_accuracy": round(acc_trtr, 4),
            },
            status=status,
        )

    def evaluate(
        self,
        real_train_df: pd.DataFrame,
        syn_train_df: pd.DataFrame,
        real_holdout_df: pd.DataFrame,
    ) -> UtilityReport:
        """
        Executes complete Machine Learning utility evaluation suite across downstream tasks.
        """
        tasks: Dict[str, MLTaskEvaluationResult] = {}
        issues: List[str] = []

        # 1. Regression Task: net_profit
        if "net_profit" in real_train_df.columns:
            reg_res = self.evaluate_regression_task(real_train_df, syn_train_df, real_holdout_df, target_col="net_profit")
            tasks["regression_net_profit"] = reg_res
            if reg_res.status != "PASS":
                issues.append(f"Regression utility degradation on net_profit: TSTR ratio = {reg_res.utility_ratio_pct}% (R2={reg_res.tstr_score} vs Real={reg_res.trtr_score}).")

        # 2. Classification Task: customer_segment
        if "customer_segment" in real_train_df.columns:
            clf_res = self.evaluate_classification_task(real_train_df, syn_train_df, real_holdout_df, target_col="customer_segment")
            tasks["classification_customer_segment"] = clf_res
            if clf_res.status != "PASS":
                issues.append(f"Classification utility degradation on customer_segment: TSTR ratio = {clf_res.utility_ratio_pct}% (F1={clf_res.tstr_score} vs Real={clf_res.trtr_score}).")

        scores = [t.utility_ratio_pct for t in tasks.values()]
        overall_utility = round(float(np.mean(scores)), 2) if scores else 100.0

        reg_score = tasks.get("regression_net_profit", MLTaskEvaluationResult("reg", "regression", "net_profit", 0, 0, 100.0)).utility_ratio_pct
        clf_score = tasks.get("classification_customer_segment", MLTaskEvaluationResult("clf", "classification", "customer_segment", 0, 0, 100.0)).utility_ratio_pct

        return UtilityReport(
            overall_utility_score=overall_utility,
            regression_utility_score=reg_score,
            classification_utility_score=clf_score,
            tasks=tasks,
            identified_issues=issues,
        )

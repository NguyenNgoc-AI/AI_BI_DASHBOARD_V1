"""
Schema Extractor Module for AI BI Dashboard.

Extracts comprehensive statistical profiles, distributions, correlation matrices,
hierarchical conditional probabilities, and temporal patterns from raw or seed datasets.
Produces serializable metadata profiles to guide synthetic data generation.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ColumnProfile:
    """Metadata and statistical profile of a single column."""
    name: str
    physical_dtype: str
    semantic_type: str
    total_count: int
    null_count: int
    null_rate_pct: float
    distinct_count: int
    distinct_rate_pct: float
    distribution_type: str  # 'numerical', 'categorical', 'datetime', 'boolean', 'identifier'
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataDistribution:
    """Statistical distribution attributes for columns."""
    numerical_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    categorical_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    conditional_distributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    temporal_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class LearnedSchemaProfile:
    """Encapsulates the complete learned metadata and statistical profile of a dataset."""
    dataset_name: str
    extracted_at: str
    total_records: int
    total_columns: int
    column_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    distributions: Dict[str, Any] = field(default_factory=dict)
    correlation_matrices: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
    hierarchies: Dict[str, Any] = field(default_factory=dict)
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    bounds: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts profile to a JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serializes profile to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, filepath: Union[str, Path]) -> None:
        """Saves profile to disk as a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "LearnedSchemaProfile":
        """Loads a LearnedSchemaProfile from a saved JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


class SchemaExtractor:
    """
    Extracts statistical distributions, semantic data types, correlation matrices,
    and hierarchical conditional probabilities from datasets.
    """

    def __init__(
        self,
        dataset_name: str = "ecommerce_dataset",
        schema_path: Optional[Union[str, Path]] = None,
    ):
        self.dataset_name = dataset_name
        self.schema_metadata: Dict[str, Any] = {}
        if schema_path and Path(schema_path).exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema_metadata = json.load(f)

    def infer_semantic_type(self, series: pd.Series, col_name: str) -> str:
        """Infers the semantic data type of a column based on name, values, and schema."""
        col_lower = col_name.lower()

        # Check against schema definitions if present
        if "tables" in self.schema_metadata:
            for table_info in self.schema_metadata["tables"].values():
                cols = table_info.get("columns", {})
                if col_name in cols:
                    return cols[col_name].get("semantic_type", "unknown")

        if series.empty:
            return "unknown"

        # Check identifiers
        if "id" in col_lower or "sku" in col_lower or "code" in col_lower:
            return "identifier"

        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "timestamp"
        if "date" in col_lower or "timestamp" in col_lower or "time" in col_lower:
            try:
                sample = series.dropna().head(30)
                if not sample.empty:
                    pd.to_datetime(sample)
                    return "timestamp"
            except Exception:
                pass

        # Check boolean
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        non_null = series.dropna()
        if not non_null.empty and non_null.isin([True, False, 0, 1, "0", "1", "True", "False"]).all():
            if series.nunique() <= 2:
                return "boolean"

        # Check numerical subtypes
        if pd.api.types.is_numeric_dtype(series):
            if any(w in col_lower for w in ["price", "cost", "sales", "revenue", "profit", "spend", "fee", "tax", "value", "payment", "cogs"]):
                return "numerical_currency"
            if any(w in col_lower for w in ["rate", "pct", "percent", "margin", "ratio"]):
                return "numerical_ratio"
            if any(w in col_lower for w in ["qty", "quantity", "count", "installments", "impressions", "clicks", "conversions"]):
                return "numerical_quantity"
            return "numerical"

        # Check geographic
        if any(w in col_lower for w in ["city", "state", "country", "province"]):
            return "categorical_geographic"
        if "zip" in col_lower or "postal" in col_lower:
            return "postal_code"

        # Check categorical
        distinct_count = series.nunique()
        total_valid = len(series.dropna())
        if total_valid > 0 and (distinct_count / total_valid < 0.05 or distinct_count <= 50):
            return "categorical"

        return "text"

    def _profile_numerical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Calculates rich statistical descriptive metrics for numerical columns."""
        clean = series.dropna()
        if clean.empty:
            return {"status": "empty"}

        vals = clean.values.astype(float)
        q01, q05, q10, q25, q50, q75, q90, q95, q99 = np.percentile(
            vals, [1, 5, 10, 25, 50, 75, 90, 95, 99]
        )
        iqr = float(q75 - q25)
        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        min_val = float(np.min(vals))
        max_val = float(np.max(vals))

        if std_val < 1e-9 or np.all(vals == vals[0]):
            skew_val = 0.0
            kurt_val = 0.0
        else:
            skew_val = float(stats.skew(vals)) if len(vals) > 2 else 0.0
            kurt_val = float(stats.kurtosis(vals)) if len(vals) > 3 else 0.0

        # Histogram estimation (10 bins)
        hist_counts, bin_edges = np.histogram(vals, bins=10)
        bins_data = [
            {"bin_start": round(float(bin_edges[i]), 4), "bin_end": round(float(bin_edges[i+1]), 4), "count": int(hist_counts[i])}
            for i in range(len(hist_counts))
        ]

        is_integer = bool(np.all(np.mod(vals, 1) == 0))

        return {
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "variance": round(std_val ** 2, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "median": round(float(q50), 4),
            "iqr": round(iqr, 4),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
            "is_integer": is_integer,
            "percentiles": {
                "p01": round(float(q01), 4),
                "p05": round(float(q05), 4),
                "p10": round(float(q10), 4),
                "p25": round(float(q25), 4),
                "p50": round(float(q50), 4),
                "p75": round(float(q75), 4),
                "p90": round(float(q90), 4),
                "p95": round(float(q95), 4),
                "p99": round(float(q99), 4),
            },
            "histogram": bins_data,
        }

    def _profile_categorical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Calculates category distributions, frequencies, and probabilities."""
        clean = series.dropna().astype(str)
        if clean.empty:
            return {"status": "empty"}

        val_counts = clean.value_counts()
        total = len(clean)
        top_categories = {}
        for val, count in val_counts.items():
            top_categories[str(val)] = {
                "count": int(count),
                "probability": round(float(count / total), 6),
            }

        return {
            "distinct_count": len(val_counts),
            "top_value": str(clean.mode().iloc[0]) if not clean.empty else None,
            "top_value_frequency": int(val_counts.iloc[0]) if not val_counts.empty else 0,
            "categories": top_categories,
        }

    def _profile_temporal_column(self, series: pd.Series) -> Dict[str, Any]:
        """Calculates date ranges and temporal distributions."""
        dt_series = pd.to_datetime(series, errors="coerce").dropna()
        if dt_series.empty:
            return {"status": "empty"}

        min_dt = dt_series.min()
        max_dt = dt_series.max()

        day_of_week_counts = dt_series.dt.day_name().value_counts().to_dict()
        hour_counts = dt_series.dt.hour.value_counts().to_dict()

        return {
            "min_timestamp": min_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "max_timestamp": max_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "range_days": round(float((max_dt - min_dt).total_seconds() / 86400), 2),
            "day_of_week_distribution": {k: int(v) for k, v in day_of_week_counts.items()},
            "hour_distribution": {int(k): int(v) for k, v in hour_counts.items()},
        }

    def _extract_hierarchical_conditionals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extracts conditional probabilities for hierarchical relationships:
        1. Category -> Sub-category
        2. State -> City
        3. Marketing Channel -> Conversion rate / average spend
        4. Customer Segment -> Payment types
        """
        conditionals: Dict[str, Any] = {}

        # 1. Category -> Sub-category
        if "category" in df.columns and "sub_category" in df.columns:
            cat_sub = {}
            for cat, group in df.groupby("category"):
                sub_counts = group["sub_category"].dropna().value_counts()
                total = len(group["sub_category"].dropna())
                if total > 0:
                    cat_sub[str(cat)] = {
                        str(sub): round(float(cnt / total), 4)
                        for sub, cnt in sub_counts.items()
                    }
            conditionals["category_to_subcategory"] = cat_sub

        # 2. State -> City (top cities per state)
        if "state" in df.columns and "city" in df.columns:
            state_city = {}
            for state, group in df.groupby("state"):
                city_counts = group["city"].dropna().value_counts()
                total = len(group["city"].dropna())
                if total > 0:
                    top_cities = {
                        str(city): round(float(cnt / total), 4)
                        for city, cnt in city_counts.head(15).items()
                    }
                    state_city[str(state)] = top_cities
            conditionals["state_to_city"] = state_city

        # 3. Category -> Price & Margin statistics
        if "category" in df.columns and "unit_price" in df.columns and "unit_cost" in df.columns:
            cat_pricing = {}
            for cat, group in df.groupby("category"):
                cat_pricing[str(cat)] = {
                    "mean_unit_price": round(float(group["unit_price"].mean()), 2),
                    "std_unit_price": round(float(group["unit_price"].std(ddof=1) if len(group) > 1 else 0.0), 2),
                    "mean_unit_cost": round(float(group["unit_cost"].mean()), 2),
                    "mean_margin_rate": round(float(group["margin_rate"].mean()), 4) if "margin_rate" in group.columns else 0.0,
                }
            conditionals["category_pricing_patterns"] = cat_pricing

        # 4. Customer Segment -> Payment Type
        if "customer_segment" in df.columns and "payment_type" in df.columns:
            seg_pay = {}
            for seg, group in df.groupby("customer_segment"):
                pay_counts = group["payment_type"].dropna().value_counts()
                total = len(group["payment_type"].dropna())
                if total > 0:
                    seg_pay[str(seg)] = {
                        str(p): round(float(cnt / total), 4)
                        for p, cnt in pay_counts.items()
                    }
            conditionals["segment_to_payment_type"] = seg_pay

        return conditionals

    def _extract_lifecycle_temporal_deltas(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extracts statistical distributions of order lifecycle duration deltas (in hours/days).
        - purchase -> approved (hours)
        - approved -> carrier (hours)
        - carrier -> delivered (hours/days)
        - purchase -> estimated_delivery (days)
        """
        deltas: Dict[str, Any] = {}

        cols = df.columns
        p_col = "order_purchase_timestamp"
        a_col = "order_approved_at"
        c_col = "order_delivered_carrier_date"
        d_col = "order_delivered_customer_date"
        e_col = "order_estimated_delivery_date"

        # Helper to compute delta stats
        def compute_delta_stats(start_col: str, end_col: str, unit: str = "hours") -> Optional[Dict[str, Any]]:
            if start_col in cols and end_col in cols:
                start_dt = pd.to_datetime(df[start_col], errors="coerce")
                end_dt = pd.to_datetime(df[end_col], errors="coerce")
                diff = (end_dt - start_dt).dt.total_seconds()
                valid_diff = diff.dropna()
                valid_diff = valid_diff[valid_diff >= 0]  # Non-negative durations
                if not valid_diff.empty:
                    factor = 3600.0 if unit == "hours" else 86400.0
                    vals = (valid_diff / factor).values
                    return {
                        "unit": unit,
                        "mean": round(float(np.mean(vals)), 2),
                        "median": round(float(np.median(vals)), 2),
                        "std": round(float(np.std(vals, ddof=1) if len(vals) > 1 else 0.0), 2),
                        "min": round(float(np.min(vals)), 2),
                        "max": round(float(np.max(vals)), 2),
                        "p95": round(float(np.percentile(vals, 95)), 2),
                    }
            return None

        deltas["purchase_to_approved_hours"] = compute_delta_stats(p_col, a_col, "hours")
        deltas["approved_to_carrier_hours"] = compute_delta_stats(a_col, c_col, "hours")
        deltas["carrier_to_delivered_days"] = compute_delta_stats(c_col, d_col, "days")
        deltas["purchase_to_estimated_days"] = compute_delta_stats(p_col, e_col, "days")

        return {k: v for k, v in deltas.items() if v is not None}

    def _extract_correlation_matrices(self, df: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Calculates Pearson and Spearman correlation matrices for numerical columns, sanitizing constant columns and NaNs."""
        # Filter out non-metric columns like zip_code or ID integers
        ignored_cols = {"zip_code", "postal_code", "id", "customer_id", "order_id", "product_id", "sales_id"}
        num_cols = [
            col for col in df.select_dtypes(include=[np.number]).columns
            if col.lower() not in ignored_cols and not col.lower().endswith("_id")
        ]
        if len(num_cols) < 2:
            return {}

        clean_df = df[num_cols].dropna()
        if clean_df.empty or len(clean_df) < 5:
            clean_df = df[num_cols].fillna(0)

        # Pearson & Spearman calculation, filling NaN from zero-variance/constant columns with 0.0
        pearson_df = clean_df.corr(method="pearson").fillna(0.0).round(4)
        spearman_df = clean_df.corr(method="spearman").fillna(0.0).round(4)

        return {
            "pearson": {col: {k: float(v) for k, v in pearson_df[col].to_dict().items()} for col in pearson_df.columns},
            "spearman": {col: {k: float(v) for k, v in spearman_df[col].to_dict().items()} for col in spearman_df.columns},
        }

    def extract(self, data: Union[pd.DataFrame, str, Path]) -> LearnedSchemaProfile:
        """
        Extracts complete LearnedSchemaProfile from a DataFrame or CSV file path.
        """
        if isinstance(data, (str, Path)):
            df = pd.read_csv(data)
        else:
            df = data.copy()

        total_records = len(df)
        total_cols = len(df.columns)

        column_profiles: Dict[str, Dict[str, Any]] = {}
        numerical_stats: Dict[str, Dict[str, Any]] = {}
        categorical_stats: Dict[str, Dict[str, Any]] = {}
        temporal_stats: Dict[str, Dict[str, Any]] = {}
        bounds: Dict[str, Dict[str, float]] = {}

        for col in df.columns:
            series = df[col]
            sem_type = self.infer_semantic_type(series, col)
            phys_type = str(series.dtype)
            null_count = int(series.isna().sum())
            null_rate = round(float(null_count / total_records * 100.0), 2) if total_records > 0 else 0.0
            distinct_count = int(series.nunique())
            distinct_rate = round(float(distinct_count / total_records * 100.0), 2) if total_records > 0 else 0.0

            stats_dict: Dict[str, Any] = {}
            dist_type = "unknown"

            if sem_type.startswith("numerical"):
                dist_type = "numerical"
                stats_dict = self._profile_numerical_column(series)
                numerical_stats[col] = stats_dict
                if "min" in stats_dict and "max" in stats_dict:
                    bounds[col] = {"min": stats_dict["min"], "max": stats_dict["max"]}
            elif sem_type in ["timestamp", "datetime", "date"]:
                dist_type = "datetime"
                stats_dict = self._profile_temporal_column(series)
                temporal_stats[col] = stats_dict
            elif sem_type in ["categorical", "categorical_geographic", "boolean"]:
                dist_type = "categorical"
                stats_dict = self._profile_categorical_column(series)
                categorical_stats[col] = stats_dict
            elif sem_type == "identifier":
                dist_type = "identifier"
                stats_dict = {"format": f"{col.upper()}_PATTERN", "is_unique": distinct_count == total_records}
            else:
                dist_type = "text"
                stats_dict = {"sample_length_avg": round(float(series.dropna().astype(str).str.len().mean()), 1) if not series.dropna().empty else 0}

            col_prof = ColumnProfile(
                name=col,
                physical_dtype=phys_type,
                semantic_type=sem_type,
                total_count=total_records,
                null_count=null_count,
                null_rate_pct=null_rate,
                distinct_count=distinct_count,
                distinct_rate_pct=distinct_rate,
                distribution_type=dist_type,
                stats=stats_dict,
            )
            column_profiles[col] = asdict(col_prof)

        # Extract higher-level patterns
        hierarchies = self._extract_hierarchical_conditionals(df)
        temporal_patterns = self._extract_lifecycle_temporal_deltas(df)
        correlation_matrices = self._extract_correlation_matrices(df)

        distributions_payload = {
            "numerical": numerical_stats,
            "categorical": categorical_stats,
            "temporal": temporal_stats,
        }

        profile = LearnedSchemaProfile(
            dataset_name=self.dataset_name,
            extracted_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_records=total_records,
            total_columns=total_cols,
            column_profiles=column_profiles,
            distributions=distributions_payload,
            correlation_matrices=correlation_matrices,
            hierarchies=hierarchies,
            temporal_patterns=temporal_patterns,
            bounds=bounds,
        )

        return profile

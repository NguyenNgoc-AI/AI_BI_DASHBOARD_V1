"""
Data Profiling Engine for AI BI Dashboard.

Performs comprehensive statistical distribution analysis on datasets:
- Column-level summary (mean, std, min, max, quantiles, skewness, kurtosis, nulls, cardinality)
- Semantic data type inference
- Correlation matrix analysis (Pearson & Spearman)
- Statistical distribution characteristics for numerical, categorical, and datetime columns
- Serialization to Dictionary, JSON, and Markdown formats.
"""

from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats


class DataProfiler:
    """Statistical Data Profiling Engine."""

    def __init__(self, dataset_name: str = "dataset"):
        self.dataset_name = dataset_name

    def infer_semantic_type(self, series: pd.Series, col_name: str) -> str:
        """Infers the business semantic type of a pandas Series."""
        col_lower = col_name.lower()
        if series.empty:
            return "unknown"

        # Check identifiers
        if "id" in col_lower or "code" in col_lower or "sku" in col_lower:
            return "identifier"

        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        if "date" in col_lower or "timestamp" in col_lower or "time" in col_lower:
            try:
                pd.to_datetime(series.dropna().head(20))
                return "datetime"
            except Exception:
                pass

        # Check boolean
        if pd.api.types.is_bool_dtype(series) or series.dropna().isin([True, False, 0, 1, "0", "1"]).all():
            if series.nunique() <= 2:
                return "boolean"

        # Check numerical
        if pd.api.types.is_numeric_dtype(series):
            if any(w in col_lower for w in ["price", "cost", "sales", "revenue", "profit", "spend", "fee", "tax", "value", "payment"]):
                return "numerical_currency"
            if any(w in col_lower for w in ["rate", "pct", "percent", "margin", "ratio"]):
                return "numerical_ratio"
            if any(w in col_lower for w in ["qty", "quantity", "count", "installments", "impressions", "clicks", "conversions"]):
                return "numerical_quantity"
            return "numerical"

        # Check categorical / text
        unique_count = series.nunique()
        total_count = len(series.dropna())
        if total_count > 0 and (unique_count / total_count < 0.05 or unique_count <= 50):
            return "categorical"

        return "text"

    def profile_numerical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Calculates rich statistical descriptive metrics for numerical columns."""
        clean = series.dropna()
        if clean.empty:
            return {"status": "empty_or_all_null"}

        vals = clean.values.astype(float)
        q01, q05, q25, q50, q75, q95, q99 = np.percentile(vals, [1, 5, 25, 50, 75, 95, 99])
        iqr = q75 - q25

        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        min_val = float(np.min(vals))
        max_val = float(np.max(vals))

        # Skewness and Kurtosis (guard against zero variance / constant column)
        if std_val < 1e-9 or np.all(vals == vals[0]):
            skew_val = 0.0
            kurt_val = 0.0
        else:
            skew_val = float(stats.skew(vals)) if len(vals) > 2 else 0.0
            kurt_val = float(stats.kurtosis(vals)) if len(vals) > 3 else 0.0


        # Outliers count based on 1.5 * IQR rule
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        outliers_count = int(np.sum((vals < lower_bound) | (vals > upper_bound)))
        outliers_pct = round(outliers_count / len(vals) * 100.0, 2)

        return {
            "count": int(len(clean)),
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "median": round(float(q50), 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
            "quantiles": {
                "q01": round(float(q01), 4),
                "q05": round(float(q05), 4),
                "q25": round(float(q25), 4),
                "q50": round(float(q50), 4),
                "q75": round(float(q75), 4),
                "q95": round(float(q95), 4),
                "q99": round(float(q99), 4),
                "iqr": round(float(iqr), 4),
            },
            "zero_count": int(np.sum(vals == 0)),
            "negative_count": int(np.sum(vals < 0)),
            "positive_count": int(np.sum(vals > 0)),
            "outliers_iqr_1_5x": {
                "count": outliers_count,
                "pct": outliers_pct,
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
            },
        }

    def profile_categorical_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profiles categorical / discrete column values, top frequency and distribution entropy."""
        clean = series.dropna().astype(str)
        if clean.empty:
            return {"status": "empty_or_all_null"}

        value_counts = clean.value_counts()
        total = len(clean)
        top_10 = []
        for val, count in value_counts.head(10).items():
            top_10.append({
                "value": str(val),
                "count": int(count),
                "percentage": round(count / total * 100.0, 2),
            })

        # Calculate Shannon Entropy
        probs = value_counts / total
        entropy_val = float(-np.sum(probs * np.log2(probs + 1e-12)))

        return {
            "distinct_count": int(len(value_counts)),
            "top_10_values": top_10,
            "shannon_entropy": round(entropy_val, 4),
            "is_high_cardinality": bool(len(value_counts) > 100),
        }

    def profile_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profiles temporal datetime columns."""
        clean_dt = pd.to_datetime(series.dropna(), errors="coerce").dropna()
        if clean_dt.empty:
            return {"status": "empty_or_invalid_datetime"}

        min_dt = clean_dt.min()
        max_dt = clean_dt.max()
        duration_days = (max_dt - min_dt).total_seconds() / (24 * 3600)

        return {
            "min_datetime": str(min_dt),
            "max_datetime": str(max_dt),
            "duration_days": round(duration_days, 2),
            "year_range": [int(min_dt.year), int(max_dt.year)],
            "distinct_dates": int(clean_dt.dt.date.nunique()),
        }

    def profile_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Performs complete end-to-end dataset profiling."""
        total_rows = len(df)
        total_cols = len(df.columns)
        memory_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        column_profiles = {}
        numerical_cols = []

        for col in df.columns:
            series = df[col]
            null_cnt = int(series.isna().sum())
            null_pct = round(null_cnt / total_rows * 100.0, 2) if total_rows > 0 else 0.0
            distinct_cnt = int(series.nunique())
            distinct_pct = round(distinct_cnt / total_rows * 100.0, 2) if total_rows > 0 else 0.0
            semantic_type = self.infer_semantic_type(series, col)

            col_meta: Dict[str, Any] = {
                "name": col,
                "dtype": str(series.dtype),
                "semantic_type": semantic_type,
                "null_count": null_cnt,
                "null_pct": null_pct,
                "distinct_count": distinct_cnt,
                "distinct_pct": distinct_pct,
            }

            if pd.api.types.is_numeric_dtype(series):
                numerical_cols.append(col)
                col_meta["stats"] = self.profile_numerical_column(series)
            elif semantic_type == "datetime":
                col_meta["stats"] = self.profile_datetime_column(series)
            else:
                col_meta["stats"] = self.profile_categorical_column(series)

            column_profiles[col] = col_meta

        # Correlation Matrix on numerical variables
        correlation_matrix = {}
        top_correlations = []
        if len(numerical_cols) >= 2:
            corr_df = df[numerical_cols].corr(method="pearson").round(4)
            correlation_matrix = corr_df.to_dict()

            # Find top pairwise correlations
            seen_pairs = set()
            for c1 in numerical_cols:
                for c2 in numerical_cols:
                    if c1 != c2 and (c2, c1) not in seen_pairs:
                        seen_pairs.add((c1, c2))
                        val = corr_df.loc[c1, c2]
                        if not math.isnan(val):
                            top_correlations.append({
                                "column_1": c1,
                                "column_2": c2,
                                "pearson_r": round(float(val), 4),
                                "strength": "Strong Positive" if val >= 0.7 else ("Strong Negative" if val <= -0.7 else "Moderate/Weak"),
                            })
            top_correlations.sort(key=lambda x: abs(x["pearson_r"]), reverse=True)

        return {
            "dataset_name": self.dataset_name,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_rows": total_rows,
                "total_columns": total_cols,
                "memory_usage_mb": memory_usage_mb,
                "total_null_cells": int(df.isna().sum().sum()),
                "total_cells": total_rows * total_cols,
                "null_density_pct": round(df.isna().sum().sum() / (total_rows * total_cols) * 100.0, 2) if total_rows > 0 else 0.0,
                "numerical_columns_count": len(numerical_cols),
            },
            "columns": column_profiles,
            "correlation_matrix": correlation_matrix,
            "top_correlations": top_correlations[:15],
        }

    def generate_markdown_report(self, profile: Dict[str, Any]) -> str:
        """Renders profiling dictionary into a structured markdown document."""
        s = profile["summary"]
        lines = [
            f"# BÁO CÁO PHÂN TÍCH PHÂN PHỐI DỮ LIỆU (DATA PROFILING REPORT)",
            f"",
            f"> **Tập dữ liệu:** `{profile['dataset_name']}`  ",
            f"> **Thời gian khởi tạo:** `{profile['generated_at']}` UTC  ",
            f"> **Quy mô:** **{s['total_rows']:,} dòng** | **{s['total_columns']} cột** | **{s['memory_usage_mb']} MB**  ",
            f"> **Tỷ lệ ô khuyết (Null density):** `{s['null_density_pct']}%` ({s['total_null_cells']:,} ô)  ",
            f"",
            f"---",
            f"",
            f"## I. BẢNG TỔNG QUAN THUỘC TÍNH (COLUMN METRICS)",
            f"",
            f"| STT | Tên cột | Kiểu dữ liệu | Semantic Type | Null % | Số giá trị duy nhất | Min | Max | Mean | Median |",
            f"|---|---|---|---|---|---|---|---|---|---|",
        ]

        idx = 1
        for col_name, c in profile["columns"].items():
            st = c.get("stats", {})
            min_v = st.get("min", "-")
            max_v = st.get("max", "-")
            mean_v = st.get("mean", "-")
            med_v = st.get("median", "-")

            lines.append(
                f"| {idx} | `{col_name}` | `{c['dtype']}` | `{c['semantic_type']}` | {c['null_pct']}% | {c['distinct_count']:,} | {min_v} | {max_v} | {mean_v} | {med_v} |"
            )
            idx += 1

        lines.extend([
            f"",
            f"---",
            f"",
            f"## II. TƯƠNG QUAN BIẾN TÀI CHÍNH HÀNG ĐẦU (TOP CORRELATIONS)",
            f"",
            f"| Biến 1 | Biến 2 | Pearson $r$ | Đánh giá tương quan |",
            f"|---|---|---|---|",
        ])

        for corr in profile.get("top_correlations", [])[:10]:
            lines.append(
                f"| `{corr['column_1']}` | `{corr['column_2']}` | **{corr['pearson_r']}** | {corr['strength']} |"
            )

        return "\n".join(lines)

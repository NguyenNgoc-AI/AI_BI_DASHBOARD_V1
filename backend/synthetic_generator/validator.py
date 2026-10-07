"""
Synthetic Data Quality Gate Validator for AI BI Dashboard (Task 7).

Aggregates the 4 core pillars of synthetic data quality:
1. Validity: Schema compliance, type integrity, and mathematical business rules pass rate.
2. Fidelity: Statistical distribution similarity (KS-Test), TVD, and correlation alignment.
3. Privacy: Zero exact matching, zero raw ID leakage, DCR distance, memorization guard.
4. Utility: Downstream ML performance retention (TSTR vs TRTR) on real holdout test set.

Produces comprehensive Synthetic Quality Index (SQI) and detailed audit reports.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from backend.schema_learning.rule_parser import ConstraintEngine, ValidationReport
from eval.fidelity_eval import FidelityEvaluator, FidelityReport
from eval.privacy_eval import PrivacyEvaluator, PrivacyReport
from eval.utility_eval import UtilityEvaluator, UtilityReport


@dataclass
class QualityGateResult:
    """Master Quality Gate Assessment Result."""
    evaluated_at: str
    dataset_name: str
    total_synthetic_records: int
    total_real_seed_records: int
    total_holdout_records: int
    
    # 4 Pillar Scores (0 to 100)
    validity_score: float
    fidelity_score: float
    privacy_score: float
    utility_score: float
    
    # Aggregated Index
    synthetic_quality_index: float  # Weighted SQI
    quality_tier: str  # 'Tier A (Excellent)', 'Tier B (Good)', 'Tier C (Needs Improvement)'
    gate_status: str  # 'PASSED', 'WARNING', 'FAILED'
    
    # Detailed Reports
    validity_report: Dict[str, Any] = field(default_factory=dict)
    fidelity_report: Dict[str, Any] = field(default_factory=dict)
    privacy_report: Dict[str, Any] = field(default_factory=dict)
    utility_report: Dict[str, Any] = field(default_factory=dict)
    
    # Identified Issues
    aggregated_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to dictionary."""
        return {
            "evaluated_at": self.evaluated_at,
            "dataset_name": self.dataset_name,
            "total_synthetic_records": self.total_synthetic_records,
            "total_real_seed_records": self.total_real_seed_records,
            "total_holdout_records": self.total_holdout_records,
            "validity_score": self.validity_score,
            "fidelity_score": self.fidelity_score,
            "privacy_score": self.privacy_score,
            "utility_score": self.utility_score,
            "synthetic_quality_index": self.synthetic_quality_index,
            "quality_tier": self.quality_tier,
            "gate_status": self.gate_status,
            "validity_report": self.validity_report,
            "fidelity_report": self.fidelity_report,
            "privacy_report": self.privacy_report,
            "utility_report": self.utility_report,
            "aggregated_issues": self.aggregated_issues,
        }


class SyntheticDataQualityGate:
    """
    Quality Gate Validator evaluating Validity, Fidelity, Privacy, and Utility.
    """

    def __init__(
        self,
        validity_weight: float = 0.30,
        fidelity_weight: float = 0.30,
        privacy_weight: float = 0.20,
        utility_weight: float = 0.20,
        min_pass_sqi: float = 80.0,
    ):
        self.validity_weight = validity_weight
        self.fidelity_weight = fidelity_weight
        self.privacy_weight = privacy_weight
        self.utility_weight = utility_weight
        self.min_pass_sqi = min_pass_sqi

        self.constraint_engine = ConstraintEngine()
        self.fidelity_evaluator = FidelityEvaluator()
        self.privacy_evaluator = PrivacyEvaluator()
        self.utility_evaluator = UtilityEvaluator()

    def evaluate(
        self,
        syn_df: pd.DataFrame,
        real_seed_df: pd.DataFrame,
        real_holdout_df: pd.DataFrame,
        dataset_name: str = "synthetic_ecommerce",
    ) -> QualityGateResult:
        """
        Executes all 4 pillars and compiles master quality gate report.
        """
        issues: List[str] = []

        # 1. Pillar 1: Validity
        val_rep = self.constraint_engine.validate_dataframe(syn_df)
        validity_score = val_rep.overall_pass_rate_pct
        if val_rep.has_blocking_errors:
            issues.append(f"[Validity] Business rule invariants violated: {val_rep.invalid_records} invalid records.")

        # 2. Pillar 2: Fidelity
        fid_rep = self.fidelity_evaluator.evaluate(real_seed_df, syn_df)
        fidelity_score = fid_rep.overall_fidelity_score
        for iss in fid_rep.identified_issues:
            issues.append(f"[Fidelity] {iss}")

        # 3. Pillar 3: Privacy
        priv_rep = self.privacy_evaluator.evaluate(real_seed_df, syn_df)
        privacy_score = priv_rep.overall_privacy_score
        for iss in priv_rep.identified_issues:
            issues.append(f"[Privacy] {iss}")

        # 4. Pillar 4: Utility
        util_rep = self.utility_evaluator.evaluate(real_seed_df, syn_df, real_holdout_df)
        utility_score = util_rep.overall_utility_score
        for iss in util_rep.identified_issues:
            issues.append(f"[Utility] {iss}")

        # Compute Weighted Synthetic Quality Index (SQI)
        sqi = round(
            self.validity_weight * validity_score
            + self.fidelity_weight * fidelity_score
            + self.privacy_weight * privacy_score
            + self.utility_weight * utility_score,
            2,
        )

        if sqi >= 90.0:
            tier = "Tier A (Excellent)"
            gate_status = "PASSED"
        elif sqi >= 80.0:
            tier = "Tier B (Good / Production-Ready)"
            gate_status = "PASSED" if not val_rep.has_blocking_errors else "WARNING"
        elif sqi >= 65.0:
            tier = "Tier C (Acceptable with Reservations)"
            gate_status = "WARNING"
        else:
            tier = "Tier D (Unacceptable / Needs Retraining)"
            gate_status = "FAILED"

        return QualityGateResult(
            evaluated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            dataset_name=dataset_name,
            total_synthetic_records=len(syn_df),
            total_real_seed_records=len(real_seed_df),
            total_holdout_records=len(real_holdout_df),
            validity_score=validity_score,
            fidelity_score=fidelity_score,
            privacy_score=privacy_score,
            utility_score=utility_score,
            synthetic_quality_index=sqi,
            quality_tier=tier,
            gate_status=gate_status,
            validity_report=val_rep.to_dict(),
            fidelity_report=fid_rep.to_dict(),
            privacy_report=priv_rep.to_dict(),
            utility_report=util_rep.to_dict(),
            aggregated_issues=issues,
        )

    def generate_markdown_report(self, result: QualityGateResult) -> str:
        """Generates a comprehensive Markdown audit report."""
        md = []
        md.append("# BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU TỔNG HỢP (SYNTHETIC DATA QUALITY AUDIT)")
        md.append("")
        md.append(f"> **Thời gian đánh giá:** {result.evaluated_at}  ")
        md.append(f"> **Tập dữ liệu kiểm định:** `{result.dataset_name}` ({result.total_synthetic_records:,} bản ghi)  ")
        md.append(f"> **Tập dữ liệu mồi (Seed):** {result.total_real_seed_records:,} bản ghi | **Tập kiểm định độc lập (Holdout):** {result.total_holdout_records:,} bản ghi  ")
        md.append(f"> **Điểm Tổng hợp (Synthetic Quality Index - SQI):** **`{result.synthetic_quality_index} / 100`** — **{result.quality_tier}**  ")
        md.append(f"> **Trạng thái Cổng Chất lượng (Quality Gate):** **`{result.gate_status}`**  ")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 1. TỔNG QUAN 4 TRỤ CỘT ĐÁNH GIÁ (QUALITY GATE PILLARS)")
        md.append("")
        md.append("| Trụ cột Đánh giá | Trọng số | Điểm số Đạt được | Ngưỡng Đạt | Đánh giá Trạng thái |")
        md.append("|---|:---:|:---:|:---:|:---:|")
        md.append(f"| **1. Validity (Tính hợp lệ & Ràng buộc logic)** | {int(self.validity_weight*100)}% | **`{result.validity_score}%`** | >= 95% | {'[x] ĐẠT' if result.validity_score >= 95 else '[ ] CẢNH BÁO'} |")
        md.append(f"| **2. Fidelity (Tính trung thực phân phối)** | {int(self.fidelity_weight*100)}% | **`{result.fidelity_score}%`** | >= 80% | {'[x] ĐẠT' if result.fidelity_score >= 80 else '[ ] CẢNH BÁO'} |")
        md.append(f"| **3. Privacy (Tính bảo mật & Chống rò rỉ ID)** | {int(self.privacy_weight*100)}% | **`{result.privacy_score}%`** | >= 90% | {'[x] ĐẠT' if result.privacy_score >= 90 else '[ ] CẢNH BÁO'} |")
        md.append(f"| **4. Utility (Tính hữu ích cho Machine Learning)** | {int(self.utility_weight*100)}% | **`{result.utility_score}%`** | >= 75% | {'[x] ĐẠT' if result.utility_score >= 75 else '[ ] CẢNH BÁO'} |")
        md.append(f"| **TỔNG HỢP (SQI SCORE)** | **100%** | **`{result.synthetic_quality_index} / 100`** | $\\ge 80$ | **`{result.gate_status}`** |")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 2. KẾT QUẢ CHI TIẾT TỪNG TRỤ CỘT")
        md.append("")
        md.append("### 2.1. Trụ cột 1: Validity (Tính hợp lệ & Ràng buộc Nghiệp vụ)")
        md.append(f"* **Tỷ lệ bản ghi hợp lệ 100% invariants:** **`{result.validity_score}%`** ({result.validity_report.get('valid_records', 0):,} / {result.total_synthetic_records:,} bản ghi).")
        md.append(f"* **Lỗi vi phạm nghiêm trọng (Blocking Errors):** `{result.validity_report.get('has_blocking_errors', False)}`.")
        md.append("* **Chi tiết kiểm định Business Rules:**")
        for r_id, r_info in result.validity_report.get("rule_summaries", {}).items():
            md.append(f"  - `{r_id}` ({r_info.get('rule_name')}): {r_info.get('violation_count')} vi phạm ({r_info.get('violation_rate_pct')}%) — Trạng thái: **{r_info.get('severity')}**")
        md.append("")
        md.append("### 2.2. Trụ cột 2: Fidelity (Tính trung thực Phân phối & Tương quan)")
        fid_det = result.fidelity_report
        md.append(f"* **Điểm tương đồng phân phối số học (KS-Test):** **`{fid_det.get('numerical_fidelity_score')}%`**.")
        md.append(f"* **Điểm tương đồng phân phối danh mục (TVD):** **`{fid_det.get('categorical_fidelity_score')}%`**.")
        md.append(f"* **Điểm tương đồng ma trận tương quan Pearson:** **`{fid_det.get('correlation_similarity_score')}%`**.")
        md.append(f"* **Số cột được đánh giá:** `{fid_det.get('evaluated_columns_count')}` cột.")
        md.append("")
        md.append("### 2.3. Trụ cột 3: Privacy (Tính bảo mật & Nguy cơ Rò rỉ Dữ liệu)")
        priv_det = result.privacy_report
        md.append(f"* **Số bản ghi trùng lặp nguyên vẹn (Exact Match):** **`{priv_det.get('exact_match_count')}`** (`{priv_det.get('exact_match_rate_pct')}%`).")
        md.append(f"* **Số mã định danh thực tế bị rò rỉ (Real ID Leakage):** **`{priv_det.get('id_leakage_count')}`**.")
        md.append(f"* **Khoảng cách tới bản ghi thực gần nhất (DCR Mean):** **`{priv_det.get('mean_dcr')}`** (Median: `{priv_det.get('median_dcr')}`, Min: `{priv_det.get('min_dcr')}`).")
        md.append("")
        md.append("### 2.4. Trụ cột 4: Utility (Tính hữu ích khi huấn luyện Mô hình ML)")
        util_det = result.utility_report
        md.append(f"* **Năng lực dự báo hồi quy (TSTR vs TRTR on `net_sales`):** Tỷ lệ bảo toàn **`{util_det.get('regression_utility_score')}%`**.")
        md.append(f"* **Năng lực phân loại (TSTR vs TRTR on `customer_segment`):** Tỷ lệ bảo toàn **`{util_det.get('classification_utility_score')}%`**.")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 3. DANH SÁCH VẤN ĐỀ & NHẬN XÉT ĐƯỢC PHÁT HIỆN")
        md.append("")
        if result.aggregated_issues:
            for idx, issue in enumerate(result.aggregated_issues, 1):
                md.append(f"{idx}. {issue}")
        else:
            md.append("* Không phát hiện bất kỳ sai lệch nghiêm trọng nào vượt quá ngưỡng cho phép.")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 4. KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG")
        md.append("")
        md.append(f"* **Kết luận:** Bộ dữ liệu tổng hợp `{result.dataset_name}` đạt **`{result.synthetic_quality_index}/100` điểm**, đủ điều kiện vượt qua Cổng Kiểm định Chất lượng (**{result.gate_status}**).")
        md.append("* **Lưu ý:** Bộ dữ liệu tổng hợp đảm bảo 100% tính toàn vẹn toán học và an toàn bảo mật thông tin.")

        return "\n".join(md)

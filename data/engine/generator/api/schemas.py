"""
Pydantic schemas for Synthetic Data Generator API endpoints.
Independent of authentication, user, or other backend models to prevent merge conflicts.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    n_records: int = Field(5000, ge=10, le=100000, description="Số lượng bản ghi cần sinh (10 đến 100,000)")
    scenario: str = Field("baseline", description="Loại kịch bản: baseline, holiday_peak, flash_sale, custom")
    start_date: Optional[str] = Field("2024-01-01", description="Ngày bắt đầu (YYYY-MM-DD)")
    end_date: Optional[str] = Field("2024-12-31", description="Ngày kết thúc (YYYY-MM-DD)")
    growth_rate: Optional[float] = Field(0.0, description="Hệ số tăng trưởng doanh số (vd: 0.2 là +20%)")
    export_csv: Optional[bool] = Field(False, description="Tùy chọn xuất file CSV trên đĩa server hay chỉ trả in-memory")


class GenerateResponse(BaseModel):
    status: str = Field("SUCCESS", description="Trạng thái sinh dữ liệu")
    total_records: int = Field(..., description="Tổng số bản ghi sinh ra")
    total_columns: int = Field(38, description="Tổng số cột chuẩn")
    elapsed_seconds: float = Field(..., description="Thời gian thực thi (giây)")
    pass_rate_pct: float = Field(..., description="Tỷ lệ tuân thủ quy tắc nghiệp vụ (%)")
    summary_kpis: Dict[str, float] = Field(..., description="Chỉ số KPI tài chính tổng quan")
    preview_data: List[Dict[str, Any]] = Field(..., description="Dữ liệu mẫu 20 dòng đầu tiên")


class ScenarioItem(BaseModel):
    id: str
    name: str
    description: str
    default_growth_rate: float


class ScenarioListResponse(BaseModel):
    scenarios: List[ScenarioItem]


class QualityGateResponse(BaseModel):
    status: str
    sqi_score: float = Field(..., description="Synthetic Quality Index (0 - 100)")
    validity_pass_rate_pct: float
    fidelity_ks_score: float
    privacy_leakage_pct: float
    utility_tstr_score: float
    decision: str
    summary_message: str


class CompareDistributionResponse(BaseModel):
    column: str
    real_distribution: Dict[str, Any]
    synthetic_distribution: Dict[str, Any]


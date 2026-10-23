"""
Pydantic schemas for Synthetic Data Generator API endpoints.
Independent of authentication, user, or other backend models to prevent merge conflicts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class GenerateRequest(BaseModel):
    n_records: int = Field(5000, ge=10, le=100000, description="Số lượng bản ghi cần sinh (10 đến 100,000)")
    scenario: str = Field("baseline", description="Loại kịch bản: baseline, holiday_peak, flash_sale, high_growth, custom")
    start_date: Optional[str] = Field("2024-01-01", description="Ngày bắt đầu (YYYY-MM-DD)")
    end_date: Optional[str] = Field("2024-12-31", description="Ngày kết thúc (YYYY-MM-DD)")
    growth_rate: Optional[float] = Field(0.0, ge=-1.0, le=10.0, description="Hệ số tăng trưởng doanh số (vd: 0.2 là +20%, giới hạn -1.0 đến 10.0)")
    export_csv: Optional[bool] = Field(False, description="Tùy chọn xuất file CSV trên đĩa server hay chỉ trả in-memory")

    @model_validator(mode="after")
    def validate_date_logic(self):
        if self.start_date and self.end_date:
            try:
                d_start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("start_date format invalid, required YYYY-MM-DD")
            try:
                d_end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("end_date format invalid, required YYYY-MM-DD")
            if d_start > d_end:
                raise ValueError("start_date cannot be after end_date")
        return self


class GenerateResponse(BaseModel):
    status: str = Field("SUCCESS", description="Trạng thái sinh dữ liệu")
    total_records: int = Field(..., description="Tổng số bản ghi sinh ra")
    total_columns: int = Field(38, description="Tổng số cột chuẩn")
    elapsed_seconds: float = Field(..., description="Thời gian thực thi (giây)")
    pass_rate_pct: float = Field(..., description="Tỷ lệ tuân thủ quy tắc nghiệp vụ (%)")
    summary_kpis: Dict[str, float] = Field(..., description="Chỉ số KPI tài chính tổng quan")
    preview_data: List[Dict[str, Any]] = Field(..., description="Dữ liệu mẫu 20 dòng đầu tiên")
    export_filepath: Optional[str] = Field(None, description="Đường dẫn tệp CSV xuất ra trên server nếu export_csv=True")


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


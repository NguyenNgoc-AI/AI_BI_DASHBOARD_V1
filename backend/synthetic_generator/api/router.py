"""
FastAPI APIRouter for Synthetic Data Generator and Interactive Testing.
Fully modularized under /api/v1/synthetic.
"""

from datetime import datetime
import io
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.synthetic_generator.pipeline import SyntheticDataPipeline
from backend.synthetic_generator.validator import SyntheticDataQualityGate
from .schemas import (
    CompareDistributionResponse,
    GenerateRequest,
    GenerateResponse,
    QualityGateResponse,
    ScenarioItem,
    ScenarioListResponse,
)
from backend.config import (
    EXPORTS_DIR as EXPORT_DIR,
    HOLDOUT_DATA_PATH as HOLDOUT_PATH,
    PROFILE_PATH,
    SEED_DATA_PATH as SEED_PATH,
    SYNTHETIC_DATA_PATH as SYNTHETIC_PATH,
)

synthetic_router = APIRouter(
    prefix="/api/v1/synthetic",
    tags=["Synthetic Data & Interactive Testing"],
)


@synthetic_router.get("/scenarios", response_model=ScenarioListResponse)
def list_scenarios():
    """Danh sách các kịch bản mô phỏng kinh doanh hỗ trợ."""
    return ScenarioListResponse(
        scenarios=[
            ScenarioItem(
                id="baseline",
                name="Tiêu chuẩn (Baseline)",
                description="Mô phỏng phân phối kinh doanh bình thường dựa trên dữ liệu mồi thực tế.",
                default_growth_rate=0.0,
            ),
            ScenarioItem(
                id="holiday_peak",
                name="Mùa Mua Sắm Cuối Năm (Holiday Peak)",
                description="Tăng mạnh số lượng đơn, đẩy mạnh chiết khấu khuyến mãi và chi phí quảng cáo.",
                default_growth_rate=0.25,
            ),
            ScenarioItem(
                id="flash_sale",
                name="Siêu Hội Flash Sale",
                description="Đột biến số lượng đơn hàng theo giờ vàng, chiết khấu sâu, biên lợi nhuận thu hẹp.",
                default_growth_rate=0.40,
            ),
            ScenarioItem(
                id="high_growth",
                name="Kịch bản Mở Rộng Thị Trường (Scale-up)",
                description="Tăng trưởng lượng khách hàng doanh nghiệp và chi tiêu marketing đa kênh.",
                default_growth_rate=0.50,
            ),
        ]
    )


@synthetic_router.post("/generate", response_model=GenerateResponse)
def generate_synthetic_data(
    req: GenerateRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role", description="Vai trò người dùng (Admin, Data_Analyst, User, Guest)"),
):
    """
    Sinh tập dữ liệu tổng hợp theo tham số tùy chỉnh và trả về bản xem trước + KPI in-memory.
    Khi export_csv=True, file được lưu vào data/generated/exports/ để bảo vệ file chuẩn 50,000 dòng.
    """
    if x_user_role and x_user_role.lower() in ["guest", "unauthorized", "anonymous"]:
        raise HTTPException(
            status_code=403,
            detail="Truy cập bị từ chối: Vai trò người dùng không có quyền thực thi thao tác sinh dữ liệu.",
        )
    try:
        custom_output_path = None
        if req.export_csv:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            custom_output_path = EXPORT_DIR / f"synthetic_{req.scenario}_{timestamp}_{req.n_records}.csv"

        pipeline = SyntheticDataPipeline(
            profile_path=PROFILE_PATH,
            output_path=custom_output_path,
        )
        scenario_params = {
            "scenario": req.scenario,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "growth_rate": req.growth_rate,
        }

        result = pipeline.run(
            n_samples=req.n_records,
            scenario_params=scenario_params,
            export_csv=req.export_csv,
            enforce_rules=True,
        )

        df: pd.DataFrame = result["dataframe"]

        total_mkt = float(df["marketing_spend"].sum()) if "marketing_spend" in df.columns else 0.0
        total_net = float(df["net_sales"].sum()) if "net_sales" in df.columns else 0.0
        avg_roas = round(total_net / total_mkt, 2) if total_mkt > 0 else 0.0

        # Calculate high-level business KPIs
        summary_kpis = {
            "total_gross_sales": round(float(df["gross_sales"].sum()), 2),
            "total_net_sales": round(total_net, 2),
            "total_net_profit": round(float(df["net_profit"].sum()), 2),
            "avg_margin_rate": round(float(df["margin_rate"].mean() * 100), 2),
            "avg_roas": avg_roas,
            "total_orders": int(df["order_id"].nunique()),
            "total_customers": int(df["customer_id"].nunique()),
        }

        # Convert preview records
        preview_records = df.head(20).fillna("").to_dict(orient="records")

        return GenerateResponse(
            status="SUCCESS",
            total_records=len(df),
            total_columns=len(df.columns),
            elapsed_seconds=result["elapsed_seconds"],
            pass_rate_pct=result["pass_rate_pct"],
            summary_kpis=summary_kpis,
            preview_data=preview_records,
            export_filepath=str(custom_output_path) if custom_output_path else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh dữ liệu: {str(e)}")


@synthetic_router.post("/download-csv")
def download_synthetic_csv(req: GenerateRequest):
    """
    Sinh dữ liệu và stream trực tiếp tệp CSV về máy khách để tải xuống.
    """
    try:
        pipeline = SyntheticDataPipeline(profile_path=PROFILE_PATH)
        scenario_params = {
            "scenario": req.scenario,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "growth_rate": req.growth_rate,
        }

        result = pipeline.run(
            n_samples=req.n_records,
            scenario_params=scenario_params,
            export_csv=False,
            enforce_rules=True,
        )
        df: pd.DataFrame = result["dataframe"]

        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding="utf-8")
        stream.seek(0)

        filename = f"synthetic_ecommerce_{req.scenario}_{req.n_records}.csv"
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file CSV: {str(e)}")


@synthetic_router.get("/validate-benchmark", response_model=QualityGateResponse)
def get_benchmark_quality_gate():
    """
    Trả về kết quả kiểm định 4 tiêu chuẩn (Quality Gate) trên bộ dữ liệu tổng hợp chính thức.
    """
    if not (SEED_PATH.exists() and SYNTHETIC_PATH.exists() and HOLDOUT_PATH.exists()):
        raise HTTPException(status_code=404, detail="Không tìm thấy đầy đủ tệp seed, holdout hoặc synthetic.")

    gate = SyntheticDataQualityGate()
    syn_df = pd.read_csv(SYNTHETIC_PATH, nrows=3000)
    real_seed_df = pd.read_csv(SEED_PATH, nrows=3000)
    real_holdout_df = pd.read_csv(HOLDOUT_PATH, nrows=3000)

    result = gate.evaluate(
        syn_df=syn_df,
        real_seed_df=real_seed_df,
        real_holdout_df=real_holdout_df,
        dataset_name="synthetic_ecommerce_mock",
    )

    return QualityGateResponse(
        status=result.gate_status,
        sqi_score=round(result.synthetic_quality_index, 2),
        validity_pass_rate_pct=round(result.validity_score, 2),
        fidelity_ks_score=round(result.fidelity_score, 2),
        privacy_leakage_pct=round(100.0 - result.privacy_score, 2),
        utility_tstr_score=round(result.utility_score, 2),
        decision=f"ACCEPTED ({result.quality_tier})" if result.gate_status == "PASSED" else "WARNING",
        summary_message=f"SQI Score: {round(result.synthetic_quality_index, 2)}/100. Status: {result.gate_status}.",
    )


@synthetic_router.get("/compare-distribution", response_model=CompareDistributionResponse)
def compare_distribution(column: str = Query("net_sales", description="Tên cột số cần so sánh (vd: net_sales, unit_price, margin_rate)")):
    """
    So sánh thống kê phân phối (Min, Max, Mean, Std, Quantiles) giữa tập Real Seed và Synthetic.
    """
    if not (SEED_PATH.exists() and SYNTHETIC_PATH.exists()):
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu Seed hoặc Synthetic.")

    try:
        df_real = pd.read_csv(SEED_PATH, usecols=[column], nrows=10000)
        df_syn = pd.read_csv(SYNTHETIC_PATH, usecols=[column], nrows=10000)
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=400,
            detail=f"Cột '{column}' không tồn tại trong danh mục 38 thuộc tính của tập dữ liệu.",
        )

    s_real = pd.to_numeric(df_real[column], errors="coerce").dropna()
    s_syn = pd.to_numeric(df_syn[column], errors="coerce").dropna()

    if len(s_real) == 0 or len(s_syn) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cột '{column}' không chứa dữ liệu số học để tính toán phân phối thống kê.",
        )

    def extract_stats(s: pd.Series):
        return {
            "mean": round(float(s.mean()), 2),
            "std": round(float(s.std()), 2),
            "min": round(float(s.min()), 2),
            "p25": round(float(np.percentile(s, 25)), 2),
            "median": round(float(s.median()), 2),
            "p75": round(float(np.percentile(s, 75)), 2),
            "max": round(float(s.max()), 2),
        }

    return CompareDistributionResponse(
        column=column,
        real_distribution=extract_stats(s_real),
        synthetic_distribution=extract_stats(s_syn),
    )

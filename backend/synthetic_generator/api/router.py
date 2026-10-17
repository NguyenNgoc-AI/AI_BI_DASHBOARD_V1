"""
FastAPI APIRouter for Synthetic Data Generator and Interactive Testing.
Fully modularized under /api/v1/synthetic.
"""

import io
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
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

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROFILE_PATH = BASE_DIR / "data" / "generated" / "learned_seed_profile.json"
SEED_PATH = BASE_DIR / "data" / "sample_dataset" / "ecommerce_seed.csv"
HOLDOUT_PATH = BASE_DIR / "data" / "warehouse" / "real_holdout.csv"
SYNTHETIC_PATH = BASE_DIR / "data" / "generated" / "synthetic_ecommerce.csv"

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
def generate_synthetic_data(req: GenerateRequest):
    """
    Sinh tập dữ liệu tổng hợp theo tham số tùy chỉnh và trả về bản xem trước + KPI in-memory.
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

    df_real = pd.read_csv(SEED_PATH, usecols=[column], nrows=10000)
    df_syn = pd.read_csv(SYNTHETIC_PATH, usecols=[column], nrows=10000)

    def extract_stats(series: pd.Series):
        s = pd.to_numeric(series, errors="coerce").dropna()
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
        real_distribution=extract_stats(df_real[column]),
        synthetic_distribution=extract_stats(df_syn[column]),
    )

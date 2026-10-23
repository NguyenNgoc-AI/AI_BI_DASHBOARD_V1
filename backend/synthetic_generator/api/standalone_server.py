"""
Standalone FastAPI Runner for Synthetic Data Interactive Testing & Demo.
Can run completely independently without requiring backend/main.py or auth modules.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .router import synthetic_router

tags_metadata = [
    {
        "name": "System Health & Service Discovery",
        "description": "Kiểm tra tính sẵn sàng (Smoke Test / Health Check) và danh mục endpoint của hệ thống.",
    },
    {
        "name": "Synthetic Data & Interactive Testing",
        "description": "Các endpoint sinh dữ liệu tổng hợp, mô phỏng kịch bản và thẩm định chất lượng.",
    },
]

app = FastAPI(
    title="AI BI Dashboard - Synthetic Data Generator & Interactive Testing API",
    description="Dedicated API service for interactive data generation, scenario simulation, and quality gate validation.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# Enable CORS for local Streamlit / Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["System Health & Service Discovery"],
    summary="Health Check & Service Discovery",
)
def health_check():
    """Kiểm tra tính sẵn sàng của server và liệt kê toàn bộ các endpoint khả dụng."""
    return {
        "service": "Synthetic Data Generator API",
        "status": "ONLINE",
        "interactive_docs": "/docs",
        "endpoints": {
            "scenarios": "/api/v1/synthetic/scenarios",
            "generate": "/api/v1/synthetic/generate",
            "download_csv": "/api/v1/synthetic/download-csv",
            "validate_benchmark": "/api/v1/synthetic/validate-benchmark",
            "compare_distribution": "/api/v1/synthetic/compare-distribution",
        },
    }


# Register synthetic router after health check
app.include_router(synthetic_router)


def start():
    uvicorn.run("backend.synthetic_generator.api.standalone_server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start()

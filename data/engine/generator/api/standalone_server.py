"""
Standalone FastAPI Runner for Synthetic Data Interactive Testing & Demo.
Can run completely independently without requiring backend/main.py or auth modules.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .router import synthetic_router

app = FastAPI(
    title="AI BI Dashboard - Synthetic Data Generator & Interactive Testing API",
    description="Dedicated API service for interactive data generation, scenario simulation, and quality gate validation.",
    version="1.0.0",
)

# Enable CORS for local Streamlit / Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(synthetic_router)


@app.get("/")
def health_check():
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


def start():
    uvicorn.run("backend.synthetic_generator.api.standalone_server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    start()


"""FastAPI composition root. Business logic stays in dedicated modules."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from time import perf_counter
import uuid

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.auth import authenticate_user, create_access_token, create_user, decode_access_token, ensure_admin_user, init_auth_db, role_allowed, update_user_role
from backend.chatbot.llm_router import LLMRouter
from backend.chatbot.rag_engine import answer_dashboard_question, build_dashboard_context
from backend.chatbot.text_to_sql import question_to_sql, validate_select_sql
from backend.config import settings
from backend.dashboard_engine.chart_generator import generate_charts
from backend.dashboard_engine.data_pipeline import coerce_ecommerce_types, ingest, validate_required_columns
from backend.dashboard_engine.kpi_calculator import calculate_kpis
from backend.dashboard_engine.report_exporter import build_report_payload, export_report
from backend.eda.profiling import profile_dataset
from backend.eda.quality_checker import check_quality
from backend.schema_learning.schema_extractor import infer_database_schema, infer_schema
from backend.synthetic_generator.pipeline import generate_synthetic_dataset
from backend.synthetic_generator.validator import validate_synthetic


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_auth_db()
    ensure_admin_user(settings.bootstrap_admin_username, settings.bootstrap_admin_password)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Filename", "X-Request-ID"],
)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)


class RoleRequest(BaseModel):
    role: str = Field(pattern="^(admin|manager|user)$")


class DatasetRequest(BaseModel):
    rows: list[dict]


class TablesRequest(BaseModel):
    tables: dict[str, list[dict]]


class SyntheticRequest(DatasetRequest):
    count: int = Field(ge=1, le=100_000)
    seed: int | None = None
    model: str = Field(default="bootstrap", pattern="^(bootstrap|gaussian_copula|ctgan|copulagan|llm_agent)$")
    target_column: str | None = None


class SyntheticValidationRequest(BaseModel):
    original_rows: list[dict]
    synthetic_rows: list[dict]
    target_column: str | None = None


class ChatRequest(DatasetRequest):
    question: str = Field(min_length=1, max_length=2_000)


def _error(code: str, message: str, request_id: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}, "request_id": request_id}}


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_upload_bytes:
                return JSONResponse(_error("PAYLOAD_TOO_LARGE", "Request body is too large", request_id), status_code=413)
        except ValueError:
            return JSONResponse(_error("INVALID_CONTENT_LENGTH", "Content-Length must be an integer", request_id), status_code=400)
    started = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{perf_counter() - started:.6f}"
    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, error: ValueError):
    return JSONResponse(_error("INVALID_REQUEST", str(error), request.state.request_id), status_code=400)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, _error_value: Exception):
    # Do not expose tracebacks, SQL, paths, secrets or provider errors to clients.
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(_error("INTERNAL_ERROR", "An unexpected error occurred", request_id), status_code=500)


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return decode_access_token(authorization.removeprefix("Bearer ").strip())
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


def manager_or_admin(user: dict = Depends(current_user)) -> dict:
    if not role_allowed(user, "manager", "admin"):
        raise HTTPException(status_code=403, detail="Manager or admin role required")
    return user


def admin_only(user: dict = Depends(current_user)) -> dict:
    if not role_allowed(user, "admin"):
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def analyze(rows: list[dict]) -> dict:
    schema = infer_schema(rows)
    profile = profile_dataset(rows)
    quality = check_quality(rows)
    kpis = calculate_kpis(rows)
    charts = generate_charts(rows)
    return {
        "dataset": {"rows": len(rows), "columns": len(schema["columns"])},
        "schema": schema,
        "profile": profile,
        "quality": quality,
        "kpis": kpis,
        "charts": charts,
    }


def canonical_rows(rows: list[dict]) -> list[dict]:
    validate_required_columns(rows)
    return coerce_ecommerce_types(rows)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials) -> dict:
    return create_user(credentials.username, credentials.password)


@app.post("/auth/login")
def login(credentials: Credentials) -> dict:
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": create_access_token(user), "token_type": "bearer", "expires_in": settings.jwt_exp_minutes * 60}


@app.get("/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {key: user[key] for key in ("sub", "username", "role")}


@app.post("/auth/users/{user_id}/role")
def change_user_role(user_id: int, payload: RoleRequest, _admin: dict = Depends(admin_only)) -> dict:
    if not update_user_role(user_id, payload.role):
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "role": payload.role}


@app.post("/datasets/analyze")
async def analyze_upload(
    request: Request,
    filename: str = Query(..., min_length=5, max_length=255),
    _user: dict = Depends(current_user),
) -> dict:
    content = await request.body()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File is too large")
    return analyze(ingest(content, filename, settings.max_rows))


@app.post("/datasets/profile")
def dataset_profile(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return profile_dataset(canonical_rows(payload.rows))


@app.post("/datasets/quality")
def dataset_quality(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return check_quality(canonical_rows(payload.rows))


@app.post("/datasets/schema")
def dataset_schema(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return infer_schema(canonical_rows(payload.rows))


@app.post("/schema/infer-relations")
def schema_relations(payload: TablesRequest, _user: dict = Depends(current_user)) -> dict:
    return infer_database_schema(payload.tables)


@app.post("/dashboard/kpis")
def dashboard_kpis(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return calculate_kpis(canonical_rows(payload.rows))


@app.post("/dashboard/charts")
def dashboard_charts(payload: DatasetRequest, _user: dict = Depends(current_user)) -> list[dict]:
    return generate_charts(canonical_rows(payload.rows))


@app.post("/synthetic/generate")
def synthetic_generate(payload: SyntheticRequest, _user: dict = Depends(manager_or_admin)) -> dict:
    llm = None
    if payload.model == "llm_agent":
        if settings.llm_provider == "deterministic":
            raise ValueError("llm_agent requires LLM_PROVIDER=openai, gemini or llama")
        llm = LLMRouter()
    return generate_synthetic_dataset(
        canonical_rows(payload.rows), payload.count, payload.seed, payload.model, payload.target_column, llm
    )


@app.post("/synthetic/validate")
def synthetic_validate(payload: SyntheticValidationRequest, _user: dict = Depends(manager_or_admin)) -> dict:
    original = canonical_rows(payload.original_rows)
    synthetic = canonical_rows(payload.synthetic_rows)
    return validate_synthetic(original, synthetic, infer_schema(original), payload.target_column)


@app.post("/chat/query")
def chat_query(payload: ChatRequest, _user: dict = Depends(current_user)) -> dict:
    analysis = analyze(canonical_rows(payload.rows))
    context = build_dashboard_context(analysis["schema"], analysis["profile"], analysis["quality"], analysis["kpis"], analysis["charts"])
    return answer_dashboard_question(payload.question, context, LLMRouter())


@app.post("/chat/sql")
def chat_sql(payload: ChatRequest, _user: dict = Depends(current_user)) -> dict[str, str | None]:
    schema = infer_schema(canonical_rows(payload.rows))
    router = LLMRouter()
    sql = question_to_sql(payload.question, schema, router if settings.llm_provider != "deterministic" else None)
    return {
        "sql": validate_select_sql(sql, {"sales"}, set(schema["columns"])),
        "provider": router.used_provider,
        "fallback_reason": router.fallback_reason,
    }


@app.post("/reports/export")
def reports_export(
    payload: DatasetRequest,
    format: str = Query("json", pattern="^[a-z]+$"),
    _user: dict = Depends(current_user),
) -> Response:
    analysis = analyze(canonical_rows(payload.rows))
    report = build_report_payload(analysis["profile"], analysis["quality"], analysis["kpis"], analysis["charts"])
    content, media_type = export_report(report, format)
    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="report.{format}"'})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("API_HOST", "127.0.0.1"), port=int(os.getenv("API_PORT", "8000")))

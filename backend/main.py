"""FastAPI composition root. Business logic stays in dedicated modules."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Annotated
import uuid

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Response, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from backend.auth import (
    activate_user,
    authenticate_user,
    create_access_token,
    decode_access_token,
    ensure_admin_user,
    get_registration_request,
    get_user_by_id,
    init_auth_db,
    list_registration_requests,
    provision_user,
    review_registration,
    role_allowed,
    submit_registration,
    update_user_role,
)
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


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(StrictModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)


class RegistrationRequest(StrictModel):
    employee_id: str = Field(min_length=3, max_length=32)
    full_name: str = Field(min_length=1, max_length=128)
    position: str = Field(min_length=1, max_length=128)
    department: str = Field(min_length=1, max_length=128)


class RegistrationResponse(StrictModel):
    id: int
    employee_id: str
    status: str


class ReviewRequest(StrictModel):
    rejection_reason: str | None = Field(default=None, max_length=500)


class ProvisionRequest(StrictModel):
    registration_request_id: int = Field(gt=0)
    temporary_password: str = Field(min_length=8, max_length=256)
    role: str = Field(pattern="^(admin|manager|user)$")
    permissions: list[str] = Field(min_length=1)
    data_scope: str = Field(pattern="^(own|department|all)$")


class ActivationRequest(StrictModel):
    new_password: str = Field(min_length=8, max_length=256)
    confirm_password: str = Field(min_length=8, max_length=256)


class RoleRequest(StrictModel):
    role: str = Field(pattern="^(admin|manager|user)$")


class DatasetRequest(StrictModel):
    rows: list[dict[str, JsonValue]]


class TablesRequest(StrictModel):
    tables: dict[str, list[dict[str, JsonValue]]]


class SyntheticRequest(DatasetRequest):
    count: int = Field(ge=1, le=100_000)
    seed: int | None = None
    model: str = Field(default="bootstrap", pattern="^(bootstrap|gaussian_copula|ctgan|copulagan|llm_agent)$")
    target_column: str | None = None


class SyntheticValidationRequest(StrictModel):
    original_rows: list[dict[str, JsonValue]]
    synthetic_rows: list[dict[str, JsonValue]]
    target_column: str | None = None


class ChatRequest(DatasetRequest):
    question: str = Field(min_length=1, max_length=2_000)


class HealthResponse(StrictModel):
    status: str
    version: str


class RootResponse(StrictModel):
    name: str
    version: str
    health: str
    docs: str


class UserResponse(StrictModel):
    id: int
    username: str
    role: str
    employee_id: str | None = None
    status: str
    permissions: list[str]
    data_scope: str


class TokenResponse(StrictModel):
    access_token: str
    token_type: str
    expires_in: int
    purpose: str


class CurrentUserResponse(StrictModel):
    sub: str
    username: str
    role: str
    employee_id: str | None
    status: str
    permissions: list[str]
    data_scope: str


class RoleResponse(StrictModel):
    id: int
    role: str


class ProfileResponse(StrictModel):
    row_count: int
    columns: dict[str, dict[str, JsonValue]]


class QualityResponse(StrictModel):
    score: float
    valid: dict[str, JsonValue]
    missing: dict[str, JsonValue]
    duplicates: dict[str, JsonValue]
    outliers: dict[str, JsonValue]


class SchemaResponse(StrictModel):
    columns: dict[str, dict[str, JsonValue]]
    relationships: list[dict[str, JsonValue]]


class KpiResponse(StrictModel):
    total_revenue: float
    total_cost: float
    net_profit: float
    order_count: int
    average_order_value: float
    cac: float | None
    roas: float | None
    ltv: float | None


class AnalysisResponse(StrictModel):
    dataset: dict[str, JsonValue]
    schema_definition: SchemaResponse = Field(alias="schema")
    profile: ProfileResponse
    quality: QualityResponse
    kpis: KpiResponse
    charts: list[dict[str, JsonValue]]


class RelationsResponse(StrictModel):
    tables: dict[str, SchemaResponse]
    primary_key_candidates: dict[str, list[str]]
    foreign_keys: list[dict[str, JsonValue]]


class SyntheticResponse(StrictModel):
    model: str
    rows: list[dict[str, JsonValue]]
    validation: dict[str, JsonValue]


class SyntheticValidationResponse(StrictModel):
    validity: float
    fidelity: float
    privacy: float
    utility: float
    details: dict[str, JsonValue]


class ChatResponse(StrictModel):
    answer: str
    source: str
    provider: str | None
    fallback_reason: str | None


class SqlResponse(StrictModel):
    sql: str
    provider: str | None
    fallback_reason: str | None


AUTH_RESPONSES = {401: {"description": "Missing or invalid bearer token"}}
RBAC_RESPONSES = {**AUTH_RESPONSES, 403: {"description": "Insufficient role"}}
DATA_RESPONSES = {
    **AUTH_RESPONSES,
    400: {"description": "Invalid dataset or request"},
    413: {"description": "Payload too large"},
}
bearer_scheme = HTTPBearer(auto_error=False, description="JWT returned by POST /auth/login")


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


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        claims = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user = get_user_by_id(int(claims["sub"]))
    if not user or user["status"] != "ACTIVE" or user["token_version"] != claims["ver"]:
        raise HTTPException(status_code=401, detail="Account or token is no longer active")
    return {**claims, **user, "sub": claims["sub"]}


def activation_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing activation token")
    try:
        claims = decode_access_token(credentials.credentials, "activation")
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user = get_user_by_id(int(claims["sub"]))
    if not user or user["status"] != "PENDING_ACTIVATION" or user["token_version"] != claims["ver"]:
        raise HTTPException(status_code=401, detail="Activation token is no longer valid")
    return user


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


@app.get("/", response_model=RootResponse)
def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": "0.1.0", "health": "/health", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post(
    "/auth/register-request",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
    responses={400: {"description": "Invalid or duplicate registration request"}},
)
def register_request(payload: RegistrationRequest) -> dict:
    return submit_registration(payload.model_dump())


@app.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
    deprecated=True,
    responses={400: {"description": "Invalid or duplicate registration request"}},
)
def legacy_register_alias(payload: RegistrationRequest) -> dict:
    """Compatibility alias; it no longer accepts a username, password or role."""
    return submit_registration(payload.model_dump())


@app.post("/auth/login", response_model=TokenResponse, responses={401: {"description": "Invalid credentials"}})
def login(credentials: Credentials) -> dict:
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user["status"] == "DISABLED":
        raise HTTPException(status_code=403, detail="Account is disabled")
    if user["status"] == "PENDING_ACTIVATION":
        return {
            "access_token": create_access_token(user, token_type="activation"),
            "token_type": "bearer",
            "expires_in": 600,
            "purpose": "activation",
        }
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": settings.jwt_exp_minutes * 60,
        "purpose": "access",
    }


@app.post("/auth/activate", status_code=status.HTTP_204_NO_CONTENT, responses=AUTH_RESPONSES)
def activate(payload: ActivationRequest, user: dict = Depends(activation_user)) -> Response:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    if not activate_user(user["id"], payload.new_password):
        raise HTTPException(status_code=409, detail="Account is no longer pending activation")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/auth/me", response_model=CurrentUserResponse, responses=AUTH_RESPONSES)
def me(user: dict = Depends(current_user)) -> dict:
    return {key: user[key] for key in (
        "sub", "username", "role", "employee_id", "status", "permissions", "data_scope"
    )}


@app.get("/admin/registration-requests", responses=RBAC_RESPONSES)
def registration_requests(
    request_status: str | None = Query(default=None, pattern="^(PENDING|APPROVED|REJECTED)$", alias="status"),
    _admin: dict = Depends(admin_only),
) -> list[dict]:
    return list_registration_requests(request_status)


@app.get("/admin/registration-requests/{request_id}", responses={**RBAC_RESPONSES, 404: {"description": "Not found"}})
def registration_request_detail(request_id: int, _admin: dict = Depends(admin_only)) -> dict:
    request_row = get_registration_request(request_id)
    if not request_row:
        raise HTTPException(status_code=404, detail="Registration request not found")
    return request_row


@app.post("/admin/registration-requests/{request_id}/approve", responses={**RBAC_RESPONSES, 404: {}, 409: {}})
def approve_registration(request_id: int, _payload: ReviewRequest, admin: dict = Depends(admin_only)) -> dict:
    existing = get_registration_request(request_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Registration request not found")
    reviewed = review_registration(request_id, admin["id"], "APPROVED")
    if not reviewed:
        raise HTTPException(status_code=409, detail="Registration request was already reviewed")
    return reviewed


@app.post("/admin/registration-requests/{request_id}/reject", responses={**RBAC_RESPONSES, 404: {}, 409: {}})
def reject_registration(request_id: int, payload: ReviewRequest, admin: dict = Depends(admin_only)) -> dict:
    existing = get_registration_request(request_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Registration request not found")
    if existing["status"] != "PENDING":
        raise HTTPException(status_code=409, detail="Registration request was already reviewed")
    try:
        reviewed = review_registration(request_id, admin["id"], "REJECTED", payload.rejection_reason)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return reviewed


@app.post("/admin/users/provision", status_code=status.HTTP_201_CREATED, response_model=UserResponse, responses=RBAC_RESPONSES)
def provision(payload: ProvisionRequest, admin: dict = Depends(admin_only)) -> dict:
    try:
        user = provision_user(
            payload.registration_request_id,
            payload.temporary_password,
            payload.role,
            payload.permissions,
            payload.data_scope,
            admin["id"],
        )
        return {key: user[key] for key in (
            "id", "username", "role", "employee_id", "status", "permissions", "data_scope"
        )}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post(
    "/auth/users/{user_id}/role",
    response_model=RoleResponse,
    responses={**RBAC_RESPONSES, 404: {"description": "User not found"}},
)
def change_user_role(user_id: int, payload: RoleRequest, _admin: dict = Depends(admin_only)) -> dict:
    if not update_user_role(user_id, payload.role):
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "role": payload.role}


@app.post("/datasets/analyze", response_model=AnalysisResponse, responses=DATA_RESPONSES)
def analyze_upload(
    content: Annotated[
        bytes,
        Body(
            media_type="application/octet-stream",
            description="Raw UTF-8 CSV or JSON bytes. The filename extension selects the parser.",
        ),
    ],
    filename: str = Query(..., min_length=5, max_length=255),
    _user: dict = Depends(current_user),
) -> dict:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File is too large")
    return analyze(ingest(content, filename, settings.max_rows))


@app.post("/datasets/profile", response_model=ProfileResponse, responses=DATA_RESPONSES)
def dataset_profile(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return profile_dataset(canonical_rows(payload.rows))


@app.post("/datasets/quality", response_model=QualityResponse, responses=DATA_RESPONSES)
def dataset_quality(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return check_quality(canonical_rows(payload.rows))


@app.post("/datasets/schema", response_model=SchemaResponse, responses=DATA_RESPONSES)
def dataset_schema(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return infer_schema(canonical_rows(payload.rows))


@app.post(
    "/schema/infer-relations",
    response_model=RelationsResponse,
    responses={**AUTH_RESPONSES, 400: {"description": "Invalid tables"}},
)
def schema_relations(payload: TablesRequest, _user: dict = Depends(current_user)) -> dict:
    return infer_database_schema(payload.tables)


@app.post("/dashboard/kpis", response_model=KpiResponse, responses=DATA_RESPONSES)
def dashboard_kpis(payload: DatasetRequest, _user: dict = Depends(current_user)) -> dict:
    return calculate_kpis(canonical_rows(payload.rows))


@app.post("/dashboard/charts", response_model=list[dict[str, JsonValue]], responses=DATA_RESPONSES)
def dashboard_charts(payload: DatasetRequest, _user: dict = Depends(current_user)) -> list[dict]:
    return generate_charts(canonical_rows(payload.rows))


@app.post(
    "/synthetic/generate",
    response_model=SyntheticResponse,
    responses={**RBAC_RESPONSES, 400: {"description": "Invalid generation request"}},
)
def synthetic_generate(payload: SyntheticRequest, _user: dict = Depends(manager_or_admin)) -> dict:
    llm = None
    if payload.model == "llm_agent":
        if settings.llm_provider == "deterministic":
            raise ValueError("llm_agent requires LLM_PROVIDER=openai, gemini or llama")
        llm = LLMRouter()
    return generate_synthetic_dataset(
        canonical_rows(payload.rows), payload.count, payload.seed, payload.model, payload.target_column, llm
    )


@app.post(
    "/synthetic/validate",
    response_model=SyntheticValidationResponse,
    responses={**RBAC_RESPONSES, 400: {"description": "Invalid validation request"}},
)
def synthetic_validate(payload: SyntheticValidationRequest, _user: dict = Depends(manager_or_admin)) -> dict:
    original = canonical_rows(payload.original_rows)
    synthetic = canonical_rows(payload.synthetic_rows)
    return validate_synthetic(original, synthetic, infer_schema(original), payload.target_column)


@app.post(
    "/chat/query",
    response_model=ChatResponse,
    responses={**AUTH_RESPONSES, 400: {"description": "Invalid chat request"}},
)
def chat_query(payload: ChatRequest, _user: dict = Depends(current_user)) -> dict:
    analysis = analyze(canonical_rows(payload.rows))
    context = build_dashboard_context(analysis["schema"], analysis["profile"], analysis["quality"], analysis["kpis"], analysis["charts"])
    return answer_dashboard_question(payload.question, context, LLMRouter())


@app.post(
    "/chat/sql",
    response_model=SqlResponse,
    responses={**AUTH_RESPONSES, 400: {"description": "Unsafe or invalid SQL request"}},
)
def chat_sql(payload: ChatRequest, _user: dict = Depends(current_user)) -> dict[str, str | None]:
    schema = infer_schema(canonical_rows(payload.rows))
    router = LLMRouter()
    sql = question_to_sql(payload.question, schema, router if settings.llm_provider != "deterministic" else None)
    return {
        "sql": validate_select_sql(sql, {"sales"}, set(schema["columns"])),
        "provider": router.used_provider,
        "fallback_reason": router.fallback_reason,
    }


@app.post(
    "/reports/export",
    responses={
        **AUTH_RESPONSES,
        400: {"description": "Invalid dataset or report format"},
        501: {"description": "Report dependency is unavailable"},
    },
)
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

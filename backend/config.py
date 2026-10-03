"""Environment configuration kept in one small, dependency-free module."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    jwt_secret: str
    jwt_exp_minutes: int
    database_path: str
    cors_origins: tuple[str, ...]
    max_upload_bytes: int
    max_rows: int
    llm_provider: str
    openai_api_key: str | None
    gemini_api_key: str | None
    llama_base_url: str | None
    openai_model: str
    gemini_model: str
    llama_model: str
    llm_timeout_seconds: float
    bootstrap_admin_username: str | None
    bootstrap_admin_password: str | None


def load_settings() -> Settings:
    environment = os.getenv("APP_ENV", "development").lower()
    secret = os.getenv("JWT_SECRET", "")
    if environment == "production" and len(secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters in production")
    if not secret:
        # Stable only for local development. Production is rejected above.
        secret = "development-only-change-me-32-chars"

    origins = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    return Settings(
        app_name=os.getenv("APP_NAME", "AI BI Dashboard API"),
        environment=environment,
        jwt_secret=secret,
        jwt_exp_minutes=int(os.getenv("JWT_EXP_MINUTES", "60")),
        database_path=os.getenv("DATABASE_PATH", str(Path("data") / "app_database.db")),
        cors_origins=origins,
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
        max_rows=int(os.getenv("MAX_ROWS", "100000")),
        llm_provider=os.getenv("LLM_PROVIDER", "deterministic").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        llama_base_url=os.getenv("LLAMA_BASE_URL") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        llama_model=os.getenv("LLAMA_MODEL", "llama"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        bootstrap_admin_username=os.getenv("ADMIN_USERNAME") or None,
        bootstrap_admin_password=os.getenv("ADMIN_PASSWORD") or None,
    )


settings = load_settings()

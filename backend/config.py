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


def _load_env_file(env_path: Path) -> None:
    """Read key-value pairs from a local .env file into os.environ without overriding."""
    if not env_path.is_file():
        return
    try:
        content = env_path.read_text(encoding="utf-8")
    except Exception:
        return
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def _persist_jwt_secret_to_env(env_path: Path, secret: str) -> None:
    """Persist generated secret into .env so local development maintains sessions across reloads."""
    try:
        if env_path.is_file():
            lines = env_path.read_text(encoding="utf-8").splitlines()
            replaced = False
            new_lines = []
            for line in lines:
                if line.strip().startswith("JWT_SECRET="):
                    new_lines.append(f"JWT_SECRET={secret}")
                    replaced = True
                else:
                    new_lines.append(line)
            if not replaced:
                new_lines.append(f"JWT_SECRET={secret}")
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        else:
            env_path.write_text(f"JWT_SECRET={secret}\n", encoding="utf-8")
    except Exception as error:
        print(f"[CONFIG] Warning: Could not persist JWT_SECRET to {env_path}: {error}")


def load_settings() -> Settings:
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / ".env"
    _load_env_file(env_path)

    environment = os.getenv("APP_ENV", "development").lower()
    secret = os.getenv("JWT_SECRET", "").strip()

    if environment == "production":
        if len(secret) < 32:
            raise RuntimeError("JWT_SECRET must contain at least 32 characters in production")
    else:
        if len(secret) < 32:
            import secrets
            secret = secrets.token_urlsafe(32)
            os.environ["JWT_SECRET"] = secret
            _persist_jwt_secret_to_env(env_path, secret)
            print(f"[CONFIG] Generated persistent local JWT_SECRET in {env_path.name}")

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
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024))),
        max_rows=int(os.getenv("MAX_ROWS", "500000")),
        llm_provider=os.getenv("LLM_PROVIDER", "deterministic").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        llama_base_url=os.getenv("LLAMA_BASE_URL") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        llama_model=os.getenv("LLM_MODEL", os.getenv("LLAMA_MODEL", "llama")),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        bootstrap_admin_username=os.getenv("ADMIN_USERNAME") or None,
        bootstrap_admin_password=os.getenv("ADMIN_PASSWORD") or None,
    )


settings = load_settings()

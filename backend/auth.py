"""SQLite users, PBKDF2 password hashing, signed JWT and RBAC helpers."""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
from typing import Any

from backend.config import settings

VALID_ROLES = {"admin", "manager", "user"}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")


def _connect(database_path: str | None = None) -> sqlite3.Connection:
    path = database_path or settings.database_path
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db(database_path: str | None = None) -> None:
    connection = _connect(database_path)
    try:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'user')),
                created_at TEXT NOT NULL
            )"""
        )
        connection.commit()
    finally:
        connection.close()


def hash_password(password: str) -> str:
    if len(password) < 8 or len(password) > 256:
        raise ValueError("Password must contain 8 to 256 characters")
    salt = secrets.token_bytes(16)
    rounds = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    return f"pbkdf2_sha256${rounds}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(rounds))
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


def create_user(username: str, password: str, database_path: str | None = None) -> dict[str, Any]:
    username = username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-64 letters, digits, dots, dashes or underscores")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        cursor = connection.execute(
            "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, 'user', ?)",
            (username, hash_password(password), datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
        return {"id": cursor.lastrowid, "username": username, "role": "user"}
    except sqlite3.IntegrityError as error:
        raise ValueError("Username already exists") from error
    finally:
        connection.close()


def ensure_admin_user(username: str | None, password: str | None, database_path: str | None = None) -> None:
    if not username and not password:
        return
    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be configured together")
    if not USERNAME_PATTERN.fullmatch(username.strip()):
        raise RuntimeError("ADMIN_USERNAME is invalid")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        existing = connection.execute("SELECT id FROM users WHERE username = ?", (username.strip(),)).fetchone()
        if not existing:
            connection.execute(
                "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
                (username.strip(), hash_password(password), datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()
    finally:
        connection.close()


def authenticate_user(username: str, password: str, database_path: str | None = None) -> dict[str, Any] | None:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        connection.close()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def update_user_role(user_id: int, role: str, database_path: str | None = None) -> bool:
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")
    connection = _connect(database_path)
    try:
        cursor = connection.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    if _b64(decoded) != value:
        raise ValueError("Non-canonical base64url")
    return decoded


def create_access_token(user: dict[str, Any], expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes or settings.jwt_exp_minutes)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    body = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
        header = json.loads(_unb64(header_part))
        if header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("Unsupported JWT header")
        body = f"{header_part}.{payload_part}"
        expected = hmac.new(settings.jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature_part)):
            raise ValueError("Invalid token signature")
        payload = json.loads(_unb64(payload_part))
        if int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Token has expired")
        if payload.get("role") not in VALID_ROLES:
            raise ValueError("Invalid token role")
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Invalid access token") from error


def role_allowed(user: dict[str, Any], *roles: str) -> bool:
    return user.get("role") in roles

"""Authentication workflow: registration review, provisioning, activation and JWTs."""

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
VALID_SCOPES = {"own", "department", "all"}
VALID_PERMISSIONS = {
    "dashboard:view", "dataset:upload", "dataset:view", "kpi:view", "chart:view",
    "synthetic:generate", "chat:use", "report:view", "report:export", "user:manage",
}
ROLE_PERMISSIONS = {
    "user": {"dashboard:view", "dataset:upload", "dataset:view", "kpi:view", "chart:view", "chat:use", "report:view"},
    "manager": VALID_PERMISSIONS - {"user:manage"},
    "admin": VALID_PERMISSIONS,
}
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Z0-9_-]{3,32}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: str | None = None) -> sqlite3.Connection:
    path = database_path or settings.database_path
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}


def _default_scope(role: str) -> str:
    return {"user": "own", "manager": "department", "admin": "all"}[role]


def _default_permissions(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS[role])


def init_auth_db(database_path: str | None = None) -> None:
    """Create the auth schema and migrate the original users table in place."""
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
        additions = {
            "employee_id": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'ACTIVE'",
            "permissions_json": "TEXT NOT NULL DEFAULT '[]'",
            "data_scope": "TEXT NOT NULL DEFAULT 'own'",
            "registration_request_id": "INTEGER",
            "token_version": "INTEGER NOT NULL DEFAULT 0",
            "activated_at": "TEXT",
        }
        existing = _columns(connection, "users")
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")

        connection.executescript(
            """CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL,
                department TEXT NOT NULL,
                is_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS registration_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL,
                department TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
                reviewed_by INTEGER,
                reviewed_at TEXT,
                rejection_reason TEXT,
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_registration
                ON registration_requests(employee_id) WHERE status = 'PENDING';
            CREATE UNIQUE INDEX IF NOT EXISTS uq_users_employee_id
                ON users(employee_id) WHERE employee_id IS NOT NULL;
            CREATE UNIQUE INDEX IF NOT EXISTS uq_users_registration_request
                ON users(registration_request_id) WHERE registration_request_id IS NOT NULL;
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_user_id INTEGER,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );"""
        )
        rows = connection.execute("SELECT id, role, permissions_json, data_scope FROM users").fetchall()
        for row in rows:
            permissions = row["permissions_json"]
            if "permissions_json" not in existing or not permissions or permissions == "[]":
                permissions = json.dumps(_default_permissions(row["role"]))
            scope = _default_scope(row["role"]) if "data_scope" not in existing else (row["data_scope"] or _default_scope(row["role"]))
            connection.execute(
                "UPDATE users SET status = COALESCE(status, 'ACTIVE'), permissions_json = ?, data_scope = ? WHERE id = ?",
                (permissions, scope, row["id"]),
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


def _user_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "username": row["username"], "employee_id": row["employee_id"],
        "role": row["role"], "status": row["status"],
        "permissions": json.loads(row["permissions_json"]), "data_scope": row["data_scope"],
        "token_version": row["token_version"],
    }


def create_user(
    username: str,
    password: str,
    database_path: str | None = None,
    *,
    role: str = "user",
    status: str = "ACTIVE",
    employee_id: str | None = None,
) -> dict[str, Any]:
    """Internal account helper. Public registration never calls this function."""
    username = username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-64 letters, digits, dots, dashes or underscores")
    if role not in VALID_ROLES or status not in {"PENDING_ACTIVATION", "ACTIVE", "DISABLED"}:
        raise ValueError("Invalid role or account status")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        cursor = connection.execute(
            """INSERT INTO users(
                username, password_hash, role, created_at, employee_id, status,
                permissions_json, data_scope, activated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, hash_password(password), role, _now(), employee_id, status,
             json.dumps(_default_permissions(role)), _default_scope(role), _now() if status == "ACTIVE" else None),
        )
        connection.commit()
        return get_user_by_id(cursor.lastrowid, database_path)
    except sqlite3.IntegrityError as error:
        raise ValueError("Username or employee ID already exists") from error
    finally:
        connection.close()


def ensure_admin_user(username: str | None, password: str | None, database_path: str | None = None) -> None:
    if not username and not password:
        return
    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be configured together")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        existing = connection.execute("SELECT id FROM users WHERE username = ?", (username.strip(),)).fetchone()
    finally:
        connection.close()
    if not existing:
        create_user(username, password, database_path, role="admin")


def get_user_by_id(user_id: int, database_path: str | None = None) -> dict[str, Any] | None:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user_dict(row) if row else None
    finally:
        connection.close()


def authenticate_user(username: str, password: str, database_path: str | None = None) -> dict[str, Any] | None:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    finally:
        connection.close()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return _user_dict(row)


def submit_registration(data: dict[str, str], database_path: str | None = None) -> dict[str, Any]:
    employee_id = data["employee_id"].strip().upper()
    if not EMPLOYEE_ID_PATTERN.fullmatch(employee_id):
        raise ValueError("Employee ID must contain 3-32 uppercase letters, digits, dashes or underscores")
    clean = {key: data[key].strip() for key in ("full_name", "position", "department")}
    if any(not value for value in clean.values()):
        raise ValueError("Full name, position and department are required")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        if connection.execute("SELECT 1 FROM users WHERE employee_id = ? OR username = ?", (employee_id, employee_id)).fetchone():
            raise ValueError("Employee already has an account")
        cursor = connection.execute(
            """INSERT INTO registration_requests(
                employee_id, full_name, position, department, status, created_at
            ) VALUES (?, ?, ?, ?, 'PENDING', ?)""",
            (employee_id, clean["full_name"], clean["position"], clean["department"], _now()),
        )
        connection.commit()
        return {"id": cursor.lastrowid, "employee_id": employee_id, "status": "PENDING"}
    except sqlite3.IntegrityError as error:
        raise ValueError("A pending registration already exists for this employee") from error
    finally:
        connection.close()


def list_registration_requests(status_filter: str | None = None, database_path: str | None = None) -> list[dict[str, Any]]:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        if status_filter:
            rows = connection.execute(
                "SELECT * FROM registration_requests WHERE status = ? ORDER BY id", (status_filter,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM registration_requests ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_registration_request(request_id: int, database_path: str | None = None) -> dict[str, Any] | None:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute("SELECT * FROM registration_requests WHERE id = ?", (request_id,)).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def review_registration(
    request_id: int,
    actor_user_id: int,
    decision: str,
    rejection_reason: str | None = None,
    database_path: str | None = None,
) -> dict[str, Any] | None:
    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError("Invalid review decision")
    reason = rejection_reason.strip() if rejection_reason else None
    if decision == "REJECTED" and not reason:
        raise ValueError("Rejection reason is required")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            """UPDATE registration_requests
               SET status = ?, reviewed_by = ?, reviewed_at = ?, rejection_reason = ?
               WHERE id = ? AND status = 'PENDING'""",
            (decision, actor_user_id, _now(), reason, request_id),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            return None
        request_row = connection.execute("SELECT * FROM registration_requests WHERE id = ?", (request_id,)).fetchone()
        if decision == "APPROVED":
            connection.execute(
                """INSERT INTO employees(employee_id, full_name, position, department, is_verified, created_at)
                   VALUES (?, ?, ?, ?, 1, ?)
                   ON CONFLICT(employee_id) DO UPDATE SET
                     full_name=excluded.full_name, position=excluded.position,
                     department=excluded.department, is_verified=1""",
                (request_row["employee_id"], request_row["full_name"], request_row["position"], request_row["department"], _now()),
            )
        connection.execute(
            "INSERT INTO audit_logs(actor_user_id, action, target_type, target_id, details_json, created_at) VALUES (?, ?, 'registration_request', ?, ?, ?)",
            (actor_user_id, f"registration.{decision.lower()}", str(request_id), json.dumps({"reason": reason}), _now()),
        )
        connection.commit()
        return dict(request_row)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def provision_user(
    request_id: int,
    temporary_password: str,
    role: str,
    permissions: list[str],
    data_scope: str,
    actor_user_id: int,
    database_path: str | None = None,
) -> dict[str, Any]:
    if role not in VALID_ROLES or data_scope not in VALID_SCOPES:
        raise ValueError("Invalid role or data scope")
    requested = set(permissions)
    if not requested or not requested <= ROLE_PERMISSIONS[role]:
        raise ValueError("Permissions are empty or not allowed for this role")
    if data_scope == "all" and role != "admin":
        raise ValueError("Only admin accounts may use all data scope")
    password_hash = hash_password(temporary_password)
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        request_row = connection.execute(
            "SELECT * FROM registration_requests WHERE id = ? AND status = 'APPROVED'", (request_id,)
        ).fetchone()
        if not request_row:
            raise ValueError("Registration request must be approved before provisioning")
        cursor = connection.execute(
            """INSERT INTO users(
                username, password_hash, role, created_at, employee_id, status,
                permissions_json, data_scope, registration_request_id
            ) VALUES (?, ?, ?, ?, ?, 'PENDING_ACTIVATION', ?, ?, ?)""",
            (request_row["employee_id"], password_hash, role, _now(), request_row["employee_id"],
             json.dumps(sorted(requested)), data_scope, request_id),
        )
        connection.execute(
            "INSERT INTO audit_logs(actor_user_id, action, target_type, target_id, details_json, created_at) VALUES (?, 'user.provisioned', 'user', ?, ?, ?)",
            (actor_user_id, str(cursor.lastrowid), json.dumps({"role": role, "data_scope": data_scope}), _now()),
        )
        connection.commit()
        return get_user_by_id(cursor.lastrowid, database_path)
    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise ValueError("This request or employee has already been provisioned") from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def activate_user(user_id: int, new_password: str, database_path: str | None = None) -> bool:
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT password_hash FROM users WHERE id = ? AND status = 'PENDING_ACTIVATION'", (user_id,)).fetchone()
        if not row:
            connection.rollback()
            return False
        if verify_password(new_password, row["password_hash"]):
            raise ValueError("New password must differ from the temporary password")
        cursor = connection.execute(
            """UPDATE users SET password_hash = ?, status = 'ACTIVE', activated_at = ?, token_version = token_version + 1
               WHERE id = ? AND status = 'PENDING_ACTIVATION'""",
            (hash_password(new_password), _now(), user_id),
        )
        connection.commit()
        return cursor.rowcount == 1
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_user_role(user_id: int, role: str, database_path: str | None = None) -> bool:
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")
    init_auth_db(database_path)
    connection = _connect(database_path)
    try:
        cursor = connection.execute(
            "UPDATE users SET role = ?, permissions_json = ?, data_scope = ?, token_version = token_version + 1 WHERE id = ?",
            (role, json.dumps(_default_permissions(role)), _default_scope(role), user_id),
        )
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


def create_access_token(user: dict[str, Any], expires_minutes: int | None = None, token_type: str = "access") -> str:
    if token_type not in {"access", "activation"}:
        raise ValueError("Invalid token type")
    now = datetime.now(timezone.utc)
    ttl = expires_minutes if expires_minutes is not None else (10 if token_type == "activation" else settings.jwt_exp_minutes)
    payload = {
        "sub": str(user["id"]), "username": user["username"], "role": user["role"],
        "typ": token_type, "ver": int(user.get("token_version", 0)),
        "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    body = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.jwt_secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def decode_access_token(token: str, expected_type: str = "access") -> dict[str, Any]:
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
        if payload.get("typ") != expected_type or payload.get("role") not in VALID_ROLES:
            raise ValueError("Invalid token purpose or role")
        int(payload["sub"])
        int(payload["ver"])
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Invalid access token") from error


def role_allowed(user: dict[str, Any], *roles: str) -> bool:
    return user.get("role") in roles

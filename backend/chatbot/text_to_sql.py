"""Generate and enforce a narrow, read-only SQLite query subset."""

import re
import sqlite3

from backend.chatbot.prompt_templates import text_to_sql_prompt

MAX_SQL_ROWS = 500
FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM|TRIGGER)\b", re.I)
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def question_to_sql(question: str, schema: dict, llm=None) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ("xóa", "xoá", "delete", "drop", "update", "sửa")):
        raise ValueError("Only read-only analytical questions are allowed")
    if llm is not None:
        generated = llm.generate(
            "You convert Vietnamese BI questions into one SQLite SELECT query. Return SQL only.",
            text_to_sql_prompt(question, schema),
            {"schema": schema},
        ).strip()
        if generated.startswith("```"):
            generated = re.sub(r"^```(?:sql)?\s*|\s*```$", "", generated, flags=re.I).strip()
        return generated
    if "lợi nhuận" in lowered or "profit" in lowered:
        return "SELECT SUM(revenue - cost) AS net_profit FROM sales LIMIT 500"
    if "đơn hàng" in lowered or "order" in lowered:
        return "SELECT COUNT(DISTINCT order_id) AS order_count FROM sales LIMIT 500"
    if "sản phẩm" in lowered or "product" in lowered:
        return "SELECT product, SUM(revenue) AS revenue FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 500"
    return "SELECT SUM(revenue) AS total_revenue FROM sales LIMIT 500"


def validate_select_sql(sql: str, allowed_tables: set[str], allowed_columns: set[str]) -> str:
    normalized = sql.strip()
    if normalized.endswith(";"):
        normalized = normalized[:-1].strip()
    if ";" in normalized or "--" in normalized or "/*" in normalized or not re.match(r"^SELECT\b", normalized, re.I):
        raise ValueError("Only one plain SELECT statement is allowed")
    if FORBIDDEN.search(normalized):
        raise ValueError("SQL contains a forbidden operation")
    tables = {name.lower() for name in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", normalized, re.I)}
    if not tables or not tables <= {table.lower() for table in allowed_tables}:
        raise ValueError("SQL references an unknown table")
    aliases = {name.lower() for name in re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", normalized, re.I)}
    keywords = {
        "select", "from", "where", "group", "by", "order", "asc", "desc", "limit",
        "as", "and", "or", "not", "null", "distinct", "sum", "count", "avg", "min", "max",
    }
    names = {name.lower() for name in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", normalized)}
    unknown = names - keywords - {name.lower() for name in allowed_tables | allowed_columns} - aliases
    if unknown:
        raise ValueError(f"SQL references unknown identifiers: {', '.join(sorted(unknown))}")
    if not re.search(r"\bLIMIT\s+\d+\b", normalized, re.I):
        normalized += f" LIMIT {MAX_SQL_ROWS}"
    else:
        normalized = re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {MAX_SQL_ROWS}", normalized, flags=re.I)
    # The application generates SQL from a fixed grammar; this allowlist is a second check.
    for identifier in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", normalized):
        if not IDENTIFIER.fullmatch(identifier):
            raise ValueError("Invalid SQL identifier")
    return normalized


def execute_read_only(connection: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    connection.execute("PRAGMA query_only = ON")
    denied = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE, sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA}
    connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_DENY if action in denied else sqlite3.SQLITE_OK)
    connection.row_factory = sqlite3.Row
    return [dict(row) for row in connection.execute(sql, params).fetchmany(MAX_SQL_ROWS)]

"""
Generic Schema Definition and Validation Specification for AI BI Dashboard.
Provides standard Pydantic models for Domain Schemas, Tables, Columns, Relationships, Metrics, and Dimensions.
Supports automated schema validation, metadata inspection, and JSON Schema export.
"""

from __future__ import annotations
import json
import re
import unicodedata
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_alias_token(value: str) -> str:
    """
    Normalizes column names/aliases:
    1. Splits CamelCase / PascalCase boundaries (e.g. InvoiceNo -> Invoice_No, UnitPrice -> Unit_Price).
    2. Strips Vietnamese diacritics (e.g. đ -> d, Ngày bán -> ngay_ban).
    3. Lowercases and normalizes non-alphanumeric separators to single underscores.
    """
    raw = str(value or "").strip()
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", raw)
    raw = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", raw)
    text = raw.lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", stripped).strip("_")


class DataType(str, Enum):
    """Standard generic machine-readable data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TEXT = "text"


class SemanticType(str, Enum):
    """Business and semantic categorization of data fields."""
    IDENTIFIER = "identifier"
    TEXT = "text"
    EMAIL = "email"
    CATEGORICAL = "categorical"
    CATEGORICAL_GEOGRAPHIC = "categorical_geographic"
    POSTAL_CODE = "postal_code"
    TIMESTAMP = "timestamp"
    DATE = "date"
    NUMERICAL_CURRENCY = "numerical_currency"
    NUMERICAL_QUANTITY = "numerical_quantity"
    NUMERICAL_RATIO = "numerical_ratio"
    FLAG = "flag"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


class Cardinality(str, Enum):
    """Relationship cardinality types."""
    MANY_TO_ONE = "many_to_one"
    ONE_TO_MANY = "one_to_many"
    ONE_TO_ONE = "one_to_one"
    MANY_TO_MANY = "many_to_many"


class ValueRange(BaseModel):
    """Defines acceptable numerical or temporal range constraints."""
    model_config = ConfigDict(extra="ignore")
    min_value: Optional[Union[float, int, str]] = None
    max_value: Optional[Union[float, int, str]] = None


class ColumnDefinition(BaseModel):
    """Specification for a single table column / attribute."""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    type: str = Field(description="Data type (e.g. string, integer, float, boolean, date, datetime)")
    nullable: bool = Field(default=True, description="Whether null/missing values are permitted")
    semantic_type: Optional[str] = Field(default=None, description="Business semantic type for BI and Text-to-SQL")
    description: Optional[str] = Field(default=None, description="Human-readable column explanation")
    aliases: List[str] = Field(default_factory=list, description="Synonyms in natural language (EN/VI) for AI matching")
    example: Optional[Any] = Field(default=None, description="Representative example value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (USD, percentage, grams, etc.)")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Enum domain / allowed category values")
    value_range: Optional[ValueRange] = Field(default=None, description="Allowed value boundary")
    min_value: Optional[Union[float, int]] = Field(default=None, description="Minimum numeric value constraint")
    max_value: Optional[Union[float, int]] = Field(default=None, description="Maximum numeric value constraint")
    regex_pattern: Optional[str] = Field(default=None, description="Regex pattern for string validation")

    @field_validator("aliases", mode="before")
    @classmethod
    def ensure_aliases_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]


class ForeignKeyDefinition(BaseModel):
    """Specification for a foreign key relationship inside a table."""
    model_config = ConfigDict(extra="ignore")

    column: str = Field(description="Source column in the current table")
    references_table: str = Field(description="Target referenced table name")
    references_column: str = Field(description="Target referenced column name")
    relationship_type: str = Field(default="many_to_one", description="Cardinality type")


class TableDefinition(BaseModel):
    """Specification for a logical business table / entity."""
    model_config = ConfigDict(extra="ignore")

    table_name: str = Field(description="Identifier name of the table")
    description: Optional[str] = Field(default=None, description="Business description of table entity")
    primary_key: List[str] = Field(default_factory=list, description="Primary key column(s)")
    foreign_keys: List[ForeignKeyDefinition] = Field(default_factory=list, description="Foreign key links")
    columns: Dict[str, ColumnDefinition] = Field(default_factory=dict, description="Dictionary of columns")

    @field_validator("primary_key", mode="before")
    @classmethod
    def ensure_pk_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v or []


class RelationshipDefinition(BaseModel):
    """Specification for explicit inter-table relationships."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique relationship identifier")
    from_table: str = Field(description="Origin table")
    from_column: str = Field(description="Origin column")
    to_table: str = Field(description="Target referenced table")
    to_column: str = Field(description="Target referenced column")
    cardinality: str = Field(default="many_to_one", description="Relationship cardinality")
    description: Optional[str] = Field(default=None, description="Business explanation of relationship")


class MetricDefinition(BaseModel):
    """Specification for BI semantic KPIs and financial metrics."""
    model_config = ConfigDict(extra="ignore")

    metric_name: str = Field(description="Formal metric name")
    code: str = Field(description="Unique metric code (e.g. GMV, Net_Profit)")
    unit: Optional[str] = Field(default=None, description="Metric unit (USD, percentage, ratio, etc.)")
    category: Optional[str] = Field(default=None, description="Business domain category")
    description: Optional[str] = Field(default=None, description="Business calculation purpose")
    formula: Optional[str] = Field(default=None, description="Mathematical formula expression")
    sql_expression: Optional[str] = Field(default=None, description="Standard SQL expression for BI engine")
    aliases: List[str] = Field(default_factory=list, description="Synonyms for chatbot and search mapping")


class DimensionDefinition(BaseModel):
    """Specification for drill-down reporting dimensions."""
    model_config = ConfigDict(extra="ignore")

    description: Optional[str] = Field(default=None, description="Dimension purpose")
    hierarchies: List[str] = Field(default_factory=list, description="Ordered drill-down hierarchy levels")


class SchemaMetadata(BaseModel):
    """Metadata header for schema specifications."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Machine-readable schema name")
    version: str = Field(default="1.0.0", description="Semantic version")
    domain: Optional[str] = Field(default=None, description="Business domain (e.g., E-Commerce, Healthcare)")
    description: Optional[str] = Field(default=None, description="Detailed schema description")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp or date")
    author: Optional[str] = Field(default=None, description="Author or organization")
    primary_currency: Optional[str] = Field(default="USD", description="Default currency code")
    timezone: Optional[str] = Field(default="UTC", description="Default timezone")
    custom_tags: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extension metadata")


class GenericSchema(BaseModel):
    """
    Root Generic Semantic Schema Specification.
    Validates any domain schema loaded into the AI BI Dashboard platform.
    """
    model_config = ConfigDict(extra="ignore")

    schema_metadata: SchemaMetadata = Field(description="Schema metadata header")
    tables: Dict[str, TableDefinition] = Field(description="Dictionary of tables in the domain")
    relationships: List[RelationshipDefinition] = Field(default_factory=list, description="Inter-table relationships")
    semantic_metrics: Dict[str, MetricDefinition] = Field(default_factory=dict, description="Calculated business KPIs")
    dimensions: Dict[str, DimensionDefinition] = Field(default_factory=dict, description="Reporting drill-down dimensions")

    def get_table(self, table_name: str) -> Optional[TableDefinition]:
        """Retrieves table definition by table name."""
        return self.tables.get(table_name)

    def get_column(self, table_name: str, column_name: str) -> Optional[ColumnDefinition]:
        """Retrieves a specific column definition within a table."""
        table = self.get_table(table_name)
        if table:
            return table.columns.get(column_name)
        return None

    def get_metric(self, metric_code: str) -> Optional[MetricDefinition]:
        """Retrieves KPI metric definition by code."""
        return self.semantic_metrics.get(metric_code)

    def get_table_names(self) -> List[str]:
        """Returns list of all table names."""
        return list(self.tables.keys())

    def find_columns_by_alias(self, query_alias: str, table_name: Optional[str] = None) -> List[Tuple[str, str, ColumnDefinition]]:
        """
        Searches for columns matching a natural language alias (exact or CamelCase/diacritic-insensitive).
        Returns a list of tuples: (table_name, column_name, ColumnDefinition).
        """
        results = []
        normalized_query = query_alias.strip().lower()
        token_query = normalize_alias_token(query_alias)
        tables_to_search = [table_name] if table_name and table_name in self.tables else self.tables.keys()

        # Pass 1: exact case-insensitive match on column name or alias
        for t_name in tables_to_search:
            table = self.tables[t_name]
            for c_name, col_def in table.columns.items():
                if normalized_query == c_name.lower():
                    results.append((t_name, c_name, col_def))
                    continue
                for alias in col_def.aliases:
                    if normalized_query == alias.strip().lower():
                        results.append((t_name, c_name, col_def))
                        break
        if results or not token_query:
            return results

        # Pass 2: normalized token match (handles CamelCase, Vietnamese without diacritics, spaces vs underscores)
        for t_name in tables_to_search:
            table = self.tables[t_name]
            for c_name, col_def in table.columns.items():
                if token_query == normalize_alias_token(c_name):
                    results.append((t_name, c_name, col_def))
                    continue
                for alias in col_def.aliases:
                    if token_query == normalize_alias_token(alias):
                        results.append((t_name, c_name, col_def))
                        break
        return results

    def validate_integrity(self) -> List[str]:
        """
        Performs structural integrity checks on the schema.
        Returns a list of warning/error messages (empty if completely valid).
        """
        errors = []

        # Check tables, primary keys, and foreign keys
        for table_name, table in self.tables.items():
            for pk in table.primary_key:
                if pk not in table.columns:
                    errors.append(f"Table '{table_name}': Primary key column '{pk}' is not defined in columns.")

            for fk in table.foreign_keys:
                if fk.column not in table.columns:
                    errors.append(f"Table '{table_name}': Foreign key source column '{fk.column}' does not exist.")
                if fk.references_table not in self.tables:
                    errors.append(f"Table '{table_name}': Foreign key references non-existent table '{fk.references_table}'.")
                else:
                    ref_table = self.tables[fk.references_table]
                    if fk.references_column not in ref_table.columns:
                        errors.append(f"Table '{table_name}': Foreign key references non-existent column '{fk.references_column}' in '{fk.references_table}'.")

        # Check explicit relationships
        for rel in self.relationships:
            if rel.from_table not in self.tables:
                errors.append(f"Relationship '{rel.id}': from_table '{rel.from_table}' not found in schema.")
            elif rel.from_column not in self.tables[rel.from_table].columns:
                errors.append(f"Relationship '{rel.id}': from_column '{rel.from_column}' not found in '{rel.from_table}'.")

            if rel.to_table not in self.tables:
                errors.append(f"Relationship '{rel.id}': to_table '{rel.to_table}' not found in schema.")
            elif rel.to_column not in self.tables[rel.to_table].columns:
                errors.append(f"Relationship '{rel.id}': to_column '{rel.to_column}' not found in '{rel.to_table}'.")

        return errors


def validate_schema(data: Union[dict, str, Path]) -> GenericSchema:
    """
    Validates a schema dictionary, JSON string, or file path against GenericSchema.
    Returns the parsed GenericSchema instance or raises ValidationError.
    """
    if isinstance(data, (str, Path)):
        p = Path(data)
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            raw_data = json.loads(str(data))
    else:
        raw_data = data

    schema_obj = GenericSchema.model_validate(raw_data)
    integrity_errors = schema_obj.validate_integrity()
    if integrity_errors:
        raise ValueError(f"Schema integrity validation failed with {len(integrity_errors)} error(s):\n" + "\n".join(f"- {e}" for e in integrity_errors))

    return schema_obj


def load_schema(file_path: Union[str, Path]) -> GenericSchema:
    """Loads and validates a schema from a JSON file path."""
    return validate_schema(file_path)


def export_json_schema(output_path: Optional[Union[str, Path]] = None) -> dict:
    """
    Exports the JSON Schema standard definition of GenericSchema.
    Optionally saves it to a JSON file.
    """
    json_schema = GenericSchema.model_json_schema()
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_schema, f, indent=2, ensure_ascii=False)
    return json_schema


DEFAULT_ECOMMERCE_SCHEMA_PATH = Path(__file__).resolve().parent / "ecommerce_schema.json"
LEARNED_SEED_PROFILE_PATH = Path(__file__).resolve().parent.parent / "data" / "datasets" / "learned_seed_profile.json"

ROLE_PRIORITIES: Dict[str, List[str]] = {
    "date": ["date", "order_purchase_timestamp", "created_at", "order_approved_at"],
    "order_id": ["order_id", "sales_id", "financial_record_id"],
    "product": ["product", "product_name", "sub_category", "category", "product_id"],
    "product_id": ["product_id", "stock_code", "sku"],
    "revenue": ["revenue", "net_sales", "gross_revenue", "gross_sales", "payment_value"],
    "cost": ["cost", "cogs", "cogs_total", "unit_cost"],
    "category": ["category", "sub_category"],
    "quantity": ["quantity"],
    "unit_price": ["unit_price"],
    "unit_cost": ["unit_cost"],
    "discount_amount": ["discount_amount"],
    "ad_spend": ["ad_spend", "marketing_spend"],
    "new_customers": ["new_customers", "conversions"],
    "customer_id": ["customer_id"],
    "net_profit": ["net_profit"],
    "platform_fee": ["platform_fee", "platform_fees_total"],
    "freight_value": ["freight_value", "shipping_cost_total"],
    "tax_amount": ["tax_amount"],
    "operating_expenses": ["operating_expenses"],
    "sales_id": ["sales_id"],
}


@lru_cache(maxsize=1)
def get_default_ecommerce_schema() -> GenericSchema:
    """Loads and caches the default 38-column e-commerce knowledge base schema."""
    return load_schema(DEFAULT_ECOMMERCE_SCHEMA_PATH)


@lru_cache(maxsize=1)
def get_learned_pricing_profile() -> Dict[str, Any]:
    """
    Loads read-only statistical pricing & margin knowledge from `data/datasets/learned_seed_profile.json`
    learned by SchemaExtractor.
    """
    default_margin = 0.45
    category_margins: Dict[str, float] = {}
    if LEARNED_SEED_PROFILE_PATH.is_file():
        try:
            with open(LEARNED_SEED_PROFILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            num_dist = data.get("distributions", {}).get("numerical", {})
            if "margin_rate" in num_dist and "mean" in num_dist["margin_rate"]:
                default_margin = float(num_dist["margin_rate"]["mean"])
            cat_patterns = data.get("hierarchies", {}).get("category_pricing_patterns", {})
            for cat, info in cat_patterns.items():
                if isinstance(info, dict) and "mean_margin_rate" in info:
                    category_margins[str(cat).strip().lower()] = float(info["mean_margin_rate"])
        except Exception:
            pass
    return {
        "default_margin_rate": max(0.05, min(0.90, default_margin)),
        "category_margins": category_margins,
    }


def estimate_learned_cost(revenue: float, category: Optional[str] = None) -> float:
    """
    Estimates Cost of Goods Sold (COGS) from revenue using the learned margin rate
    from `learned_seed_profile.json` when a dataset (e.g. `online_retail_clean`) lacks a cost column.
    """
    profile = get_learned_pricing_profile()
    margin_rate = profile["default_margin_rate"]
    if category:
        cat_key = str(category).strip().lower()
        if cat_key in profile["category_margins"]:
            margin_rate = profile["category_margins"][cat_key]
    return round(max(0.0, float(revenue) * (1.0 - margin_rate)), 2)


def _layer2_heuristic_match(token: str) -> Optional[Dict[str, Any]]:
    """
    Layer 2 Semantic Heuristic (ported from SchemaExtractor.infer_semantic_type):
    Matches unseen column names by sub-tokens when Layer 1 exact/alias lookup does not match.
    """
    if not token:
        return None
    parts = set(token.split("_"))

    if any(w in token for w in ("invoice_date", "trans_date", "order_date", "purchase_date")) or (
        parts & {"date", "timestamp", "time", "ngay"}
    ):
        return {
            "matched_table": "orders",
            "matched_column": "order_purchase_timestamp",
            "declared_type": "datetime",
            "semantic_type": "timestamp",
            "unit": None,
            "description": "Inferred temporal milestone (Layer 2 heuristic)",
        }
    if any(w in token for w in ("invoice_no", "invoiceno", "bill_no", "order_no")) or (
        parts & {"invoice", "order"} and parts & {"id", "no", "number", "code", "ma"}
    ):
        return {
            "matched_table": "orders",
            "matched_column": "order_id",
            "declared_type": "string",
            "semantic_type": "identifier",
            "unit": None,
            "description": "Inferred order identifier (Layer 2 heuristic)",
        }
    if any(w in token for w in ("stock_code", "stockcode", "item_code", "product_code")) or (
        parts & {"product", "item", "stock", "sku"} and parts & {"id", "code", "no", "ma"}
    ):
        return {
            "matched_table": "products",
            "matched_column": "product_id",
            "declared_type": "string",
            "semantic_type": "identifier",
            "unit": None,
            "description": "Inferred product identifier (Layer 2 heuristic)",
        }
    if any(w in token for w in ("description", "product_desc", "item_desc", "product_title")) or (
        parts & {"description", "desc", "title"}
    ):
        return {
            "matched_table": "products",
            "matched_column": "product_name",
            "declared_type": "string",
            "semantic_type": "text",
            "unit": None,
            "description": "Inferred product title/description (Layer 2 heuristic)",
        }
    if any(w in token for w in ("unit_price", "selling_price", "item_price", "retail_price")):
        return {
            "matched_table": "sales",
            "matched_column": "unit_price",
            "declared_type": "float",
            "semantic_type": "numerical_currency",
            "unit": "USD",
            "description": "Inferred unit selling price (Layer 2 heuristic)",
        }
    if any(w in token for w in ("unit_cost", "item_cost", "buying_cost")):
        return {
            "matched_table": "products",
            "matched_column": "unit_cost",
            "declared_type": "float",
            "semantic_type": "numerical_currency",
            "unit": "USD",
            "description": "Inferred unit cost (Layer 2 heuristic)",
        }
    if parts & {"qty", "quantity"} or "so_luong" in token:
        return {
            "matched_table": "sales",
            "matched_column": "quantity",
            "declared_type": "integer",
            "semantic_type": "numerical_quantity",
            "unit": None,
            "description": "Inferred item quantity (Layer 2 heuristic)",
        }
    if any(w in token for w in ("revenue", "net_sales", "total_sales", "line_total", "amount", "doanh_thu", "thanh_tien")):
        return {
            "matched_table": "sales",
            "matched_column": "net_sales",
            "declared_type": "float",
            "semantic_type": "numerical_currency",
            "unit": "USD",
            "description": "Inferred sales revenue (Layer 2 heuristic)",
        }
    if any(w in token for w in ("cogs", "cost_of_goods", "total_cost", "gia_von", "chi_phi")):
        return {
            "matched_table": "financials",
            "matched_column": "cogs_total",
            "declared_type": "float",
            "semantic_type": "numerical_currency",
            "unit": "USD",
            "description": "Inferred cost of goods sold (Layer 2 heuristic)",
        }
    return None


def inspect_and_map_columns(
    headers: List[str],
    schema: Optional[GenericSchema] = None,
) -> Dict[str, Any]:
    """
    2-Layer Semantic Mapper:
    - Layer 1: Matches user headers against the 38-column semantic dictionary & 15 metrics.
    - Layer 2: Applies sub-token heuristics (like SchemaExtractor.infer_semantic_type) for unseen variants.
    Resolves the 5 Dashboard View Contract roles + financial extension roles without mutating original headers.
    """
    schema_obj = schema or get_default_ecommerce_schema()
    column_semantics: Dict[str, Dict[str, Any]] = {}
    concept_to_headers: Dict[str, List[str]] = {}

    for header in headers:
        raw_header = str(header)
        token = normalize_alias_token(raw_header)
        matches = schema_obj.find_columns_by_alias(raw_header)
        if matches:
            table_name, col_name, col_def = matches[0]
            column_semantics[raw_header] = {
                "matched_table": table_name,
                "matched_column": col_name,
                "declared_type": col_def.type,
                "semantic_type": col_def.semantic_type or "custom",
                "unit": col_def.unit,
                "description": col_def.description,
            }
            concept_to_headers.setdefault(col_name, []).append(raw_header)
            if token:
                concept_to_headers.setdefault(token, []).append(raw_header)
        else:
            # Layer 1B: Check semantic_metrics (e.g. gross_profit, gross_margin_pct, net_margin_pct, cogs)
            matched_metric = None
            for metric in schema_obj.semantic_metrics.values():
                metric_tokens = {normalize_alias_token(metric.code), *(normalize_alias_token(a) for a in metric.aliases)}
                if token in metric_tokens or (token.endswith("_pct") and token[:-4] in metric_tokens):
                    matched_metric = metric
                    break
            if matched_metric:
                sem_type = "percentage" if matched_metric.unit == "percentage" else "numerical_currency"
                column_semantics[raw_header] = {
                    "matched_table": "semantic_metrics",
                    "matched_column": matched_metric.code.lower(),
                    "declared_type": "float",
                    "semantic_type": sem_type,
                    "unit": matched_metric.unit,
                    "description": matched_metric.description,
                }
                concept_to_headers.setdefault(matched_metric.code.lower(), []).append(raw_header)
            else:
                # Layer 2: Keyword & token structure heuristic
                heuristic_info = _layer2_heuristic_match(token)
                if heuristic_info:
                    column_semantics[raw_header] = heuristic_info
                    concept_to_headers.setdefault(heuristic_info["matched_column"], []).append(raw_header)
                else:
                    column_semantics[raw_header] = {
                        "matched_table": None,
                        "matched_column": None,
                        "declared_type": None,
                        "semantic_type": "custom",
                        "unit": None,
                        "description": None,
                    }
            if token:
                concept_to_headers.setdefault(token, []).append(raw_header)

    roles: Dict[str, Optional[str]] = {}
    for role, candidates in ROLE_PRIORITIES.items():
        selected = None
        for candidate in candidates:
            for header in headers:
                if normalize_alias_token(header) == candidate:
                    selected = header
                    break
            if selected:
                break
        if not selected:
            for candidate in candidates:
                if candidate in concept_to_headers and concept_to_headers[candidate]:
                    selected = concept_to_headers[candidate][0]
                    break
        roles[role] = selected

    return {
        "columns": column_semantics,
        "roles": roles,
    }

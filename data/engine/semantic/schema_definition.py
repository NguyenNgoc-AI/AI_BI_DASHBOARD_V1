"""
Generic Schema Definition and Validation Specification for AI BI Dashboard.
Provides standard Pydantic models for Domain Schemas, Tables, Columns, Relationships, Metrics, and Dimensions.
Supports automated schema validation, metadata inspection, and JSON Schema export.
"""

from __future__ import annotations
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
        Searches for columns matching a natural language alias.
        Returns a list of tuples: (table_name, column_name, ColumnDefinition).
        """
        results = []
        normalized_query = query_alias.strip().lower()
        tables_to_search = [table_name] if table_name and table_name in self.tables else self.tables.keys()

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


"""
Unit tests for Generic Schema Definition and Validator (Task 1).
Compatible with Python unittest and pytest.
"""

import unittest
import tempfile
from pathlib import Path
from semantic.schema_definition import (
    GenericSchema,
    TableDefinition,
    ColumnDefinition,
    ForeignKeyDefinition,
    RelationshipDefinition,
    MetricDefinition,
    DimensionDefinition,
    SchemaMetadata,
    validate_schema,
    load_schema,
    export_json_schema,
)

SCHEMA_FILE = Path(__file__).parent.parent / "semantic" / "ecommerce_schema.json"


class TestSchemaDefinition(unittest.TestCase):
    def test_load_and_validate_ecommerce_gold_template(self):
        """Test loading and validating the Gold Template ecommerce_schema.json."""
        schema = load_schema(SCHEMA_FILE)
        self.assertIsInstance(schema, GenericSchema)
        self.assertEqual(schema.schema_metadata.name, "ecommerce_bi_semantic_schema")
        self.assertIn("customers", schema.tables)
        self.assertIn("products", schema.tables)
        self.assertIn("orders", schema.tables)
        self.assertIn("sales", schema.tables)
        self.assertIn("financials", schema.tables)
        self.assertGreaterEqual(len(schema.relationships), 4)
        self.assertIn("GMV", schema.semantic_metrics)
        self.assertIn("Net_Profit", schema.semantic_metrics)

    def test_find_columns_by_alias(self):
        """Test searching for columns by natural language aliases in Vietnamese and English."""
        schema = load_schema(SCHEMA_FILE)
        
        # English alias / column name
        results_en = schema.find_columns_by_alias("customer_id")
        self.assertGreaterEqual(len(results_en), 1)
        
        # Vietnamese alias
        results_vi = schema.find_columns_by_alias("doanh thu thuần")
        self.assertTrue(any(c[1] == "net_sales" for c in results_vi))
        
        # Vietnamese alias for price
        results_price = schema.find_columns_by_alias("giá bán")
        self.assertTrue(any(c[1] == "unit_price" for c in results_price))

    def test_schema_integrity_error_handling(self):
        """Test that integrity validator catches broken foreign keys or missing primary keys."""
        broken_schema_dict = {
            "schema_metadata": {
                "name": "broken_schema",
                "version": "1.0.0"
            },
            "tables": {
                "users": {
                    "table_name": "users",
                    "primary_key": ["missing_pk_col"],  # Broken PK
                    "columns": {
                        "id": {"type": "integer"}
                    }
                },
                "orders": {
                    "table_name": "orders",
                    "foreign_keys": [
                        {
                            "column": "user_id",
                            "references_table": "non_existent_table",  # Broken FK
                            "references_column": "id"
                        }
                    ],
                    "columns": {
                        "order_id": {"type": "string"},
                        "user_id": {"type": "integer"}
                    }
                }
            },
            "relationships": [],
            "semantic_metrics": {},
            "dimensions": {}
        }
        
        with self.assertRaises(ValueError) as context:
            validate_schema(broken_schema_dict)
        
        error_msg = str(context.exception)
        self.assertIn("Primary key column 'missing_pk_col' is not defined", error_msg)
        self.assertIn("references non-existent table", error_msg)

    def test_export_json_schema(self):
        """Test exporting JSON Schema standard definition."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "generic_schema.json"
            exported = export_json_schema(out_file)
            self.assertIsInstance(exported, dict)
            self.assertTrue("$defs" in exported or "properties" in exported)
            self.assertTrue(out_file.exists())


if __name__ == "__main__":
    unittest.main()


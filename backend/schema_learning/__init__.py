"""
Schema Learning and Rule Parsing Package for AI BI Dashboard.

This package provides modules to:
1. Extract statistical distributions, correlations, and semantic data profiles (schema_extractor.py).
2. Parse business logic rules into executable constraints and mathematical repair functions (rule_parser.py).
"""

from backend.schema_learning.schema_extractor import (
    DataDistribution,
    LearnedSchemaProfile,
    SchemaExtractor,
)
from backend.schema_learning.rule_parser import (
    ConstraintEngine,
    ExecutableConstraint,
    RuleParser,
    ValidationReport,
)

__all__ = [
    "SchemaExtractor",
    "LearnedSchemaProfile",
    "DataDistribution",
    "RuleParser",
    "ExecutableConstraint",
    "ConstraintEngine",
    "ValidationReport",
]

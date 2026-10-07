"""
Synthetic Generator Package for AI BI Dashboard.

This package provides:
1. BusinessDataGenerator (SyntheticGeneratorModel): Hierarchical conditional synthetic business data generator.
2. SyntheticDataPipeline: End-to-end parameterized orchestration pipeline with constraint enforcement and export.
"""

from backend.synthetic_generator.generator_model import (
    BusinessDataGenerator,
    SyntheticGeneratorModel,
)
from backend.synthetic_generator.pipeline import SyntheticDataPipeline

__all__ = [
    "BusinessDataGenerator",
    "SyntheticGeneratorModel",
    "SyntheticDataPipeline",
]

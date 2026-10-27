"""
Synthetic Generator Package for AI BI Dashboard.

This package provides:
1. BusinessDataGenerator (SyntheticGeneratorModel): Hierarchical conditional synthetic business data generator.
2. SyntheticDataPipeline: End-to-end parameterized orchestration pipeline with constraint enforcement and export.
"""

from .generator_model import (
    BusinessDataGenerator,
    SyntheticGeneratorModel,
)
from .pipeline import SyntheticDataPipeline

__all__ = [
    "BusinessDataGenerator",
    "SyntheticGeneratorModel",
    "SyntheticDataPipeline",
]

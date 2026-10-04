"""
Synthetic Generator Package for AI BI Dashboard.

This package provides:
1. SyntheticGeneratorModel: Hierarchical conditional synthetic data generation engine.
2. SyntheticDataPipeline: End-to-end orchestration pipeline with constraint enforcement and CSV export.
"""

from backend.synthetic_generator.generator_model import SyntheticGeneratorModel
from backend.synthetic_generator.pipeline import SyntheticDataPipeline

__all__ = [
    "SyntheticGeneratorModel",
    "SyntheticDataPipeline",
]

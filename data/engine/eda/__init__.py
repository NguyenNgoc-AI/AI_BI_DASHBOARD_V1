"""
EDA (Exploratory Data Analysis) and Quality Assessment Package for AI BI Dashboard.
Provides Generic Data Profiler and Data Quality Checker engines.
"""

from .profiling import GenericDataProfiler, DataProfiler
from .quality_checker import GenericQualityChecker, DataQualityChecker

__all__ = [
    "GenericDataProfiler",
    "DataProfiler",
    "GenericQualityChecker",
    "DataQualityChecker",
]

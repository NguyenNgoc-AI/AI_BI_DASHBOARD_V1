"""
Runner Script: Run Data Profiling & Quality Audit on Ecommerce Seed Dataset.
Outputs reports to JSON and Markdown format in docs/ and data/generated/.
"""

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from backend.eda.profiling import DataProfiler
from backend.eda.quality_checker import DataQualityChecker

SEED_DATA_PATH = PROJECT_ROOT / "data" / "sample_dataset" / "ecommerce_seed.csv"
DOCS_DIR = PROJECT_ROOT / "docs"

def main():
    print(f"Loading seed data from {SEED_DATA_PATH}...")
    df = pd.read_csv(SEED_DATA_PATH)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns.")

    # 1. Run Data Profiler
    print("\n[1/2] Running Data Profiler...")
    profiler = DataProfiler(dataset_name="ecommerce_seed.csv")
    profile_result = profiler.profile_dataframe(df)
    
    profiling_md_path = DOCS_DIR / "eda_seed_profiling.md"
    profile_md = profiler.generate_markdown_report(profile_result)
    with open(profiling_md_path, "w", encoding="utf-8") as f:
        f.write(profile_md)

    print(f"  -> Saved profiling Markdown report to: {profiling_md_path}")

    # 2. Run Data Quality Checker
    print("\n[2/2] Running Data Quality Checker...")
    checker = DataQualityChecker(dataset_name="ecommerce_seed.csv")
    quality_result = checker.check_dataset_quality(df, primary_key="sales_id")
    
    quality_md_path = DOCS_DIR / "data_quality_audit.md"
    quality_md = checker.generate_quality_markdown_report(quality_result)
    with open(quality_md_path, "w", encoding="utf-8") as f:
        f.write(quality_md)

    print(f"  -> Saved quality Markdown report to: {quality_md_path}")

    print("\n" + "=" * 60)
    print(f"OVERALL QUALITY SCORE: {quality_result['data_quality_score']} / 100")
    print(f"QUALITY TIER:          {quality_result['quality_tier']}")
    print(f"STATUS:                {quality_result['overall_status']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

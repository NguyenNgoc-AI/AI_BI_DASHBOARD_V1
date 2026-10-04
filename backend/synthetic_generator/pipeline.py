"""
Synthetic Data Generation Pipeline for AI BI Dashboard.

Orchestrates:
1. Loading learned distributions and schema metadata.
2. Model sampling and synthetic dataset generation.
3. Constraint enforcement and mathematical post-processing.
4. Validation and quality verification gate.
5. Exporting production-ready synthetic dataset to CSV.
"""

from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any, Dict, Optional, Union
import pandas as pd

from backend.schema_learning.rule_parser import ConstraintEngine, ValidationReport
from backend.schema_learning.schema_extractor import LearnedSchemaProfile
from backend.synthetic_generator.generator_model import SyntheticGeneratorModel


class SyntheticDataPipeline:
    """
    End-to-end Pipeline for generating, repairing, validating, and saving synthetic e-commerce data.
    """

    def __init__(
        self,
        profile_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = None,
        random_state: int = 42,
    ):
        self.profile_path = Path(profile_path) if profile_path else Path("data/generated/learned_seed_profile.json")
        self.output_path = Path(output_path) if output_path else Path("data/generated/synthetic_ecommerce.csv")
        self.random_state = random_state
        self.engine = ConstraintEngine()

    def run(
        self,
        n_samples: int = 50000,
        enforce_rules: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes the full generation, repair, and export pipeline.
        """
        start_time = time.time()
        print(f"[*] Starting Synthetic Data Generation Pipeline for {n_samples:,} records...")

        # 1. Check profile existence
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Learned profile not found at {self.profile_path}. Please run Task 5 schema extractor first.")

        # 2. Instantiate Model and Sample
        print(f"[*] Initializing SyntheticGeneratorModel with profile: {self.profile_path}")
        model = SyntheticGeneratorModel(profile_path=self.profile_path, random_state=self.random_state)

        print(f"[*] Generating {n_samples:,} raw synthetic records...")
        df_raw = model.generate(n_samples=n_samples)

        # 3. Post-Processing & Constraint Enforcement
        if enforce_rules:
            print("[*] Applying ConstraintEngine post-processing and mathematical repair...")
            df_final = self.engine.enforce_constraints(df_raw)
        else:
            df_final = df_raw

        # 4. Quality Validation Gate
        print("[*] Running Validation Gate on generated dataset...")
        validation_report = self.engine.validate_dataframe(df_final)
        print(f"[*] Validation Gate: {validation_report.summary_message}")

        # 5. Export to CSV
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[*] Exporting synthetic dataset to: {self.output_path}...")
        df_final.to_csv(self.output_path, index=False, encoding="utf-8")
        file_size_mb = round(self.output_path.stat().st_size / (1024 * 1024), 2)
        elapsed_sec = round(time.time() - start_time, 2)

        print(f"[OK] Successfully generated and exported {len(df_final):,} rows ({file_size_mb} MB) in {elapsed_sec}s.")

        return {
            "status": "SUCCESS",
            "total_records": len(df_final),
            "total_columns": len(df_final.columns),
            "output_filepath": str(self.output_path),
            "file_size_mb": file_size_mb,
            "elapsed_seconds": elapsed_sec,
            "pass_rate_pct": validation_report.overall_pass_rate_pct,
            "has_blocking_errors": validation_report.has_blocking_errors,
            "validation_summary": validation_report.to_dict(),
        }


def run_pipeline():
    """CLI runner entry point."""
    pipeline = SyntheticDataPipeline()
    result = pipeline.run(n_samples=50000)
    print("\n--- Pipeline Execution Summary ---")
    print(f"Status: {result['status']}")
    print(f"Records: {result['total_records']:,}")
    print(f"Output: {result['output_filepath']} ({result['file_size_mb']} MB)")
    print(f"Pass Rate: {result['pass_rate_pct']}% (Errors: {result['has_blocking_errors']})")


if __name__ == "__main__":
    run_pipeline()

"""Orchestrate generation and validation."""

from backend.schema_learning.schema_extractor import infer_schema
from backend.synthetic_generator.generator_model import create_generator
from backend.synthetic_generator.validator import validate_synthetic


def generate_synthetic_dataset(
    rows: list[dict], count: int, seed: int | None = None, model: str = "bootstrap", target_column: str | None = None, llm=None
) -> dict:
    schema = infer_schema(rows)
    generated = create_generator(model, llm).generate(rows, count, seed)
    return {"model": model, "rows": generated, "validation": validate_synthetic(rows, generated, schema, target_column)}

"""Build grounded context from the current dashboard for LLM queries."""

from backend.chatbot.llm_router import LLMAdapter
from backend.chatbot.prompt_templates import dashboard_qa_prompt, financial_system_prompt


def build_dashboard_context(schema: dict, profile: dict, quality: dict, kpis: dict, charts: list[dict]) -> dict:
    return {
        "schema": schema,
        "profile": profile,
        "quality": quality,
        "kpis": kpis,
        "charts": charts,
        "available_dimensions": sorted(schema.get("columns", {})),
    }


def answer_dashboard_question(question: str, context: dict, llm: LLMAdapter) -> dict[str, str | None]:
    if not question.strip() or len(question) > 2_000:
        raise ValueError("Question must contain 1 to 2000 characters")
    answer = llm.generate(financial_system_prompt(), dashboard_qa_prompt(question, context), context)
    return {
        "answer": answer,
        "source": "dashboard_context",
        "provider": getattr(llm, "used_provider", "custom"),
        "fallback_reason": getattr(llm, "fallback_reason", None),
    }

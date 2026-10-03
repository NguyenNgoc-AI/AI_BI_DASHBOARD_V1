"""Route dashboard prompts to OpenAI, Gemini, Llama or an offline fallback."""

import json
from typing import Protocol

import httpx

from backend.config import Settings, settings


class LLMAdapter(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str: ...


class DeterministicAdapter:
    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str:
        kpis = (context or {}).get("kpis", {})
        if not kpis:
            return "Không có đủ dữ liệu dashboard để trả lời."
        return (
            f"Theo dữ liệu dashboard: doanh thu {kpis.get('total_revenue')}, "
            f"chi phí {kpis.get('total_cost')}, lợi nhuận ròng {kpis.get('net_profit')}."
        )


class OpenAIAdapter:
    def __init__(self, api_key: str, model: str, timeout: float):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str:
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "instructions": system_prompt, "input": user_prompt},
            timeout=self.timeout,
        )
        response.raise_for_status()
        text = "".join(
            item.get("text", "")
            for block in response.json().get("output", []) if block.get("type") == "message"
            for item in block.get("content", []) if item.get("type") == "output_text"
        ).strip()
        if not text:
            raise RuntimeError("OpenAI returned no text output")
        return text


class GeminiAdapter:
    def __init__(self, api_key: str, model: str, timeout: float):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for the Gemini provider")
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned no text output")
        return text


class LlamaAdapter:
    """Call an OpenAI-compatible local Llama server (Ollama, vLLM, etc.)."""

    def __init__(self, base_url: str, model: str, timeout: float):
        if not base_url:
            raise ValueError("LLAMA_BASE_URL is required for the Llama provider")
        self.url = base_url.rstrip("/") + "/v1/chat/completions"
        self.model, self.timeout = model, timeout

    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str:
        response = httpx.post(
            self.url,
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            return response.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise RuntimeError("Llama server returned an invalid response") from error


def create_adapter(config: Settings) -> LLMAdapter:
    if config.llm_provider == "deterministic":
        return DeterministicAdapter()
    if config.llm_provider == "openai":
        return OpenAIAdapter(config.openai_api_key or "", config.openai_model, config.llm_timeout_seconds)
    if config.llm_provider == "gemini":
        return GeminiAdapter(config.gemini_api_key or "", config.gemini_model, config.llm_timeout_seconds)
    if config.llm_provider == "llama":
        return LlamaAdapter(config.llama_base_url or "", config.llama_model, config.llm_timeout_seconds)
    raise ValueError("LLM_PROVIDER must be deterministic, openai, gemini or llama")


class LLMRouter:
    def __init__(self, config: Settings = settings):
        self.provider = config.llm_provider
        self.fallback = DeterministicAdapter()
        self.adapter = create_adapter(config)
        self.used_provider = self.provider
        self.fallback_reason: str | None = None

    def generate(self, system_prompt: str, user_prompt: str, context: dict | None = None) -> str:
        try:
            return self.adapter.generate(system_prompt, user_prompt, context)
        except (httpx.HTTPError, RuntimeError) as error:
            if self.provider == "deterministic":
                raise
            self.used_provider = "deterministic"
            self.fallback_reason = type(error).__name__
            return self.fallback.generate(system_prompt, user_prompt, context)

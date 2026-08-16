from __future__ import annotations

from app.config import (
    GROQ_BASE_URL,
    GROQ_MODEL,
    LLMConfig,
    Settings,
    XAI_BASE_URL,
    XAI_MODEL,
    get_settings,
)


def _non_openai_model(explicit_model: str | None, fallback: str) -> str:
    if explicit_model and explicit_model != "gpt-4o-mini":
        return explicit_model
    return fallback


def resolve_llm(settings: Settings | None = None) -> LLMConfig | None:
    settings = settings or get_settings()
    groq_key = settings.groq_api_key.strip()
    xai_key = (settings.xai_api_key or settings.grok_api_key).strip()
    openai_key = settings.openai_api_key.strip()
    explicit_url = settings.openai_base_url.strip() or None
    explicit_model = settings.openai_model.strip() or None

    if groq_key:
        return LLMConfig(
            api_key=groq_key,
            base_url=explicit_url or GROQ_BASE_URL,
            model=_non_openai_model(explicit_model, GROQ_MODEL),
            provider="groq",
        )
    if xai_key:
        return LLMConfig(
            api_key=xai_key,
            base_url=explicit_url or XAI_BASE_URL,
            model=_non_openai_model(explicit_model, XAI_MODEL),
            provider="xai",
        )
    if openai_key.startswith("gsk_"):
        return LLMConfig(
            api_key=openai_key,
            base_url=explicit_url or GROQ_BASE_URL,
            model=_non_openai_model(explicit_model, GROQ_MODEL),
            provider="groq",
        )
    if openai_key.startswith("xai-"):
        return LLMConfig(
            api_key=openai_key,
            base_url=explicit_url or XAI_BASE_URL,
            model=_non_openai_model(explicit_model, XAI_MODEL),
            provider="xai",
        )
    if openai_key:
        return LLMConfig(
            api_key=openai_key,
            base_url=explicit_url,
            model=explicit_model or "gpt-4o-mini",
            provider="openai",
        )
    return None

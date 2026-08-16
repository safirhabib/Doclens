from app.config import GROQ_BASE_URL, GROQ_MODEL, Settings
from app.llm import resolve_llm


def _settings(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_groq_named_key() -> None:
    llm = resolve_llm(_settings(groq_api_key="gsk_test"))
    assert llm is not None
    assert llm.provider == "groq"
    assert llm.base_url == GROQ_BASE_URL
    assert llm.model == GROQ_MODEL


def test_groq_key_in_openai_slot() -> None:
    llm = resolve_llm(_settings(openai_api_key="gsk_test"))
    assert llm is not None
    assert llm.provider == "groq"
    assert llm.base_url == GROQ_BASE_URL


def test_xai_named_key() -> None:
    llm = resolve_llm(_settings(xai_api_key="xai-test"))
    assert llm is not None
    assert llm.provider == "xai"


def test_openai_key_unchanged() -> None:
    llm = resolve_llm(_settings(openai_api_key="sk-test"))
    assert llm is not None
    assert llm.provider == "openai"
    assert llm.model == "gpt-4o-mini"


def test_no_key() -> None:
    assert resolve_llm(_settings()) is None

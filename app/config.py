from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "qwen/qwen3.6-27b"
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-2-vision-1212"

_SECRET_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_BASE_URL",
    "GROQ_API_KEY",
    "XAI_API_KEY",
    "GROK_API_KEY",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    groq_api_key: str = ""
    xai_api_key: str = ""
    grok_api_key: str = ""
    doclens_api_url: str = "http://localhost:8000"
    mlflow_tracking_uri: str = "file:./mlruns"
    review_confidence_threshold: float = 0.8
    data_dir: Path = PROJECT_ROOT / "data"
    prompts_dir: Path = PROJECT_ROOT / "experiments" / "prompts"
    results_dir: Path = PROJECT_ROOT / "experiments" / "results"
    ocr_min_words: int = 15
    render_dpi: int = 150


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str | None
    model: str
    provider: str


def _copy_streamlit_secrets() -> None:
    try:
        import streamlit as st

        secrets = st.secrets
    except Exception:
        return
    for name in _SECRET_NAMES:
        if os.environ.get(name):
            continue
        try:
            value = secrets[name]
        except Exception:
            continue
        if value not in (None, ""):
            os.environ[name] = str(value)


def get_settings() -> Settings:
    _copy_streamlit_secrets()
    return Settings()

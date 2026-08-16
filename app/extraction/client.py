from __future__ import annotations

import json
from typing import Protocol

from openai import OpenAI

from app.config import get_settings
from app.extraction.json_parse import parse_model
from app.schemas.compliance import ModelRequirements
from app.schemas.extraction import ModelExtraction


class ExtractionClient(Protocol):
    def extract_equipment(self, messages: list[dict], model: str) -> ModelExtraction: ...

    def extract_requirements(self, messages: list[dict], model: str) -> ModelRequirements: ...


class OpenAIExtractionClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        settings = get_settings()
        key = api_key if api_key is not None else settings.openai_api_key
        url = base_url if base_url is not None else (settings.openai_base_url or None)
        kwargs: dict = {"api_key": key or None}
        if url:
            kwargs["base_url"] = url
        self._client = OpenAI(**kwargs)

    def extract_equipment(self, messages: list[dict], model: str) -> ModelExtraction:
        return self._parse(messages, model, ModelExtraction, "equipment extraction")

    def extract_requirements(self, messages: list[dict], model: str) -> ModelRequirements:
        return self._parse(messages, model, ModelRequirements, "requirements extraction")

    def _parse(self, messages: list[dict], model: str, schema, label: str):
        try:
            completion = self._client.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=schema,
                temperature=0,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is not None:
                return parsed
        except Exception:
            pass
        try:
            completion = self._client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
            )
        except Exception as exc:
            raise ValueError(f"{label} failed ({model}): {exc}") from exc
        text = completion.choices[0].message.content or ""
        try:
            return parse_model(text, schema)
        except Exception as exc:
            raise ValueError(f"Model returned empty {label}") from exc


class FakeExtractionClient:
    """Deterministic stand-in for tests. Optional canned payloads."""

    def __init__(
        self,
        equipment: ModelExtraction | None = None,
        requirements: ModelRequirements | None = None,
    ) -> None:
        self.equipment = equipment or ModelExtraction(equipment=[])
        self.requirements = requirements or ModelRequirements(requirements=[])
        self.calls: list[str] = []

    def extract_equipment(self, messages: list[dict], model: str) -> ModelExtraction:
        self.calls.append(json.dumps({"model": model, "kind": "equipment"}))
        return self.equipment

    def extract_requirements(self, messages: list[dict], model: str) -> ModelRequirements:
        self.calls.append(json.dumps({"model": model, "kind": "requirements"}))
        return self.requirements


def build_extraction_client() -> OpenAIExtractionClient | None:
    from app.llm import resolve_llm

    llm = resolve_llm()
    if llm is None:
        return None
    return OpenAIExtractionClient(api_key=llm.api_key, base_url=llm.base_url)


def default_model() -> str:
    from app.llm import resolve_llm

    llm = resolve_llm()
    if llm is None:
        return "heuristic"
    return llm.model

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_model(text: str, model_cls: type[T]) -> T:
    """Parse a Pydantic model from model/agent output that may include fences or prose."""
    if not text or not text.strip():
        raise ValueError("empty model output")
    candidates = [text.strip()]
    fenced = _FENCE.findall(text)
    candidates = [block.strip() for block in fenced] + candidates
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.insert(0, text[start : end + 1])

    errors: list[str] = []
    for blob in candidates:
        try:
            return model_cls.model_validate_json(blob)
        except Exception as exc:
            errors.append(str(exc))
        try:
            payload = json.loads(blob)
            if isinstance(payload, list):
                payload = {"equipment": payload}
            return model_cls.model_validate(payload)
        except Exception as exc:
            errors.append(str(exc))
    raise ValueError(f"could not parse {model_cls.__name__}: {errors[0]}")

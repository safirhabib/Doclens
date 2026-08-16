from __future__ import annotations

from app.config import get_settings
from app.schemas.extraction import FieldValue


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def calibrate_field(
    field: FieldValue,
    *,
    used_ocr: bool,
    grounded: bool,
) -> FieldValue:
    confidence = field.confidence
    if used_ocr:
        confidence *= 0.9
    if not grounded:
        confidence *= 0.75
    if field.value is None:
        confidence = min(confidence, 0.2)
    return field.model_copy(update={"confidence": round(clamp(confidence), 4)})


def load_prompt(name: str) -> str:
    settings = get_settings()
    path = settings.prompts_dir / name
    return path.read_text(encoding="utf-8").strip()

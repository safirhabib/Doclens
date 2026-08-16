from __future__ import annotations

from app.schemas.evaluation import FailureType


def classify_failure(
    *,
    predicted: str | None,
    ground_truth: str | None,
    used_ocr: bool,
    predicted_in_document: bool,
    field: str,
) -> FailureType:
    if predicted is None or predicted == "":
        return FailureType.MISSING
    if ground_truth is None:
        return FailureType.INCORRECT
    if used_ocr and _looks_like_ocr_error(predicted, ground_truth):
        return FailureType.INCORRECT_OCR
    if field == "capacity" and _numeric_confusion(predicted, ground_truth):
        return FailureType.TABLE_LAYOUT
    if field == "capacity" and _unit_mismatch(predicted, ground_truth):
        return FailureType.UNIT_INTERPRETATION
    if not predicted_in_document:
        return FailureType.VLM_HALLUCINATION
    if used_ocr:
        return FailureType.LOW_RESOLUTION
    if _partial_overlap(predicted, ground_truth):
        return FailureType.AMBIGUOUS_TERMINOLOGY
    return FailureType.INCORRECT


def _looks_like_ocr_error(predicted: str, ground_truth: str) -> bool:
    a = predicted.replace(" ", "").lower()
    b = ground_truth.replace(" ", "").lower()
    if a == b:
        return False
    if abs(len(a) - len(b)) > 3:
        return False
    distance = _levenshtein(a, b)
    return 0 < distance <= 2


def _numeric_confusion(predicted: str, ground_truth: str) -> bool:
    def number(text: str) -> str:
        digits = "".join(ch for ch in text if ch.isdigit())
        return digits

    p, g = number(predicted), number(ground_truth)
    if not p or not g or p == g:
        return False
    return p in g or g in p or abs(len(p) - len(g)) <= 1


def _unit_mismatch(predicted: str, ground_truth: str) -> bool:
    def parts(text: str) -> tuple[str, str]:
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        unit = "".join(ch for ch in text.lower() if ch.isalpha())
        return digits, unit

    p_num, p_unit = parts(predicted)
    g_num, g_unit = parts(ground_truth)
    return bool(p_num and g_num and p_num == g_num and p_unit and g_unit and p_unit != g_unit)


def _partial_overlap(predicted: str, ground_truth: str) -> bool:
    a, b = predicted.lower(), ground_truth.lower()
    return a in b or b in a


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            ins = current[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            current.append(min(ins, delete, sub))
        prev = current
    return prev[-1]

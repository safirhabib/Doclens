from __future__ import annotations

import re

from app.vision.boxes import normalize_text


def normalize_value(value: str | int | float | None) -> str | None:
    if value is None:
        return None
    text = normalize_text(str(value))
    if text == "":
        return None
    return text


def values_match(predicted: str | int | float | None, ground_truth: str | int | float | None) -> bool:
    left = normalize_value(predicted)
    right = normalize_value(ground_truth)
    if left is None or right is None:
        return False
    if left == right:
        return True
    return _numeric_unit_match(left, right)


def _numeric_unit_match(left: str, right: str) -> bool:
    pattern = re.compile(r"^(\d+(?:\.\d+)?)\s*([a-z]+)?$")
    a = pattern.match(left)
    b = pattern.match(right)
    if not a or not b:
        return False
    if float(a.group(1)) != float(b.group(1)):
        return False
    unit_a = a.group(2) or ""
    unit_b = b.group(2) or ""
    aliases = {("cfm", "cfm"), ("kw", "kw"), ("gpm", "gpm"), ("a", "a")}
    return unit_a == unit_b or (unit_a, unit_b) in aliases

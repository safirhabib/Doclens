from __future__ import annotations

import re

from app.schemas.compliance import Operator
from app.schemas.extraction import EquipmentRecord, FieldValue


def parse_capacity(value: str | int | float | None) -> tuple[float | None, str]:
    if value is None:
        return None, ""
    text = str(value).replace(",", "")
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*([A-Za-z]+)?", text)
    if not match:
        return None, ""
    number = float(match.group(1))
    unit = (match.group(2) or "").strip()
    return number, unit


def field_numeric(field: FieldValue | None) -> tuple[float | None, str]:
    if field is None:
        return None, ""
    if isinstance(field.value, int | float) and not isinstance(field.value, bool):
        return float(field.value), ""
    return parse_capacity(field.value)


def units_compatible(left: str, right: str) -> bool:
    if not left or not right:
        return True
    return left.lower() == right.lower()


def apply_operator(actual: float, operator: Operator, threshold: float) -> bool:
    if operator == Operator.GTE:
        return actual >= threshold
    if operator == Operator.LTE:
        return actual <= threshold
    if operator == Operator.GT:
        return actual > threshold
    if operator == Operator.LT:
        return actual < threshold
    return actual == threshold


def type_matches(record: EquipmentRecord, equipment_type: str | None) -> bool:
    if not equipment_type:
        return True
    actual = str(record.type.value or "").lower()
    tag = str(record.tag.value or "").upper()
    expected = equipment_type.lower()
    if expected in actual:
        return True
    aliases = {
        "emergency generator": ("generator", "g-"),
        "air handling unit": ("air handling", "ahu"),
        "centrifugal pump": ("pump", "p-"),
    }
    for key, needles in aliases.items():
        if key in expected:
            return any(needle in actual or tag.startswith(needle.upper().rstrip("-")) for needle in needles)
    return False


def record_metric_value(record: EquipmentRecord, metric: str) -> tuple[float | None, str, FieldValue | None]:
    if metric == "quantity":
        return field_numeric(record.quantity)[0], "", record.quantity
    if metric == "capacity":
        number, unit = field_numeric(record.capacity)
        return number, unit, record.capacity
    return None, "", None

from __future__ import annotations

import re

from app.schemas.compliance import ModelRequirement, ModelRequirements, Operator
from app.vision.types import DocumentContent

PATTERNS = [
    (
        re.compile(
            r"(emergency\s+generator|generator).{0,80}?(minimum capacity of|at least|minimum of)\s+(\d+(?:,\d{3})*)\s*(kW)",
            re.IGNORECASE,
        ),
        "capacity",
        "Emergency Generator",
        Operator.GTE,
    ),
    (
        re.compile(
            r"(air handling unit|AHU).{0,80}?(minimum capacity of|at least|minimum of)\s+(\d+(?:,\d{3})*)\s*(CFM)",
            re.IGNORECASE,
        ),
        "capacity",
        "Air Handling Unit",
        Operator.GTE,
    ),
    (
        re.compile(
            r"(centrifugal pumps?|pumps?).{0,80}?(quantity of at least|at least)\s+(\d+)\b",
            re.IGNORECASE,
        ),
        "quantity",
        "Centrifugal Pump",
        Operator.GTE,
    ),
]


def heuristic_requirements(document: DocumentContent) -> ModelRequirements:
    text = document.full_text
    found: list[ModelRequirement] = []
    for pattern, metric, equipment_type, operator in PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        threshold = float(match.group(3).replace(",", ""))
        unit = match.group(4) if match.lastindex and match.lastindex >= 4 else ""
        if metric == "quantity":
            unit = ""
        page = 1
        for page_content in document.pages:
            if match.group(0)[:40].lower() in page_content.text.lower():
                page = page_content.page
                break
        found.append(
            ModelRequirement(
                text=match.group(0).strip(),
                metric=metric,
                equipment_type=equipment_type,
                operator=operator.value,
                threshold=threshold,
                unit=unit,
                page=page,
            )
        )
    return ModelRequirements(requirements=found)

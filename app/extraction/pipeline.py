from __future__ import annotations

import base64
import time
from pathlib import Path

from app.extraction.client import ExtractionClient, build_extraction_client, default_model
from app.extraction.confidence import calibrate_field, load_prompt
from app.extraction.grounding import ground_record, page_used_ocr
from app.extraction.heuristic import heuristic_extract
from app.schemas.extraction import (
    EquipmentRecord,
    ExtractionResult,
    FieldValue,
    ModelEquipment,
    ModelExtraction,
)
from app.vision.pdf import load_pdf
from app.vision.types import DocumentContent

STRATEGIES = ("heuristic", "v1", "v2", "v3")


def _document_id(filename: str) -> str:
    return Path(filename).stem


def _coerce_quantity(value: str | None) -> str | int | None:
    if value is None or value == "":
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit() or ch == "-")
    if digits in {"", "-"}:
        return str(value)
    try:
        return int(digits)
    except ValueError:
        return str(value)


def _to_record(item: ModelEquipment) -> EquipmentRecord:
    def fv(model_field, coerce=lambda x: x) -> FieldValue:
        if model_field is None:
            return FieldValue(value=None, confidence=0.0)
        return FieldValue(value=coerce(model_field.value), confidence=model_field.confidence)

    manufacturer = None
    if item.manufacturer is not None:
        manufacturer = fv(item.manufacturer)
    return EquipmentRecord(
        tag=fv(item.tag),
        type=fv(item.type),
        quantity=fv(item.quantity, _coerce_quantity),
        capacity=fv(item.capacity),
        manufacturer=manufacturer,
    )


def _image_message(png: bytes) -> dict:
    b64 = base64.b64encode(png).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"},
    }


def _v1_messages(document: DocumentContent) -> list[dict]:
    prompt = load_prompt("extract_v1.txt")
    return [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": f"Document: {document.filename}\n\n{document.full_text}",
        },
    ]


def _v2_messages(document: DocumentContent) -> list[dict]:
    prompt = load_prompt("extract_v2.txt")
    content: list[dict] = [
        {
            "type": "text",
            "text": f"Document: {document.filename}\n\nExtracted text:\n{document.full_text}",
        }
    ]
    images = 0
    for page in document.pages:
        if page.image_png and images < 5:
            content.append(_image_message(page.image_png))
            images += 1
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content},
    ]


def _v3_messages(document: DocumentContent) -> list[dict]:
    prompt = load_prompt("extract_v3.txt")
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Document: {document.filename}\n"
                "Extract only values you can support from a table cell or sentence.\n\n"
                f"{document.full_text}"
            ),
        }
    ]
    images = 0
    for page in document.pages:
        if page.image_png and images < 5:
            content.append(_image_message(page.image_png))
            images += 1
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content},
    ]


def _run_model(
    document: DocumentContent,
    strategy: str,
    model: str,
    client: ExtractionClient,
) -> tuple[ModelExtraction, str]:
    if strategy == "v1":
        parsed = client.extract_equipment(_v1_messages(document), model)
        return parsed, "extract_v1"
    if strategy == "v2":
        parsed = client.extract_equipment(_v2_messages(document), model)
        return parsed, "extract_v2"
    if strategy == "v3":
        parsed = client.extract_equipment(_v3_messages(document), model)
        return parsed, "extract_v3"
    raise ValueError(f"Unknown strategy: {strategy}")


def _finalize(model_result: ModelExtraction, document: DocumentContent) -> list[EquipmentRecord]:
    records: list[EquipmentRecord] = []
    for item in model_result.equipment:
        record = ground_record(_to_record(item), document)
        fields = {}
        for name in ("tag", "type", "quantity", "capacity", "manufacturer"):
            field = getattr(record, name)
            if field is None:
                continue
            ocr = page_used_ocr(document, field.source)
            fields[name] = calibrate_field(field, used_ocr=ocr, grounded=field.source is not None)
        records.append(record.model_copy(update=fields))
    return records


def extract_document(
    source: bytes | Path,
    filename: str | None = None,
    strategy: str = "v2",
    model: str | None = None,
    client: ExtractionClient | None = None,
) -> ExtractionResult:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")

    model_name = model or default_model()
    started = time.perf_counter()
    document = load_pdf(source, filename=filename)
    name = document.filename

    if strategy == "heuristic":
        model_result = heuristic_extract(document)
        prompt_version = "heuristic"
        model_name = "heuristic"
    else:
        if client is None:
            client = build_extraction_client()
        if client is None:
            model_result = heuristic_extract(document)
            prompt_version = "heuristic-fallback"
            model_name = "heuristic"
            strategy = "heuristic"
        else:
            model_result, prompt_version = _run_model(document, strategy, model_name, client)

    equipment = _finalize(model_result, document)
    latency_ms = (time.perf_counter() - started) * 1000
    return ExtractionResult(
        document_id=_document_id(name),
        filename=name,
        strategy=strategy,
        model=model_name,
        prompt_version=prompt_version,
        latency_ms=round(latency_ms, 1),
        used_ocr=document.used_ocr,
        ocr_pages=document.ocr_pages,
        page_count=len(document.pages),
        equipment=equipment,
    )

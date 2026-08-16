from __future__ import annotations

from app.schemas.extraction import EquipmentRecord, FieldValue, SourceSpan
from app.vision.boxes import find_span
from app.vision.types import DocumentContent, WordBox

FIELD_NAMES = ("tag", "type", "quantity", "capacity", "manufacturer")


def _all_words(document: DocumentContent) -> list[WordBox]:
    words: list[WordBox] = []
    for page in document.pages:
        words.extend(page.words)
    return words


def ground_record(record: EquipmentRecord, document: DocumentContent) -> EquipmentRecord:
    words = _all_words(document)
    tag_span = find_span(words, str(record.tag.value) if record.tag.value is not None else "")
    updates: dict[str, FieldValue] = {}
    for name in FIELD_NAMES:
        field: FieldValue | None = getattr(record, name)
        if field is None:
            continue
        query = field.value
        if query is None:
            updates[name] = field
            continue
        page = tag_span.page if tag_span else None
        span = find_span(
            words,
            str(query),
            page=page,
            anchor=tag_span,
        )
        if span is None and tag_span is not None:
            span = find_span(words, str(query), anchor=tag_span)
        updates[name] = field.model_copy(update={"source": span})
    if tag_span is not None and updates.get("tag") is not None:
        updates["tag"] = updates["tag"].model_copy(update={"source": tag_span})
    return record.model_copy(update=updates)


def page_used_ocr(document: DocumentContent, span: SourceSpan | None) -> bool:
    if span is None:
        return document.used_ocr
    for page in document.pages:
        if page.page == span.page:
            return page.used_ocr
    return document.used_ocr

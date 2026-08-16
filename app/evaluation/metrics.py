from __future__ import annotations

from collections import defaultdict

import pandas as pd

from app.evaluation.failures import classify_failure
from app.evaluation.normalize import normalize_value, values_match
from app.schemas.evaluation import EvalReport, FieldComparison
from app.schemas.extraction import EquipmentRecord, ExtractionResult, FieldValue
from app.schemas.ground_truth import GroundTruthDocument, GroundTruthEquipment
from app.vision.boxes import normalize_text

COMPARE_FIELDS = ("tag", "type", "quantity", "capacity", "manufacturer")


def _field_value(record: EquipmentRecord, name: str) -> FieldValue | None:
    return getattr(record, name)


def _gt_value(item: GroundTruthEquipment, name: str) -> str | int | None:
    return getattr(item, name)


def _predicted_in_document(predicted: str | None, document_text: str) -> bool:
    if not predicted:
        return False
    return normalize_text(predicted) in normalize_text(document_text)


def compare_extraction(
    result: ExtractionResult,
    truth: GroundTruthDocument,
    document_text: str = "",
) -> list[FieldComparison]:
    predicted_by_tag: dict[str, EquipmentRecord] = {}
    for record in result.equipment:
        key = normalize_value(record.tag.value)
        if key:
            predicted_by_tag[key] = record

    comparisons: list[FieldComparison] = []
    for item in truth.equipment:
        key = normalize_value(item.tag) or item.tag
        predicted = predicted_by_tag.get(key)
        for field in COMPARE_FIELDS:
            gt = _gt_value(item, field)
            gt_text = None if gt is None else str(gt)
            if predicted is None:
                comparisons.append(
                    FieldComparison(
                        document_id=result.document_id,
                        record_key=item.tag,
                        field=field,
                        predicted=None,
                        ground_truth=gt_text,
                        match=False,
                        failure_type=classify_failure(
                            predicted=None,
                            ground_truth=gt_text,
                            used_ocr=result.used_ocr,
                            predicted_in_document=False,
                            field=field,
                        ),
                        confidence=0.0,
                        used_ocr=result.used_ocr,
                    )
                )
                continue
            fv = _field_value(predicted, field)
            pred_val = None if fv is None or fv.value is None else str(fv.value)
            matched = values_match(pred_val, gt)
            failure = None
            if not matched:
                failure = classify_failure(
                    predicted=pred_val,
                    ground_truth=gt_text,
                    used_ocr=page_ocr(result, fv),
                    predicted_in_document=_predicted_in_document(pred_val, document_text),
                    field=field,
                )
            comparisons.append(
                FieldComparison(
                    document_id=result.document_id,
                    record_key=item.tag,
                    field=field,
                    predicted=pred_val,
                    ground_truth=gt_text,
                    match=matched,
                    failure_type=failure,
                    confidence=0.0 if fv is None else fv.confidence,
                    source=None if fv is None else fv.source,
                    used_ocr=result.used_ocr,
                )
            )
    return comparisons


def page_ocr(result: ExtractionResult, fv: FieldValue | None) -> bool:
    if fv is None or fv.source is None:
        return result.used_ocr
    return fv.source.page in result.ocr_pages


def build_report(
    *,
    strategy: str,
    model: str,
    prompt_version: str,
    dataset: str,
    comparisons: list[FieldComparison],
    latency_ms_mean: float,
) -> EvalReport:
    frame = pd.DataFrame([row.model_dump() for row in comparisons])
    total = len(comparisons)
    correct = int(frame["match"].sum()) if total else 0
    if total:
        unmatched = frame.loc[~frame["match"]]
        blank = unmatched["predicted"].isna() | (unmatched["predicted"] == "")
        missing = int(blank.sum())
        incorrect = int((~blank).sum())
    else:
        missing = 0
        incorrect = 0

    field_accuracy: dict[str, float] = {}
    if total:
        grouped = frame.groupby("field")["match"].mean()
        field_accuracy = {str(k): round(float(v) * 100, 2) for k, v in grouped.items()}

    failure_counts: dict[str, int] = defaultdict(int)
    for row in comparisons:
        if row.failure_type is not None:
            failure_counts[row.failure_type.value] += 1

    accuracy = round((correct / total) * 100, 2) if total else 0.0
    return EvalReport(
        strategy=strategy,
        model=model,
        prompt_version=prompt_version,
        dataset=dataset,
        accuracy=accuracy,
        field_accuracy=field_accuracy,
        total_fields=total,
        correct=correct,
        incorrect=max(0, incorrect),
        missing=missing,
        latency_ms_mean=round(latency_ms_mean, 1),
        comparisons=comparisons,
        failure_counts=dict(failure_counts),
    )

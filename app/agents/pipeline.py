from __future__ import annotations

import time
from pathlib import Path

from app.agents.compare import (
    apply_operator,
    record_metric_value,
    type_matches,
    units_compatible,
)
from app.agents.requirements import heuristic_requirements
from app.config import get_settings
from app.extraction.client import ExtractionClient, build_extraction_client, default_model
from app.extraction.confidence import load_prompt
from app.extraction.pipeline import extract_document
from app.schemas.compliance import (
    ComplianceFinding,
    ComplianceReport,
    ComplianceResult,
    EvidenceStep,
    ModelRequirements,
    Operator,
    Requirement,
)
from app.schemas.extraction import ExtractionResult
from app.vision.boxes import find_span
from app.vision.pdf import load_pdf
from app.vision.types import DocumentContent


def _to_requirement(model_req, document: DocumentContent) -> Requirement:
    try:
        operator = Operator(model_req.operator)
    except ValueError:
        operator = Operator.GTE
    source = None
    if model_req.text:
        words = [word for page in document.pages for word in page.words]
        source = find_span(words, model_req.text[:80], page=model_req.page)
    return Requirement(
        text=model_req.text,
        metric=model_req.metric,
        equipment_type=model_req.equipment_type,
        operator=operator,
        threshold=model_req.threshold,
        unit=model_req.unit or "",
        source=source,
    )


def extract_requirements(
    source: bytes | Path,
    filename: str | None = None,
    model: str | None = None,
    client: ExtractionClient | None = None,
) -> tuple[list[Requirement], DocumentContent]:
    settings = get_settings()
    document = load_pdf(source, filename=filename)
    parsed: ModelRequirements
    if client is None:
        client = build_extraction_client()
    if client is None:
        parsed = heuristic_requirements(document)
    else:
        prompt = load_prompt("requirements_v1.txt")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": document.full_text},
        ]
        try:
            parsed = client.extract_requirements(messages, model or default_model())
        except Exception:
            parsed = heuristic_requirements(document)

    if not parsed.requirements:
        parsed = heuristic_requirements(document)
    return [_to_requirement(item, document) for item in parsed.requirements], document


def _narrative(finding: ComplianceFinding) -> str:
    req = finding.requirement
    clause = f"{req.metric} {req.operator.value} {req.threshold:g} {req.unit}".strip()
    if finding.result == ComplianceResult.PASS:
        return (
            f"Scheduled {finding.detected_tag} meets {clause} "
            f"(detected {finding.detected_value})."
        )
    if finding.result == ComplianceResult.FAIL:
        return (
            f"Scheduled {finding.detected_tag} does not meet {clause} "
            f"(detected {finding.detected_value})."
        )
    return (
        f"Could not confidently verify {clause} for "
        f"{req.equipment_type or 'equipment'}; routed for human review."
    )


def check_requirement(
    requirement: Requirement,
    schedule: ExtractionResult,
    requirements_name: str,
    schedule_name: str,
    threshold: float,
) -> ComplianceFinding:
    chain = [
        EvidenceStep(step="requirement", detail=requirement.text, source=requirement.source),
        EvidenceStep(
            step="document_retrieval",
            detail=f"Loaded requirements '{requirements_name}' and schedule '{schedule_name}'",
        ),
    ]
    matches = [row for row in schedule.equipment if type_matches(row, requirement.equipment_type)]
    if not matches:
        finding = ComplianceFinding(
            requirement=requirement,
            detected_tag=None,
            detected_value=None,
            result=ComplianceResult.NEEDS_REVIEW,
            confidence=0.4,
            narrative="",
            evidence_chain=chain
            + [
                EvidenceStep(
                    step="structured_extraction",
                    detail="No matching equipment type in the schedule",
                )
            ],
        )
        finding.narrative = _narrative(finding)
        return finding

    worst: ComplianceFinding | None = None
    for record in matches:
        actual, unit, field = record_metric_value(record, requirement.metric)
        tag = None if record.tag.value is None else str(record.tag.value)
        chain_item = list(chain) + [
            EvidenceStep(
                step="relevant_source_location",
                detail=f"Equipment {tag}",
                source=record.tag.source,
            ),
            EvidenceStep(
                step="structured_extraction",
                detail=f"{requirement.metric}={field.value if field else None}",
                source=None if field is None else field.source,
            ),
        ]
        confidence = min(record.tag.confidence, field.confidence if field else 0.3)
        grounded = field is not None and field.source is not None
        if actual is None or (requirement.unit and unit and not units_compatible(unit, requirement.unit)):
            candidate = ComplianceFinding(
                requirement=requirement,
                detected_tag=tag,
                detected_value=None if field is None else str(field.value),
                result=ComplianceResult.NEEDS_REVIEW,
                confidence=min(confidence, 0.55),
                narrative="",
                evidence_chain=chain_item
                + [
                    EvidenceStep(
                        step="deterministic_comparison",
                        detail="Missing numeric value or incompatible units",
                    )
                ],
            )
        else:
            passed = apply_operator(actual, requirement.operator, requirement.threshold)
            display = f"{actual:g} {unit or requirement.unit}".strip()
            result = ComplianceResult.PASS if passed else ComplianceResult.FAIL
            if confidence < threshold or not grounded:
                result = ComplianceResult.NEEDS_REVIEW if passed else ComplianceResult.FAIL
            candidate = ComplianceFinding(
                requirement=requirement,
                detected_tag=tag,
                detected_value=display,
                result=result,
                confidence=confidence,
                narrative="",
                evidence_chain=chain_item
                + [
                    EvidenceStep(
                        step="deterministic_comparison",
                        detail=(
                            f"{actual:g} {requirement.operator.value} {requirement.threshold:g} "
                            f"{requirement.unit} → {'pass' if passed else 'fail'}"
                        ),
                        source=None if field is None else field.source,
                    ),
                    EvidenceStep(
                        step="llm_interpretation",
                        detail="Narrative is templated from the deterministic result; the model does not compute the inequality.",
                    ),
                    EvidenceStep(
                        step="compliance_result",
                        detail=result.value,
                    ),
                ],
            )
        candidate.narrative = _narrative(candidate)
        if worst is None or _severity(candidate) > _severity(worst):
            worst = candidate
    assert worst is not None
    return worst


def _severity(finding: ComplianceFinding) -> int:
    return {
        ComplianceResult.FAIL: 2,
        ComplianceResult.NEEDS_REVIEW: 1,
        ComplianceResult.PASS: 0,
    }[finding.result]


def run_compliance(
    requirements_source: bytes | Path,
    schedule_source: bytes | Path,
    requirements_filename: str = "requirements.pdf",
    schedule_filename: str = "schedule.pdf",
    strategy: str = "heuristic",
    model: str | None = None,
    client: ExtractionClient | None = None,
) -> ComplianceReport:
    settings = get_settings()
    started = time.perf_counter()
    requirements, _req_doc = extract_requirements(
        requirements_source,
        filename=requirements_filename,
        model=model,
        client=client,
    )
    schedule = extract_document(
        schedule_source,
        filename=schedule_filename,
        strategy=strategy,
        model=model,
        client=client,
    )
    findings = [
        check_requirement(
            requirement,
            schedule,
            requirements_filename,
            schedule_filename,
            settings.review_confidence_threshold,
        )
        for requirement in requirements
    ]
    passed = sum(1 for item in findings if item.result == ComplianceResult.PASS)
    failed = sum(1 for item in findings if item.result == ComplianceResult.FAIL)
    review = sum(1 for item in findings if item.result == ComplianceResult.NEEDS_REVIEW)
    return ComplianceReport(
        requirements_document=requirements_filename,
        schedule_document=schedule_filename,
        findings=findings,
        passed=passed,
        failed=failed,
        needs_review=review,
        latency_ms=round((time.perf_counter() - started) * 1000, 1),
    )

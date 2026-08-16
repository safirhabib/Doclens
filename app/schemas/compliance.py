from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.extraction import SourceSpan


class Operator(str, Enum):
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "="


class Requirement(BaseModel):
    text: str
    metric: str
    equipment_type: str | None = None
    operator: Operator
    threshold: float
    unit: str
    source: SourceSpan | None = None


class EvidenceStep(BaseModel):
    step: str
    detail: str
    source: SourceSpan | None = None


class ComplianceResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class ComplianceFinding(BaseModel):
    requirement: Requirement
    detected_tag: str | None = None
    detected_value: str | None = None
    result: ComplianceResult
    confidence: float = Field(ge=0.0, le=1.0)
    narrative: str
    evidence_chain: list[EvidenceStep] = Field(default_factory=list)


class ComplianceReport(BaseModel):
    requirements_document: str
    schedule_document: str
    findings: list[ComplianceFinding] = Field(default_factory=list)
    passed: int = 0
    failed: int = 0
    needs_review: int = 0
    latency_ms: float = 0.0


class ModelRequirement(BaseModel):
    text: str
    metric: str
    equipment_type: str | None = None
    operator: str
    threshold: float
    unit: str
    page: int | None = None


class ModelRequirements(BaseModel):
    requirements: list[ModelRequirement] = Field(default_factory=list)

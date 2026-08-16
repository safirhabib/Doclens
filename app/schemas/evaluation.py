from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.extraction import SourceSpan


class FailureType(str, Enum):
    INCORRECT_OCR = "incorrect_ocr"
    TABLE_LAYOUT = "table_layout"
    LOW_RESOLUTION = "low_resolution"
    AMBIGUOUS_TERMINOLOGY = "ambiguous_terminology"
    VLM_HALLUCINATION = "vlm_hallucination"
    UNIT_INTERPRETATION = "unit_interpretation"
    MISSING = "missing"
    INCORRECT = "incorrect"


class FieldComparison(BaseModel):
    document_id: str
    record_key: str
    field: str
    predicted: str | None = None
    ground_truth: str | None = None
    match: bool
    failure_type: FailureType | None = None
    confidence: float = 0.0
    source: SourceSpan | None = None
    used_ocr: bool = False


class EvalReport(BaseModel):
    strategy: str
    model: str
    prompt_version: str
    dataset: str
    accuracy: float
    field_accuracy: dict[str, float] = Field(default_factory=dict)
    total_fields: int
    correct: int
    incorrect: int
    missing: int
    latency_ms_mean: float
    comparisons: list[FieldComparison] = Field(default_factory=list)
    failure_counts: dict[str, int] = Field(default_factory=dict)

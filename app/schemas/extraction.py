from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    page: int
    bbox: tuple[float, float, float, float]


class FieldValue(BaseModel):
    value: str | int | float | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: SourceSpan | None = None


class EquipmentRecord(BaseModel):
    tag: FieldValue
    type: FieldValue
    quantity: FieldValue
    capacity: FieldValue
    manufacturer: FieldValue | None = None


class ExtractionResult(BaseModel):
    document_id: str
    filename: str
    strategy: str
    model: str
    prompt_version: str
    latency_ms: float
    used_ocr: bool
    ocr_pages: list[int] = Field(default_factory=list)
    page_count: int
    equipment: list[EquipmentRecord] = Field(default_factory=list)


class ModelField(BaseModel):
    value: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ModelEquipment(BaseModel):
    tag: ModelField
    type: ModelField
    quantity: ModelField
    capacity: ModelField
    manufacturer: ModelField | None = None


class ModelExtraction(BaseModel):
    equipment: list[ModelEquipment] = Field(default_factory=list)

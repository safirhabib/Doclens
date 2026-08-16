from pydantic import BaseModel, Field


class GroundTruthEquipment(BaseModel):
    tag: str
    type: str
    quantity: int
    capacity: str
    manufacturer: str | None = None


class GroundTruthDocument(BaseModel):
    document_id: str
    equipment: list[GroundTruthEquipment] = Field(default_factory=list)

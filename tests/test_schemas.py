from app.schemas.extraction import EquipmentRecord, FieldValue, SourceSpan


def test_equipment_record_roundtrip() -> None:
    record = EquipmentRecord(
        tag=FieldValue(value="AHU-01", confidence=0.94, source=SourceSpan(page=1, bbox=(1, 2, 3, 4))),
        type=FieldValue(value="Air Handling Unit", confidence=0.9),
        quantity=FieldValue(value=2, confidence=0.88),
        capacity=FieldValue(value="25000 CFM", confidence=0.8),
        manufacturer=FieldValue(value="Trane", confidence=0.7),
    )
    cloned = EquipmentRecord.model_validate(record.model_dump())
    assert cloned.tag.value == "AHU-01"
    assert cloned.tag.source is not None
    assert cloned.tag.source.bbox[0] == 1

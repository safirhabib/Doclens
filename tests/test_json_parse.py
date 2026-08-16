from app.evaluation.failures import classify_failure
from app.extraction.json_parse import parse_model
from app.schemas.evaluation import FailureType
from app.schemas.extraction import ModelExtraction


def test_parse_fenced_json() -> None:
    text = """Here you go
```json
{"equipment": [{"tag": {"value": "G-01", "confidence": 0.9}, "type": {"value": "Emergency Generator", "confidence": 0.9}, "quantity": {"value": "1", "confidence": 0.9}, "capacity": {"value": "450 kW", "confidence": 0.9}, "manufacturer": {"value": "Caterpillar", "confidence": 0.9}}]}
```
"""
    parsed = parse_model(text, ModelExtraction)
    assert parsed.equipment[0].tag.value == "G-01"


def test_unit_interpretation_failure() -> None:
    failure = classify_failure(
        predicted="400 kW",
        ground_truth="400 tons",
        used_ocr=False,
        predicted_in_document=True,
        field="capacity",
    )
    assert failure == FailureType.UNIT_INTERPRETATION

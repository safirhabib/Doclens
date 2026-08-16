from app.evaluation.failures import classify_failure
from app.evaluation.metrics import build_report, compare_extraction
from app.evaluation.normalize import values_match
from app.schemas.evaluation import FailureType
from app.schemas.extraction import EquipmentRecord, ExtractionResult, FieldValue
from app.schemas.ground_truth import GroundTruthDocument, GroundTruthEquipment


def test_values_match_normalizes_capacity() -> None:
    assert values_match("25,000 CFM", "25000 CFM")
    assert values_match(2, "2")
    assert not values_match("450 kW", "500 kW")


def test_compare_extraction_counts_missing_and_correct() -> None:
    truth = GroundTruthDocument(
        document_id="demo",
        equipment=[
            GroundTruthEquipment(
                tag="AHU-01",
                type="Air Handling Unit",
                quantity=2,
                capacity="25000 CFM",
                manufacturer="Trane",
            )
        ],
    )
    result = ExtractionResult(
        document_id="demo",
        filename="demo.pdf",
        strategy="heuristic",
        model="heuristic",
        prompt_version="heuristic",
        latency_ms=10,
        used_ocr=False,
        page_count=1,
        equipment=[
            EquipmentRecord(
                tag=FieldValue(value="AHU-01", confidence=0.9),
                type=FieldValue(value="Air Handling Unit", confidence=0.9),
                quantity=FieldValue(value=2, confidence=0.9),
                capacity=FieldValue(value="25000 CFM", confidence=0.9),
                manufacturer=FieldValue(value=None, confidence=0.1),
            )
        ],
    )
    comparisons = compare_extraction(result, truth)
    report = build_report(
        strategy="heuristic",
        model="heuristic",
        prompt_version="heuristic",
        dataset="demo",
        comparisons=comparisons,
        latency_ms_mean=10,
    )
    assert report.total_fields == 5
    assert report.correct == 4
    assert report.missing == 1
    assert report.accuracy == 80.0


def test_classify_table_layout_for_capacity_confusion() -> None:
    failure = classify_failure(
        predicted="250 kW",
        ground_truth="25000 CFM",
        used_ocr=False,
        predicted_in_document=True,
        field="capacity",
    )
    assert failure == FailureType.TABLE_LAYOUT

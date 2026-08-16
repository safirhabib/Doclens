from app.extraction.heuristic import heuristic_extract
from app.extraction.pipeline import extract_document
from app.vision.pdf import load_pdf


def test_heuristic_extracts_hvac_rows(hvac_pdf) -> None:
    document = load_pdf(hvac_pdf, filename=hvac_pdf.name)
    parsed = heuristic_extract(document)
    tags = [item.tag.value for item in parsed.equipment]
    assert "AHU-01" in tags
    assert "P-101" in tags
    ahu = next(item for item in parsed.equipment if item.tag.value == "AHU-01")
    assert ahu.capacity.value is not None
    assert "25000" in ahu.capacity.value.replace(",", "")


def test_pipeline_heuristic_grounds_tag(hvac_pdf) -> None:
    result = extract_document(hvac_pdf, filename=hvac_pdf.name, strategy="heuristic")
    ahu = next(item for item in result.equipment if item.tag.value == "AHU-01")
    assert ahu.tag.source is not None
    assert ahu.tag.source.page == 1
    assert ahu.tag.confidence > 0.5

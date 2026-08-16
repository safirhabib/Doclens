from app.demo.catalog import CHALLENGE_EQUIPMENT
from app.demo.render import write_challenge_pdf
from app.extraction.pipeline import extract_document
from app.schemas.ground_truth import GroundTruthDocument


def test_challenge_pdf_has_five_answer_rows(tmp_path) -> None:
    pdf = tmp_path / "challenge_messy.pdf"
    write_challenge_pdf(pdf)
    result = extract_document(pdf, filename="challenge_messy.pdf", strategy="heuristic")
    tags = {row.tag.value for row in result.equipment}
    expected = {item.tag for item in CHALLENGE_EQUIPMENT}
    assert expected <= tags
    ahu = next(row for row in result.equipment if row.tag.value == "AHU-01")
    assert ahu.capacity.value is not None
    assert "25000" in str(ahu.capacity.value).replace(",", "")
    assert "kW" not in str(ahu.capacity.value)


def test_challenge_ground_truth_matches_catalog() -> None:
    doc = GroundTruthDocument(document_id="challenge_messy", equipment=CHALLENGE_EQUIPMENT)
    assert len(doc.equipment) == 5
    assert doc.equipment[-1].capacity == "450 kW"

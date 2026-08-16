from fastapi.testclient import TestClient

from app.api.main import app
from app.extraction.client import FakeExtractionClient
from app.schemas.extraction import ModelEquipment, ModelExtraction, ModelField

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extract_heuristic(tiny_pdf_bytes: bytes) -> None:
    response = client.post(
        "/extract",
        data={"strategy": "heuristic"},
        files={"file": ("tiny.pdf", tiny_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "heuristic"
    tags = [row["tag"]["value"] for row in payload["equipment"]]
    assert "AHU-01" in tags


def test_extract_with_fake_vlm(tiny_pdf_bytes: bytes, monkeypatch) -> None:
    fake = FakeExtractionClient(
        equipment=ModelExtraction(
            equipment=[
                ModelEquipment(
                    tag=ModelField(value="AHU-01", confidence=0.99),
                    type=ModelField(value="Air Handling Unit", confidence=0.9),
                    quantity=ModelField(value="2", confidence=0.9),
                    capacity=ModelField(value="25000 CFM", confidence=0.9),
                    manufacturer=ModelField(value="Trane", confidence=0.9),
                )
            ]
        )
    )

    def _extract(source, filename=None, strategy="v2", model=None, client=None):
        from app.extraction.pipeline import extract_document

        return extract_document(source, filename=filename, strategy="v1", model="fake", client=fake)

    monkeypatch.setattr("app.api.main.extract_document", _extract)
    response = client.post(
        "/extract",
        data={"strategy": "v1"},
        files={"file": ("tiny.pdf", tiny_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["equipment"][0]["tag"]["value"] == "AHU-01"


def test_render_page(tiny_pdf_bytes: bytes) -> None:
    response = client.post(
        "/render-page",
        data={"page": 1, "x0": 70, "y0": 690, "x1": 140, "y1": 720},
        files={"file": ("tiny.pdf", tiny_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

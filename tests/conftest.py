from __future__ import annotations

import io
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.demo.render import write_hvac_schedule


@pytest.fixture
def tiny_pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Times-Roman", 14)
    c.drawString(72, 700, "AHU-01  Air Handling Unit  2  25000 CFM  Trane")
    c.save()
    return buf.getvalue()


@pytest.fixture
def hvac_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "hvac_schedule.pdf"
    write_hvac_schedule(path)
    return path

"""Synthetic engineering PDFs for the DocLens demo corpus."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.demo.catalog import GENERATOR_EQUIPMENT, HVAC_EQUIPMENT
from app.schemas.ground_truth import GroundTruthDocument, GroundTruthEquipment

NAVY = colors.HexColor("#1B3A4B")
TEAL = colors.HexColor("#2A9D8F")
LIGHT = colors.HexColor("#F4F1DE")
ROW_ALT = colors.HexColor("#E8F1F2")
WARN = colors.HexColor("#C45C26")


def _header_style() -> ParagraphStyle:
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=16,
        textColor=NAVY,
        spaceAfter=6,
    )


def _meta_style() -> ParagraphStyle:
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        textColor=colors.HexColor("#4A5568"),
        leading=12,
    )


def _body_style() -> ParagraphStyle:
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        textColor=NAVY,
    )


def _build_pdf(path: Path, story: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=path.stem,
        author="DocLens Demo",
    )
    doc.build(story)


def _table_style(header_fill: colors.Color = NAVY) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_fill),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8AA4B0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )


def _rows(equipment: list[GroundTruthEquipment]) -> list[list[str]]:
    header = ["Tag", "Type", "Qty", "Capacity", "Manufacturer"]
    body = [
        [
            item.tag,
            item.type,
            str(item.quantity),
            _display_capacity(item.capacity),
            item.manufacturer or "—",
        ]
        for item in equipment
    ]
    return [header, *body]


def _display_capacity(capacity: str) -> str:
    number, _, unit = capacity.partition(" ")
    if number.isdigit() and len(number) > 3:
        return f"{int(number):,} {unit}".strip()
    return capacity


def write_schedule(
    path: Path,
    *,
    title: str,
    doc_no: str,
    equipment: list[GroundTruthEquipment],
    header_fill: colors.Color | None = None,
    notes: str = "",
) -> None:
    table = Table(_rows(equipment), colWidths=[70, 150, 40, 90, 110])
    table.setStyle(_table_style(header_fill=header_fill or NAVY))
    story: list = [
        Paragraph(title, _header_style()),
        Paragraph(
            f"Project: Harborview Lab Expansion &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Doc No. {doc_no} &nbsp;&nbsp;|&nbsp;&nbsp; Rev. A",
            _meta_style(),
        ),
        Spacer(1, 14),
        table,
    ]
    if notes:
        story.extend([Spacer(1, 16), Paragraph(notes, _meta_style())])
    _build_pdf(path, story)


def write_hvac_schedule(path: Path) -> None:
    write_schedule(
        path,
        title="MECHANICAL EQUIPMENT SCHEDULE",
        doc_no="M-601",
        equipment=HVAC_EQUIPMENT,
        notes="Notes: Capacities are design values at scheduled conditions. Verify nameplate data during commissioning.",
    )


def write_generator_schedule(path: Path) -> None:
    write_schedule(
        path,
        title="EMERGENCY POWER EQUIPMENT SCHEDULE",
        doc_no="E-410",
        equipment=GENERATOR_EQUIPMENT,
        header_fill=colors.HexColor("#6B2D5B"),
        notes="G-01 serves life-safety and standby loads. Standby rating shown.",
    )


def write_messy_schedule(
    path: Path,
    equipment: list[GroundTruthEquipment] | None = None,
    decoy: dict[str, str] | None = None,
    title: str = "HVAC SCHEDULE (DRAFT) — DO NOT USE NOTES COLUMN",
    doc_no: str = "M-601D",
    warning: str | None = None,
) -> None:
    """Column order and a decoy numeric column invite table-association errors."""
    equipment = equipment or HVAC_EQUIPMENT
    decoy = decoy or {
        "AHU-01": "250",
        "AHU-02": "180",
        "P-101": "32",
        "P-102": "18",
        "FCU-03": "12",
        "EF-04": "40",
        "VAV-12": "8",
    }
    header = ["Tag", "MCA (A)", "Qty", "Capacity", "Manufacturer", "Type"]
    body = []
    for item in equipment:
        body.append(
            [
                item.tag,
                decoy.get(item.tag, "15"),
                str(item.quantity),
                _display_capacity(item.capacity),
                item.manufacturer or "—",
                item.type,
            ]
        )
    table = Table([header, *body], colWidths=[60, 55, 35, 85, 100, 120])
    table.setStyle(_table_style(header_fill=WARN))
    story: list = [
        Paragraph(title, _header_style()),
        Paragraph(
            f"Project: Harborview Lab Expansion &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Doc No. {doc_no} &nbsp;&nbsp;|&nbsp;&nbsp; WORKING COPY",
            _meta_style(),
        ),
        Spacer(1, 10),
        Paragraph(
            warning
            or (
                "The MCA (A) column is feeder sizing only. Capacity is the scheduled "
                "airflow or flow rate, not the MCA value. A reviewer note on AHU-01 "
                "says “confirm 250 kW feeder” — that is electrical, not mechanical capacity."
            ),
            _body_style(),
        ),
        Spacer(1, 12),
        table,
    ]
    _build_pdf(path, story)


def write_challenge_pdf(path: Path) -> None:
    """Messy working-copy schedule designed for a human to check against ANSWER_KEY.md."""
    from app.demo.catalog import CHALLENGE_EQUIPMENT

    header = ["Tag", "MCA (A)", "Reviewer notes", "Qty", "Manufacturer", "Capacity", "Type"]
    rows = [
        [
            "AHU-01",
            "250",
            "confirm 250 kW feeder — ELECTRICAL, not AHU capacity",
            "2",
            "Trane",
            "25,000 CFM",
            "Air Handling Unit",
        ],
        [
            "AHU-02",
            "180",
            "OK",
            "1",
            "Carrier",
            "18,000 CFM",
            "Air Handling Unit",
        ],
        [
            "P-101",
            "32",
            "do not copy the 250 from the AHU feeder note",
            "4",
            "Grundfos",
            "250 GPM",
            "Centrifugal Pump",
        ],
        [
            "EF-04",
            "40",
            "—",
            "3",
            "Greenheck",
            "5,000 CFM",
            "Exhaust Fan",
        ],
        [
            "G-01",
            "600",
            "owner wants 500 kW min; SCHEDULED standby rating is 450 kW",
            "1",
            "Caterpillar",
            "450 kW",
            "Emergency Generator",
        ],
    ]
    table = Table([header, *rows], colWidths=[55, 48, 145, 32, 78, 78, 110])
    table.setStyle(_table_style(header_fill=WARN))
    scratch = Table(
        [
            ["Scratch / do not extract", "Value"],
            ["Panel feeder for AHU-01", "250 kW"],
            ["Owner requirement (not a schedule value)", "Generator ≥ 500 kW"],
            ["Old revision G-01 (superseded)", "500 kW nameplate / 450 kW scheduled"],
        ],
        colWidths=[280, 180],
    )
    scratch.setStyle(_table_style(header_fill=colors.HexColor("#6B6B6B")))
    story: list = [
        Paragraph("WORKING COPY — DO NOT ISSUE  ·  M-601X", _header_style()),
        Paragraph(
            "Harborview Lab Expansion &nbsp;&nbsp;|&nbsp;&nbsp; "
            "Columns are NOT in the usual order. MCA and notes are traps.",
            _meta_style(),
        ),
        Spacer(1, 10),
        Paragraph(
            "Read the <b>Capacity</b> column, not MCA and not reviewer notes. "
            "AHU-01 capacity is airflow (CFM), not the 250 kW feeder. "
            "G-01 scheduled capacity is 450 kW even though the owner wants 500 kW.",
            _body_style(),
        ),
        Spacer(1, 12),
        table,
        Spacer(1, 18),
        Paragraph("Red-line scratch pad (not equipment rows)", _meta_style()),
        Spacer(1, 6),
        scratch,
        Spacer(1, 12),
        Paragraph(
            f"{len(CHALLENGE_EQUIPMENT)} equipment rows only. Ignore the scratch pad.",
            _meta_style(),
        ),
    ]
    _build_pdf(path, story)


def write_mixed_notes(path: Path, equipment: list[GroundTruthEquipment]) -> None:
    """Prose-first narrative with a small confirmation table — harder for regex."""
    paragraphs = [
        f"{item.type} {item.tag} is scheduled at quantity {item.quantity} "
        f"with a capacity of {_display_capacity(item.capacity)} "
        f"({item.manufacturer})."
        for item in equipment
    ]
    table = Table(_rows(equipment), colWidths=[70, 150, 40, 90, 110])
    table.setStyle(_table_style())
    story: list = [
        Paragraph("NARRATIVE EQUIPMENT SUMMARY", _header_style()),
        Paragraph(
            "Project: Harborview Lab Expansion &nbsp;&nbsp;|&nbsp;&nbsp; Doc No. M-900",
            _meta_style(),
        ),
        Spacer(1, 10),
        Paragraph(" ".join(paragraphs), _body_style()),
        Spacer(1, 14),
        Paragraph("Confirmation table", _meta_style()),
        Spacer(1, 8),
        table,
    ]
    _build_pdf(path, story)


def write_requirements(path: Path) -> None:
    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "ReqH",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
    )
    story: list = [
        Paragraph("DIVISION 26 / 23 — OWNER PROJECT REQUIREMENTS", _header_style()),
        Paragraph(
            "Harborview Lab Expansion &nbsp;&nbsp;|&nbsp;&nbsp; OPR-2024-08",
            _meta_style(),
        ),
        Spacer(1, 8),
        Paragraph("Emergency Power", heading),
        Paragraph(
            "Emergency generator must have minimum capacity of 500 kW. "
            "The unit shall be diesel standby rated and serve life-safety loads.",
            _body_style(),
        ),
        Paragraph("Air Handling", heading),
        Paragraph(
            "Each air handling unit shall provide a minimum capacity of 10000 CFM "
            "at design cooling conditions.",
            _body_style(),
        ),
        Paragraph("Hydronic Pumps", heading),
        Paragraph(
            "Centrifugal pumps serving primary chilled water shall have a quantity "
            "of at least 2 (duty plus standby or multiple duty).",
            _body_style(),
        ),
        Spacer(1, 16),
        Paragraph(
            "Compliance is determined by comparing scheduled equipment values "
            "against these thresholds. Field verification remains required.",
            _meta_style(),
        ),
    ]
    _build_pdf(path, story)


def rasterize_to_scanned_pdf(source: Path, dest: Path, dpi: int = 110) -> None:
    """Render pages to noisy images so native PDF text is unavailable (OCR path)."""
    import pymupdf as fitz

    src = fitz.open(source)
    out = fitz.open()
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page in src:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        image = ImageOps.grayscale(image).convert("RGB")
        image = ImageEnhance.Contrast(image).enhance(0.85)
        image = ImageEnhance.Brightness(image).enhance(1.05)
        image = image.filter(ImageFilter.SMOOTH)
        noise = Image.effect_noise(image.size, 12).convert("RGB")
        image = Image.blend(image, noise, 0.08)
        image = image.rotate(0.35, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(245, 245, 242))
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=55)
        img_bytes = buf.getvalue()
        rect = page.rect
        new_page = out.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, stream=img_bytes)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest)
    out.close()
    src.close()


def write_ground_truth(path: Path, document_id: str, equipment: list[GroundTruthEquipment]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = GroundTruthDocument(document_id=document_id, equipment=equipment)
    path.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

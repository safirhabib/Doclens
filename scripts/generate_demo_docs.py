#!/usr/bin/env python3
"""Generate the synthetic engineering demo corpus."""

from __future__ import annotations

from app.config import PROJECT_ROOT
from app.demo.catalog import (
    BOILER_EQUIPMENT,
    CHALLENGE_EQUIPMENT,
    CHILLER_EQUIPMENT,
    ELECTRICAL_EQUIPMENT,
    FIRE_EQUIPMENT,
    GENERATOR_EQUIPMENT,
    HVAC_EQUIPMENT,
    KITCHEN_EQUIPMENT,
    LIGHTING_EQUIPMENT,
    MIXED_NOTES_EQUIPMENT,
    PLUMBING_EQUIPMENT,
)
from app.demo.render import (
    rasterize_to_scanned_pdf,
    write_challenge_pdf,
    write_generator_schedule,
    write_ground_truth,
    write_hvac_schedule,
    write_messy_schedule,
    write_mixed_notes,
    write_requirements,
    write_schedule,
)
from reportlab.lib import colors

RAW = PROJECT_ROOT / "data" / "raw"
GT = PROJECT_ROOT / "data" / "ground_truth"


def main() -> None:
    write_hvac_schedule(RAW / "hvac_schedule.pdf")
    write_messy_schedule(RAW / "hvac_schedule_messy.pdf")
    write_generator_schedule(RAW / "generator_schedule.pdf")
    write_requirements(RAW / "requirements.pdf")
    rasterize_to_scanned_pdf(RAW / "hvac_schedule.pdf", RAW / "hvac_schedule_scanned.pdf")

    write_schedule(
        RAW / "plumbing_schedule.pdf",
        title="PLUMBING EQUIPMENT SCHEDULE",
        doc_no="P-210",
        equipment=PLUMBING_EQUIPMENT,
        header_fill=colors.HexColor("#1D4E89"),
    )
    rasterize_to_scanned_pdf(RAW / "plumbing_schedule.pdf", RAW / "plumbing_schedule_scanned.pdf")

    write_schedule(
        RAW / "lighting_schedule.pdf",
        title="LIGHTING FIXTURE SCHEDULE",
        doc_no="E-501",
        equipment=LIGHTING_EQUIPMENT,
        header_fill=colors.HexColor("#C9A227"),
    )
    write_messy_schedule(
        RAW / "lighting_schedule_messy.pdf",
        equipment=LIGHTING_EQUIPMENT,
        decoy={
            "LT-01": "32",
            "LT-02": "9",
            "LT-03": "150",
            "LT-04": "40",
            "LT-05": "5",
        },
        title="LIGHTING SCHEDULE (DRAFT) — WATTS COLUMN IS INPUT, NOT OUTPUT",
        doc_no="E-501D",
        warning=(
            "The MCA (A) column is circuit load only. Capacity is luminous output or "
            "fixture wattage as scheduled. Do not treat input watts as lumens."
        ),
    )

    write_schedule(
        RAW / "boiler_schedule.pdf",
        title="BOILER EQUIPMENT SCHEDULE",
        doc_no="M-410",
        equipment=BOILER_EQUIPMENT,
        header_fill=colors.HexColor("#8C2F39"),
    )
    write_schedule(
        RAW / "chiller_schedule.pdf",
        title="CHILLED WATER EQUIPMENT SCHEDULE",
        doc_no="M-420",
        equipment=CHILLER_EQUIPMENT,
        header_fill=colors.HexColor("#2C6E63"),
    )
    rasterize_to_scanned_pdf(
        RAW / "chiller_schedule.pdf",
        RAW / "chiller_schedule_lowres.pdf",
        dpi=72,
    )
    write_schedule(
        RAW / "electrical_schedule.pdf",
        title="ELECTRICAL DISTRIBUTION SCHEDULE",
        doc_no="E-201",
        equipment=ELECTRICAL_EQUIPMENT,
        header_fill=colors.HexColor("#3D3B30"),
    )
    write_schedule(
        RAW / "fire_schedule.pdf",
        title="FIRE PROTECTION EQUIPMENT SCHEDULE",
        doc_no="FP-101",
        equipment=FIRE_EQUIPMENT,
        header_fill=colors.HexColor("#9B2226"),
    )
    write_schedule(
        RAW / "kitchen_schedule.pdf",
        title="KITCHEN VENTILATION SCHEDULE",
        doc_no="M-710",
        equipment=KITCHEN_EQUIPMENT,
    )
    write_mixed_notes(RAW / "mixed_notes.pdf", MIXED_NOTES_EQUIPMENT)
    write_challenge_pdf(RAW / "challenge_messy.pdf")

    pairs = [
        ("hvac_schedule", HVAC_EQUIPMENT),
        ("hvac_schedule_messy", HVAC_EQUIPMENT),
        ("hvac_schedule_scanned", HVAC_EQUIPMENT),
        ("generator_schedule", GENERATOR_EQUIPMENT),
        ("plumbing_schedule", PLUMBING_EQUIPMENT),
        ("plumbing_schedule_scanned", PLUMBING_EQUIPMENT),
        ("lighting_schedule", LIGHTING_EQUIPMENT),
        ("lighting_schedule_messy", LIGHTING_EQUIPMENT),
        ("boiler_schedule", BOILER_EQUIPMENT),
        ("chiller_schedule", CHILLER_EQUIPMENT),
        ("chiller_schedule_lowres", CHILLER_EQUIPMENT),
        ("electrical_schedule", ELECTRICAL_EQUIPMENT),
        ("fire_schedule", FIRE_EQUIPMENT),
        ("kitchen_schedule", KITCHEN_EQUIPMENT),
        ("mixed_notes", MIXED_NOTES_EQUIPMENT),
        ("challenge_messy", CHALLENGE_EQUIPMENT),
    ]
    for document_id, equipment in pairs:
        write_ground_truth(GT / f"{document_id}.json", document_id, equipment)

    print(f"Wrote {len(pairs)} labeled PDFs to {RAW}")
    print(f"Wrote ground truth to {GT}")


if __name__ == "__main__":
    main()

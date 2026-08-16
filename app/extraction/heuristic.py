from __future__ import annotations

import re

from app.schemas.extraction import ModelEquipment, ModelExtraction, ModelField
from app.vision.boxes import normalize_text
from app.vision.types import DocumentContent

TAG_RE = re.compile(r"\b([A-Z]{1,4}-\d{2,3})\b")
CAPACITY_RE = re.compile(
    r"(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(CFM|kW|GPM|Gpm|cfm|KW|A|MBH|lm|tons|ton|gal|kVA|W)\b",
    re.IGNORECASE,
)
UNIT_NORM = {
    "cfm": "CFM",
    "kw": "kW",
    "gpm": "GPM",
    "a": "A",
    "mbh": "MBH",
    "lm": "lm",
    "tons": "tons",
    "ton": "tons",
    "gal": "gal",
    "kva": "kVA",
    "w": "W",
}

TYPE_HINTS = [
    ("air handling", "Air Handling Unit"),
    ("ahu", "Air Handling Unit"),
    ("makeup air", "Makeup Air Unit"),
    ("exhaust hood", "Exhaust Hood"),
    ("dishwasher", "Dishwasher Exhaust"),
    ("centrifugal pump", "Centrifugal Pump"),
    ("domestic water", "Domestic Water Pump"),
    ("recirc", "Hot Water Recirc Pump"),
    ("boiler circ", "Boiler Circ Pump"),
    ("chw pump", "CHW Pump"),
    ("fire pump", "Fire Pump"),
    ("jockey", "Jockey Pump"),
    ("pump", "Centrifugal Pump"),
    ("fan coil", "Fan Coil Unit"),
    ("exhaust fan", "Exhaust Fan"),
    ("vav", "VAV Box"),
    ("emergency generator", "Emergency Generator"),
    ("generator", "Emergency Generator"),
    ("transfer switch", "Automatic Transfer Switch"),
    ("water heater", "Water Heater"),
    ("storage tank", "Hot Water Storage Tank"),
    ("led troffer", "LED Troffer"),
    ("downlight", "Downlight"),
    ("high bay", "High Bay"),
    ("wall pack", "Wall Pack"),
    ("exit sign", "Exit Sign"),
    ("condensing boiler", "Condensing Boiler"),
    ("hot water boiler", "Hot Water Boiler"),
    ("air-cooled chiller", "Air-Cooled Chiller"),
    ("centrifugal chiller", "Centrifugal Chiller"),
    ("cooling tower", "Cooling Tower"),
    ("panelboard", "Panelboard"),
    ("transformer", "Transformer"),
    ("ups", "UPS"),
    ("fire tank", "Fire Tank"),
]

HEADER_ALIASES = {
    "tag": ("tag", "id", "equipment id", "eq id"),
    "type": ("type", "description", "equipment type"),
    "quantity": ("qty", "quantity", "count"),
    "capacity": ("capacity", "rating"),
    "manufacturer": ("manufacturer", "mfr", "vendor"),
}


def _field(value: str | None, confidence: float) -> ModelField:
    return ModelField(value=value, confidence=confidence)


def _guess_type(blob: str) -> str | None:
    lower = blob.lower()
    for needle, label in TYPE_HINTS:
        if needle in lower:
            return label
    return None


def _manufacturer(blob: str) -> str | None:
    vendors = [
        "Trane",
        "Carrier",
        "Grundfos",
        "Bell & Gossett",
        "Daikin",
        "Greenheck",
        "Titus",
        "Caterpillar",
        "ASCO",
        "AO Smith",
        "Lochinvar",
        "Lithonia",
        "Halo",
        "Holophane",
        "Dual-Lite",
        "Aerco",
        "Viessmann",
        "York",
        "Baltimore Aircoil",
        "Square D",
        "Eaton",
        "Patterson",
        "CST",
        "CaptiveAire",
    ]
    for vendor in vendors:
        if vendor.lower() in blob.lower():
            return vendor
    return None


def _capacity_from(line: str) -> str | None:
    matches = list(CAPACITY_RE.finditer(line))
    if not matches:
        return None
    chosen = matches[0]
    if "mca" in line.lower():
        non_amp = [match for match in matches if match.group(2).lower() != "a"]
        if non_amp:
            chosen = non_amp[0]
    number, unit = chosen.group(1), chosen.group(2)
    return f"{number.replace(',', '')} {UNIT_NORM[unit.lower()]}"


def _header_map(header: list[str | None]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for index, cell in enumerate(header):
        name = normalize_text(cell or "")
        if "mca" in name:
            continue
        for field, aliases in HEADER_ALIASES.items():
            if field in mapping:
                continue
            if name in aliases or any(alias == name or alias in name for alias in aliases):
                mapping[field] = index
    return mapping


def _cell(row: list[str | None], index: int | None) -> str | None:
    if index is None or index >= len(row):
        return None
    value = row[index]
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _from_tables(document: DocumentContent) -> list[ModelEquipment]:
    rows: list[ModelEquipment] = []
    seen: set[str] = set()
    for page in document.pages:
        for table in page.tables:
            if not table:
                continue
            mapping = _header_map(table[0])
            if "tag" not in mapping:
                continue
            for raw in table[1:]:
                tag = _cell(raw, mapping.get("tag"))
                if not tag or not TAG_RE.search(tag) or tag in seen:
                    continue
                seen.add(tag)
                type_val = _cell(raw, mapping.get("type")) or _guess_type(" ".join(str(c or "") for c in raw))
                qty = _cell(raw, mapping.get("quantity"))
                cap_raw = _cell(raw, mapping.get("capacity"))
                capacity = _capacity_from(cap_raw) if cap_raw else _capacity_from(" ".join(str(c or "") for c in raw))
                mfr = _cell(raw, mapping.get("manufacturer")) or _manufacturer(" ".join(str(c or "") for c in raw))
                rows.append(
                    ModelEquipment(
                        tag=_field(TAG_RE.search(tag).group(1), 0.96),
                        type=_field(type_val, 0.9 if type_val else 0.3),
                        quantity=_field(qty, 0.9 if qty else 0.2),
                        capacity=_field(capacity, 0.9 if capacity else 0.2),
                        manufacturer=_field(mfr, 0.9 if mfr else 0.3),
                    )
                )
    return rows


def _parse_line(line: str) -> ModelEquipment | None:
    tag_match = TAG_RE.search(line)
    if not tag_match:
        return None
    tag = tag_match.group(1)
    capacity = _capacity_from(line)
    qty = None
    for match in re.finditer(r"\b(\d{1,3})\b", line):
        token = match.group(1)
        if capacity and token in capacity.replace(",", "").split()[0]:
            continue
        if token == tag.split("-")[-1].lstrip("0") or token == tag.split("-")[-1]:
            continue
        qty = token
        if int(token) < 20:
            break
    return ModelEquipment(
        tag=_field(tag, 0.92),
        type=_field(_guess_type(line), 0.7 if _guess_type(line) else 0.3),
        quantity=_field(qty, 0.75 if qty else 0.2),
        capacity=_field(capacity, 0.8 if capacity else 0.2),
        manufacturer=_field(_manufacturer(line), 0.85 if _manufacturer(line) else 0.3),
    )


def _from_text_blocks(document: DocumentContent) -> list[ModelEquipment]:
    rows: list[ModelEquipment] = []
    seen: set[str] = set()
    for page in document.pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        index = 0
        while index < len(lines):
            if TAG_RE.fullmatch(lines[index]):
                chunk = " ".join(lines[index : index + 6])
                item = _parse_line(chunk)
                index += 1
                if item and item.tag.value not in seen:
                    seen.add(str(item.tag.value))
                    rows.append(item)
                continue
            item = _parse_line(lines[index])
            index += 1
            if item and item.tag.value not in seen:
                seen.add(str(item.tag.value))
                rows.append(item)
    return rows


def heuristic_extract(document: DocumentContent) -> ModelExtraction:
    rows = _from_tables(document)
    if rows:
        return ModelExtraction(equipment=rows)
    return ModelExtraction(equipment=_from_text_blocks(document))

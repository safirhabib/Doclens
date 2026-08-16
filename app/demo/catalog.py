from app.schemas.ground_truth import GroundTruthEquipment

HVAC_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="AHU-01", type="Air Handling Unit", quantity=2, capacity="25000 CFM", manufacturer="Trane"),
    GroundTruthEquipment(tag="AHU-02", type="Air Handling Unit", quantity=1, capacity="18000 CFM", manufacturer="Carrier"),
    GroundTruthEquipment(tag="P-101", type="Centrifugal Pump", quantity=4, capacity="250 GPM", manufacturer="Grundfos"),
    GroundTruthEquipment(tag="P-102", type="Centrifugal Pump", quantity=2, capacity="120 GPM", manufacturer="Bell & Gossett"),
    GroundTruthEquipment(tag="FCU-03", type="Fan Coil Unit", quantity=6, capacity="1200 CFM", manufacturer="Daikin"),
    GroundTruthEquipment(tag="EF-04", type="Exhaust Fan", quantity=3, capacity="5000 CFM", manufacturer="Greenheck"),
    GroundTruthEquipment(tag="VAV-12", type="VAV Box", quantity=8, capacity="800 CFM", manufacturer="Titus"),
]

GENERATOR_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="G-01", type="Emergency Generator", quantity=1, capacity="450 kW", manufacturer="Caterpillar"),
    GroundTruthEquipment(tag="ATS-01", type="Automatic Transfer Switch", quantity=1, capacity="800 A", manufacturer="ASCO"),
]

PLUMBING_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="P-201", type="Domestic Water Pump", quantity=2, capacity="80 GPM", manufacturer="Grundfos"),
    GroundTruthEquipment(tag="P-202", type="Hot Water Recirc Pump", quantity=2, capacity="25 GPM", manufacturer="Bell & Gossett"),
    GroundTruthEquipment(tag="WH-01", type="Water Heater", quantity=1, capacity="199 MBH", manufacturer="AO Smith"),
    GroundTruthEquipment(tag="HWT-01", type="Hot Water Storage Tank", quantity=1, capacity="120 gal", manufacturer="Lochinvar"),
]

LIGHTING_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="LT-01", type="LED Troffer", quantity=24, capacity="4000 lm", manufacturer="Lithonia"),
    GroundTruthEquipment(tag="LT-02", type="Downlight", quantity=12, capacity="800 lm", manufacturer="Halo"),
    GroundTruthEquipment(tag="LT-03", type="High Bay", quantity=6, capacity="24000 lm", manufacturer="Holophane"),
    GroundTruthEquipment(tag="LT-04", type="Wall Pack", quantity=8, capacity="5000 lm", manufacturer="Lithonia"),
    GroundTruthEquipment(tag="LT-05", type="Exit Sign", quantity=16, capacity="2 W", manufacturer="Dual-Lite"),
]

BOILER_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="B-01", type="Hot Water Boiler", quantity=2, capacity="2000 MBH", manufacturer="Aerco"),
    GroundTruthEquipment(tag="B-02", type="Condensing Boiler", quantity=1, capacity="1500 MBH", manufacturer="Viessmann"),
    GroundTruthEquipment(tag="P-301", type="Boiler Circ Pump", quantity=3, capacity="150 GPM", manufacturer="Grundfos"),
]

CHILLER_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="CH-01", type="Centrifugal Chiller", quantity=2, capacity="400 tons", manufacturer="York"),
    GroundTruthEquipment(tag="CH-02", type="Air-Cooled Chiller", quantity=1, capacity="150 tons", manufacturer="Carrier"),
    GroundTruthEquipment(tag="CT-01", type="Cooling Tower", quantity=2, capacity="1200 GPM", manufacturer="Baltimore Aircoil"),
    GroundTruthEquipment(tag="P-401", type="CHW Pump", quantity=4, capacity="800 GPM", manufacturer="Bell & Gossett"),
]

ELECTRICAL_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="PN-01", type="Panelboard", quantity=4, capacity="400 A", manufacturer="Square D"),
    GroundTruthEquipment(tag="PN-02", type="Panelboard", quantity=2, capacity="225 A", manufacturer="Square D"),
    GroundTruthEquipment(tag="UPS-01", type="UPS", quantity=1, capacity="80 kVA", manufacturer="Eaton"),
    GroundTruthEquipment(tag="XF-01", type="Transformer", quantity=2, capacity="500 kVA", manufacturer="Eaton"),
]

FIRE_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="FP-01", type="Fire Pump", quantity=1, capacity="1000 GPM", manufacturer="Patterson"),
    GroundTruthEquipment(tag="J-01", type="Jockey Pump", quantity=1, capacity="10 GPM", manufacturer="Grundfos"),
    GroundTruthEquipment(tag="FT-01", type="Fire Tank", quantity=1, capacity="15000 gal", manufacturer="CST"),
]

KITCHEN_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="KE-01", type="Exhaust Hood", quantity=2, capacity="5000 CFM", manufacturer="CaptiveAire"),
    GroundTruthEquipment(tag="KE-02", type="Makeup Air Unit", quantity=2, capacity="4500 CFM", manufacturer="Greenheck"),
    GroundTruthEquipment(tag="KE-03", type="Dishwasher Exhaust", quantity=1, capacity="800 CFM", manufacturer="Greenheck"),
]

MIXED_NOTES_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="B-01", type="Hot Water Boiler", quantity=2, capacity="2000 MBH", manufacturer="Aerco"),
    GroundTruthEquipment(tag="CH-01", type="Centrifugal Chiller", quantity=2, capacity="400 tons", manufacturer="York"),
    GroundTruthEquipment(tag="G-01", type="Emergency Generator", quantity=1, capacity="450 kW", manufacturer="Caterpillar"),
]

# Walkthrough PDF: traps are intentional. See docs/ANSWER_KEY.md
CHALLENGE_EQUIPMENT: list[GroundTruthEquipment] = [
    GroundTruthEquipment(tag="AHU-01", type="Air Handling Unit", quantity=2, capacity="25000 CFM", manufacturer="Trane"),
    GroundTruthEquipment(tag="AHU-02", type="Air Handling Unit", quantity=1, capacity="18000 CFM", manufacturer="Carrier"),
    GroundTruthEquipment(tag="P-101", type="Centrifugal Pump", quantity=4, capacity="250 GPM", manufacturer="Grundfos"),
    GroundTruthEquipment(tag="EF-04", type="Exhaust Fan", quantity=3, capacity="5000 CFM", manufacturer="Greenheck"),
    GroundTruthEquipment(tag="G-01", type="Emergency Generator", quantity=1, capacity="450 kW", manufacturer="Caterpillar"),
]

# Answer key — `challenge_messy.pdf`

Open the PDF: [`data/raw/challenge_messy.pdf`](../data/raw/challenge_messy.pdf)

There are **exactly 5 equipment rows**. Ignore the scratch pad at the bottom.

## Correct extractions

| Tag | Type | Qty | Capacity | Manufacturer |
| --- | --- | ---: | --- | --- |
| AHU-01 | Air Handling Unit | 2 | 25000 CFM | Trane |
| AHU-02 | Air Handling Unit | 1 | 18000 CFM | Carrier |
| P-101 | Centrifugal Pump | 4 | 250 GPM | Grundfos |
| EF-04 | Exhaust Fan | 3 | 5000 CFM | Greenheck |
| G-01 | Emergency Generator | 1 | 450 kW | Caterpillar |

Commas in the PDF (`25,000 CFM`) are the same value as `25000 CFM`.

## Traps (wrong if the model copies these)

| If the model outputs… | It mixed up… | Correct value |
| --- | --- | --- |
| AHU-01 capacity = **250 kW** or **250** | MCA / “250 kW feeder” note | **25000 CFM** |
| P-101 capacity = **250 kW** | The AHU feeder note sitting near the pump row | **250 GPM** |
| G-01 capacity = **500 kW** | Owner requirement / old nameplate, not the schedule | **450 kW** |
| G-01 capacity = **600** | MCA (A) column | **450 kW** |
| Extra rows from the scratch pad | “Panel feeder 250 kW”, “≥ 500 kW” | not equipment |

## How to check in the UI

1. Extract → `challenge_messy.pdf` → Run extraction
2. For each tag above, compare type / qty / capacity / manufacturer
3. Click **AHU-01** → field **capacity** — highlight should be on **25,000 CFM**, not 250

Machine-readable copy: [`data/ground_truth/challenge_messy.json`](../data/ground_truth/challenge_messy.json)

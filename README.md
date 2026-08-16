# DocLens

Evaluation-driven document intelligence for messy engineering PDFs.

**Live demo:** [https://pod8syfgtn2vnvksqnp9t9.streamlit.app](https://pod8syfgtn2vnvksqnp9t9.streamlit.app)

Upload a schedule → extract structured equipment JSON → ground every field to a page and bounding box → score confidence → compare strategies against ground truth → run an evidence-backed compliance check.

This is **not** a chat-with-PDF app. The design question is: *can you trust an extraction when the input is messy?*

## Results (measured)

| Strategy | Accuracy | Fields | Notes |
| --- | ---: | ---: | --- |
| Heuristic baseline | **77.5%** | 325 | 15 labeled documents, 0.10s/doc |
| v1 Basic LLM | *run locally* | 325 | text-only prompt |
| v2 Schema-guided VLM | *run locally* | 325 | schema + page images |
| v3 Evidence-guided | *run locally* | 325 | extract only if supportable |

Heuristic field accuracy on this corpus:

| Field | Accuracy |
| --- | ---: |
| Tag | 78.5% |
| Type | 78.5% |
| Quantity | 76.9% |
| Capacity | 76.9% |
| Manufacturer | 76.9% |

252 correct / 3 incorrect / 70 missing. Almost all heuristic failures are **missing rows on scanned/low-res PDFs** (no OCR text), not wrong values. That is the gap a VLM strategy is supposed to close.

Do not quote a VLM percentage until `v1`/`v2`/`v3` have been run on this same corpus. See [experiments/EXPERIMENT_04.md](experiments/EXPERIMENT_04.md).

## Architecture

```text
PDF / scan
    → preprocessing (PyMuPDF + optional Tesseract)
    → extraction strategy (heuristic | v1 | v2 | v3)
    → Pydantic JSON
    → visual grounding (word-box search, not model coordinates)
    → confidence calibration
         ├─ Streamlit review
         ├─ evaluation + MLflow
         └─ deterministic compliance + evidence chain
```

## LLM provider

If `GROQ_API_KEY` is set (or `OPENAI_API_KEY` starts with `gsk_`), v1/v2/v3 use Groq (`qwen/qwen3.6-27b`). `XAI_API_KEY` / `GROK_API_KEY` go to xAI Grok. A plain `OPENAI_API_KEY` uses OpenAI. Otherwise extraction falls back to the heuristic baseline.

## Quick start

Walkthrough: **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)**.  
Messy PDF + answers: **[data/raw/challenge_messy.pdf](data/raw/challenge_messy.pdf)** · **[docs/ANSWER_KEY.md](docs/ANSWER_KEY.md)**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add OPENAI_API_KEY for v1/v2/v3
python scripts/generate_demo_docs.py
streamlit run streamlit_app/Home.py
```

Open http://localhost:8501. Uvicorn is optional. Tesseract (`brew install tesseract`) is only needed for scanned PDFs.

## Streamlit Community Cloud

**Public app:** [https://pod8syfgtn2vnvksqnp9t9.streamlit.app](https://pod8syfgtn2vnvksqnp9t9.streamlit.app)

Main file: `streamlit_app/Home.py`. Dependencies: `requirements.txt` (pip). In **Manage app → Settings**, set **Python version to 3.12**, then reboot. Without a model key, heuristic extraction still works.

## Experiments

```bash
python -m app.evaluation.run_experiment --strategy heuristic
python -m app.evaluation.run_experiment --strategy v1
python -m app.evaluation.run_experiment --strategy v2
python -m app.evaluation.run_experiment --strategy v3
```

Reports land in `experiments/results/` and can be logged to local MLflow (`mlflow ui`).

**Experiment 04** (evidence-guided vs basic/schema) is documented in [experiments/EXPERIMENT_04.md](experiments/EXPERIMENT_04.md).

## Compliance demo

`requirements.pdf` vs `generator_schedule.pdf`:

```text
Requirement: Emergency generator ≥ 500 kW
Detected:    G-01 = 450 kW
Result:      NON-COMPLIANT
Evidence:    generator_schedule.pdf + requirements.pdf (page + bbox)
```

The inequality is **deterministic**. The model does not compute 450 ≥ 500.

## Tests

```bash
pytest
```

17 tests. The LLM provider is never called in CI.

## What this does not claim

- VLM bounding boxes are not used as source of truth.
- Confidence is a calibrated heuristic, not a statistically calibrated probability.
- The corpus is synthetic, so evaluation and the 450 vs 500 kW finding are reproducible.

## Layout

```text
app/api            FastAPI
app/vision         PDF render, OCR, word boxes
app/extraction     prompts, OpenAI client, grounding
app/evaluation     metrics, failure taxonomy, MLflow runner
app/agents         requirements + deterministic compliance
data/              raw PDFs + ground truth (15 labeled docs)
experiments/prompts
streamlit_app/
```

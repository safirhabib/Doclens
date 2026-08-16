# DocLens user manual

How to run the app, how to check extraction against known answers, and how the demo is supposed to work.

## Run the app (simplest)

From the project folder:

```bash
source .venv/bin/activate
python scripts/generate_demo_docs.py
streamlit run streamlit_app/Home.py
```

Then open **http://localhost:8501**.

You do **not** need a second terminal. If FastAPI is not running, the UI calls the Python pipeline directly.

### Streamlit Community Cloud

The repo includes `requirements.txt` so Cloud uses **pip**, not Poetry. (A PEP 621 `pyproject.toml` is not Poetry, but Cloud treats it as Poetry if `requirements.txt` is missing.)

After you push:

1. In the Streamlit dashboard: **Manage app → Settings → Python version → 3.12** (`runtime.txt` is ignored).
2. Reboot the app.
3. Optional: **Secrets** — any one of:
   - `GROQ_API_KEY` (Groq, key starts with `gsk_`)
   - `XAI_API_KEY` (xAI Grok)
   - `OPENAI_API_KEY` (OpenAI, or a Groq key pasted in this slot)

   Then reboot. Without a key, heuristic extraction still works.

Heuristic extraction (the default strategy) works with no model key. For v1 / v2 / v3 you need a Groq, xAI, or OpenAI key in `.env` or Streamlit secrets.

### Optional: API + UI (two processes)

Useful if you want the Swagger docs at http://localhost:8000/docs.

```bash
# terminal 1
source .venv/bin/activate
uvicorn app.api.main:app --reload

# terminal 2
source .venv/bin/activate
streamlit run streamlit_app/Home.py
```

### First-time install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/generate_demo_docs.py
```

Scanned PDFs need Tesseract (`brew install tesseract`). Digital PDFs do not.

---

## 5-minute walkthrough (checkable)

### 1. Open the messy PDF yourself

File: [`data/raw/challenge_messy.pdf`](../data/raw/challenge_messy.pdf)

It is a working-copy HVAC/power schedule with **traps**:

- Columns are out of order
- An **MCA (A)** column with numbers like `250`
- Reviewer notes that mention **250 kW** and **500 kW**
- A scratch pad of values that must **not** be extracted as equipment

Correct answers: [`docs/ANSWER_KEY.md`](ANSWER_KEY.md)

### 2. Extract it in the app

1. Sidebar → **Extract**
2. Demo document → `challenge_messy.pdf`
3. Strategy → `heuristic` (or `v1`/`v2`/`v3` if you have a key)
4. Click **Run extraction**
5. Click **AHU-01**, then the **capacity** field. The page highlight should sit on **25,000 CFM**, not on 250.

Compare the table to the answer key. If the model says AHU-01 capacity is `250 kW`, it fell for the feeder note.

### 3. Compliance (known fail)

1. Sidebar → **Compliance**
2. Leave **Use demo PDFs** checked
3. Click **Run compliance**

Expected:

| Requirement | Detected | Result |
| --- | --- | --- |
| Emergency generator ≥ 500 kW | G-01 = 450 kW | **FAIL** |
| AHU ≥ 10,000 CFM | AHU-01 / AHU-02 | pass (if those rows extracted) |
| Pump quantity ≥ 2 | P-101 / P-102 | pass (if those rows extracted) |

The math is deterministic. The model does not decide whether 450 ≥ 500.

### 4. Evaluation lab

1. Sidebar → **Evaluation**
2. Strategy → `heuristic`
3. **Run experiment**

You should see field accuracy for the labeled corpus. **Failures** lists each mismatch with predicted vs ground truth.

---

## Pages

| Page | What it is for |
| --- | --- |
| Home | What DocLens is |
| Extract | Upload or pick a demo PDF; click a row to highlight the source cell |
| Evaluation | Run a strategy on every labeled PDF; compare accuracy |
| Failures | Why a field was wrong |
| Compliance | Requirements PDF vs equipment schedule |

## Strategies

| Strategy | Needs a key? | What it does |
| --- | --- | --- |
| heuristic | no | Reads PDF tables / text with rules |
| v1 | yes | LLM on extracted text only |
| v2 | yes | Schema-guided LLM + page images |
| v3 | yes | Same as v2, but only extract values it can support |

## Files you can open without the app

| File | What it is |
| --- | --- |
| `data/raw/challenge_messy.pdf` | Messy input for the walkthrough |
| `docs/ANSWER_KEY.md` | Human-readable correct answers |
| `data/ground_truth/challenge_messy.json` | Same answers as JSON |
| `data/raw/generator_schedule.pdf` | G-01 = 450 kW |
| `data/raw/requirements.pdf` | Generator must be ≥ 500 kW |

## Troubleshooting

**Extract page says it cannot reach the API**  
Restart Streamlit after pulling these changes. Local mode no longer requires uvicorn.

**Demo list is empty**  
Run `python scripts/generate_demo_docs.py` from the project root.

**Scanned PDFs extract nothing**  
Install Tesseract, or use a digital PDF (`challenge_messy.pdf` is digital).

**v1/v2/v3 fail or silently look like heuristic**  
No model key, or the key is Groq/xAI but the running app is an older deploy. Reboot after pushing. Check secret names: `GROQ_API_KEY`, `XAI_API_KEY`, or `OPENAI_API_KEY`.

# Experiment 04 — Does requiring evidence improve extraction?

**Question:** Does an evidence-guided prompt (page/cell support + confidence) improve field accuracy versus basic and schema-guided extraction?

**Setup**

- Dataset: synthetic Harborview schedules in `data/raw/` with labels in `data/ground_truth/`
- Same corpus for every strategy
- Grounding still computed from PDF word boxes (model coordinates are not trusted)
- LLM provider: OpenAI-compatible API if `OPENAI_API_KEY` is set

**Strategies**

| ID | Idea |
| --- | --- |
| heuristic | Table/regex baseline, no LLM |
| v1 | Basic text extraction |
| v2 | Schema-guided + page images |
| v3 | Evidence-guided (only extract values you can support) |

**How to run**

```bash
python scripts/generate_demo_docs.py
python -m app.evaluation.run_experiment --strategy heuristic
python -m app.evaluation.run_experiment --strategy v1
python -m app.evaluation.run_experiment --strategy v2
python -m app.evaluation.run_experiment --strategy v3
```

**Measured baseline (this repo, heuristic, 15 documents):**

```text
Accuracy: 77.5%
Fields:   325
Correct:  252
Missing:  70   (mostly scanned/low-res pages)
Incorrect: 3
Latency:  0.10s / document
```

Fill in v1/v2/v3 below after running them. Do not invent those numbers.

**Hypothesis:** v3 (evidence-guided) beats v1 (basic text) on messy/scanned files, with some extra latency. v2 (schema + images) should beat v1 on table-column association.

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

API_URL = os.getenv("DOCLENS_API_URL", "http://localhost:8000")
TIMEOUT = httpx.Timeout(180.0)


def _http() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=TIMEOUT)


def api_available() -> bool:
    try:
        with _http() as client:
            response = client.get("/health", timeout=1.5)
            return response.status_code == 200
    except Exception:
        return False


def _raw_dir() -> Path:
    from app.config import get_settings

    return get_settings().data_dir / "raw"


def health() -> dict:
    if api_available():
        with _http() as client:
            return client.get("/health").json()
    provider = "heuristic"
    try:
        from app.llm import resolve_llm

        llm = resolve_llm()
        if llm:
            provider = llm.provider
    except Exception:
        pass
    return {"status": "ok", "llm_provider": provider, "mode": "local"}


def list_demo_documents() -> list[dict]:
    if api_available():
        with _http() as client:
            response = client.get("/demo/documents")
            response.raise_for_status()
            return response.json()
    from app.config import get_settings

    settings = get_settings()
    raw = settings.data_dir / "raw"
    gt = settings.data_dir / "ground_truth"
    if not raw.exists():
        return []
    return [
        {
            "filename": path.name,
            "document_id": path.stem,
            "has_ground_truth": (gt / f"{path.stem}.json").exists(),
        }
        for path in sorted(raw.glob("*.pdf"))
    ]


def download_demo(filename: str) -> bytes:
    if api_available():
        with _http() as client:
            response = client.get(f"/demo/file/{filename}")
            response.raise_for_status()
            return response.content
    path = (_raw_dir() / filename).resolve()
    if not path.exists() or _raw_dir().resolve() not in path.parents:
        raise FileNotFoundError(filename)
    return path.read_bytes()


def extract(file_bytes: bytes, filename: str, strategy: str, model: str | None) -> dict:
    if api_available():
        data = {"strategy": strategy}
        if model:
            data["model"] = model
        with _http() as client:
            response = client.post(
                "/extract",
                data=data,
                files={"file": (filename, file_bytes, "application/pdf")},
            )
            response.raise_for_status()
            return response.json()
    from app.extraction.pipeline import extract_document

    return extract_document(
        file_bytes, filename=filename, strategy=strategy, model=model
    ).model_dump()


def render_page(
    file_bytes: bytes,
    filename: str,
    page: int,
    bbox: list[float] | None = None,
) -> bytes:
    if api_available():
        data: dict[str, str | int | float] = {"page": page}
        if bbox and len(bbox) == 4:
            data.update({"x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]})
        with _http() as client:
            response = client.post(
                "/render-page",
                data=data,
                files={"file": (filename, file_bytes, "application/pdf")},
            )
            response.raise_for_status()
            return response.content
    from app.schemas.extraction import SourceSpan
    from app.vision.pdf import render_page_highlight

    highlight = None
    if bbox and len(bbox) == 4:
        highlight = SourceSpan(page=page, bbox=(bbox[0], bbox[1], bbox[2], bbox[3]))
    return render_page_highlight(file_bytes, page_number=page, highlight=highlight)


def evaluate(strategy: str, model: str | None = None, log_mlflow: bool = False) -> dict:
    if api_available():
        params: dict[str, str | bool] = {"strategy": strategy, "log_mlflow": log_mlflow}
        if model:
            params["model"] = model
        with _http() as client:
            response = client.post("/evaluate", params=params)
            response.raise_for_status()
            return response.json()
    from app.evaluation.run_experiment import run_experiment

    return run_experiment(strategy=strategy, model=model, log_mlflow=log_mlflow).model_dump()


def evaluate_result(result: dict) -> dict:
    if api_available():
        with _http() as client:
            response = client.post("/evaluate-result", json=result)
            response.raise_for_status()
            return response.json()
    from app.config import get_settings
    from app.evaluation.metrics import build_report, compare_extraction
    from app.schemas.extraction import ExtractionResult
    from app.schemas.ground_truth import GroundTruthDocument
    from app.vision.pdf import load_pdf

    parsed = ExtractionResult.model_validate(result)
    settings = get_settings()
    gt_path = settings.data_dir / "ground_truth" / f"{parsed.document_id}.json"
    truth = GroundTruthDocument.model_validate_json(gt_path.read_text(encoding="utf-8"))
    raw = settings.data_dir / "raw" / parsed.filename
    document_text = load_pdf(raw, filename=parsed.filename).full_text if raw.exists() else ""
    comparisons = compare_extraction(parsed, truth, document_text=document_text)
    return build_report(
        strategy=parsed.strategy,
        model=parsed.model,
        prompt_version=parsed.prompt_version,
        dataset=parsed.document_id,
        comparisons=comparisons,
        latency_ms_mean=parsed.latency_ms,
    ).model_dump()


def list_experiments() -> list[dict]:
    if api_available():
        with _http() as client:
            response = client.get("/experiments")
            response.raise_for_status()
            return response.json()
    from app.config import get_settings
    from app.schemas.evaluation import EvalReport

    settings = get_settings()
    if not settings.results_dir.exists():
        return []
    reports = []
    for path in sorted(settings.results_dir.glob("*.json")):
        payload = EvalReport.model_validate_json(path.read_text(encoding="utf-8")).model_dump()
        payload["filename"] = path.name
        reports.append(payload)
    return reports


def compliance(
    requirements: bytes,
    requirements_name: str,
    schedule: bytes,
    schedule_name: str,
    strategy: str,
    model: str | None = None,
) -> dict:
    if api_available():
        data = {"strategy": strategy}
        if model:
            data["model"] = model
        with _http() as client:
            response = client.post(
                "/compliance",
                data=data,
                files={
                    "requirements": (requirements_name, requirements, "application/pdf"),
                    "schedule": (schedule_name, schedule, "application/pdf"),
                },
            )
            response.raise_for_status()
            return response.json()
    from app.agents.pipeline import run_compliance

    return run_compliance(
        requirements,
        schedule,
        requirements_filename=requirements_name,
        schedule_filename=schedule_name,
        strategy=strategy,
        model=model,
    ).model_dump()

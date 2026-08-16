from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.agents.pipeline import run_compliance
from app.config import get_settings
from app.evaluation.metrics import build_report, compare_extraction
from app.evaluation.run_experiment import run_experiment
from app.extraction.pipeline import STRATEGIES, extract_document
from app.schemas.evaluation import EvalReport
from app.schemas.extraction import ExtractionResult, SourceSpan
from app.schemas.ground_truth import GroundTruthDocument
from app.vision.pdf import load_pdf, render_page_highlight

app = FastAPI(title="DocLens", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    from app.llm import resolve_llm

    llm = resolve_llm()
    provider = llm.provider if llm else "heuristic"
    return {"status": "ok", "llm_provider": provider}


@app.get("/demo/documents")
def list_demo_documents() -> list[dict]:
    settings = get_settings()
    raw = settings.data_dir / "raw"
    gt = settings.data_dir / "ground_truth"
    if not raw.exists():
        return []
    items = []
    for path in sorted(raw.glob("*.pdf")):
        items.append(
            {
                "filename": path.name,
                "document_id": path.stem,
                "has_ground_truth": (gt / f"{path.stem}.json").exists(),
            }
        )
    return items


@app.get("/demo/file/{filename}")
def get_demo_file(filename: str) -> FileResponse:
    settings = get_settings()
    path = (settings.data_dir / "raw" / filename).resolve()
    raw = (settings.data_dir / "raw").resolve()
    if raw not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Unknown demo file")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.post("/extract", response_model=ExtractionResult)
async def extract(
    file: UploadFile = File(...),
    strategy: str = Form("v2"),
    model: str | None = Form(None),
) -> ExtractionResult:
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"strategy must be one of {STRATEGIES}")
    data = await file.read()
    return extract_document(
        data,
        filename=file.filename or "document.pdf",
        strategy=strategy,
        model=model,
    )


@app.post("/render-page")
async def render_page(
    file: UploadFile = File(...),
    page: int = Form(...),
    x0: float | None = Form(None),
    y0: float | None = Form(None),
    x1: float | None = Form(None),
    y1: float | None = Form(None),
) -> Response:
    data = await file.read()
    highlight = None
    if None not in (x0, y0, x1, y1):
        highlight = SourceSpan(page=page, bbox=(x0, y0, x1, y1))
    png = render_page_highlight(data, page_number=page, highlight=highlight)
    return Response(content=png, media_type="image/png")


@app.post("/evaluate", response_model=EvalReport)
def evaluate(
    strategy: str = "heuristic",
    model: str | None = None,
    log_mlflow: bool = False,
) -> EvalReport:
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=400, detail=f"strategy must be one of {STRATEGIES}")
    return run_experiment(strategy=strategy, model=model, log_mlflow=log_mlflow)


@app.post("/evaluate-result", response_model=EvalReport)
async def evaluate_result(
    result: ExtractionResult,
) -> EvalReport:
    settings = get_settings()
    gt_path = settings.data_dir / "ground_truth" / f"{result.document_id}.json"
    if not gt_path.exists():
        raise HTTPException(status_code=404, detail="No ground truth for this document")
    truth = GroundTruthDocument.model_validate_json(gt_path.read_text(encoding="utf-8"))
    raw = settings.data_dir / "raw" / result.filename
    document_text = ""
    if raw.exists():
        document_text = load_pdf(raw, filename=result.filename).full_text
    comparisons = compare_extraction(result, truth, document_text=document_text)
    return build_report(
        strategy=result.strategy,
        model=result.model,
        prompt_version=result.prompt_version,
        dataset=result.document_id,
        comparisons=comparisons,
        latency_ms_mean=result.latency_ms,
    )


@app.get("/experiments")
def list_experiments() -> list[dict]:
    settings = get_settings()
    results = settings.results_dir
    if not results.exists():
        return []
    reports = []
    for path in sorted(results.glob("*.json")):
        report = EvalReport.model_validate_json(path.read_text(encoding="utf-8"))
        payload = report.model_dump()
        payload["filename"] = path.name
        reports.append(payload)
    return reports


@app.post("/compliance")
async def compliance(
    requirements: UploadFile = File(...),
    schedule: UploadFile = File(...),
    strategy: str = Form("heuristic"),
    model: str | None = Form(None),
):
    req_bytes = await requirements.read()
    sched_bytes = await schedule.read()
    return run_compliance(
        req_bytes,
        sched_bytes,
        requirements_filename=requirements.filename or "requirements.pdf",
        schedule_filename=schedule.filename or "schedule.pdf",
        strategy=strategy,
        model=model,
    )


def create_app() -> FastAPI:
    return app

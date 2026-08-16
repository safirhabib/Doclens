from __future__ import annotations

import argparse
from pathlib import Path

from app.config import get_settings
from app.evaluation.metrics import build_report, compare_extraction
from app.extraction.client import ExtractionClient, default_model
from app.extraction.pipeline import STRATEGIES, extract_document
from app.schemas.evaluation import EvalReport, FieldComparison
from app.schemas.ground_truth import GroundTruthDocument
from app.vision.pdf import load_pdf


def labeled_pdfs() -> list[Path]:
    settings = get_settings()
    raw_dir = settings.data_dir / "raw"
    gt_dir = settings.data_dir / "ground_truth"
    files = []
    for path in sorted(raw_dir.glob("*.pdf")):
        if (gt_dir / f"{path.stem}.json").exists():
            files.append(path)
    return files


def _gt_path(raw_name: str) -> Path:
    settings = get_settings()
    return settings.data_dir / "ground_truth" / f"{Path(raw_name).stem}.json"


def evaluate_file(
    pdf_path: Path,
    strategy: str,
    model: str | None,
    client: ExtractionClient | None = None,
) -> tuple[list[FieldComparison], float, str, str]:
    truth = GroundTruthDocument.model_validate_json(_gt_path(pdf_path.name).read_text(encoding="utf-8"))
    result = extract_document(
        pdf_path,
        filename=pdf_path.name,
        strategy=strategy,
        model=model,
        client=client,
    )
    document = load_pdf(pdf_path, filename=pdf_path.name)
    comparisons = compare_extraction(result, truth, document_text=document.full_text)
    return comparisons, result.latency_ms, result.model, result.prompt_version


def run_experiment(
    strategy: str = "heuristic",
    model: str | None = None,
    dataset: str = "demo",
    client: ExtractionClient | None = None,
    log_mlflow: bool = True,
) -> EvalReport:
    comparisons: list[FieldComparison] = []
    latencies: list[float] = []
    model_name = model or default_model()
    prompt_version = strategy

    files = labeled_pdfs()
    for path in files:
        rows, latency, used_model, prompt_version = evaluate_file(path, strategy, model, client)
        comparisons.extend(rows)
        latencies.append(latency)
        model_name = used_model

    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
    report = build_report(
        strategy=strategy,
        model=model_name,
        prompt_version=prompt_version,
        dataset=dataset,
        comparisons=comparisons,
        latency_ms_mean=mean_latency,
    )

    settings = get_settings()
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    out = settings.results_dir / f"{strategy}_{model_name.replace('/', '-')}.json"
    out.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    if log_mlflow:
        try:
            import mlflow
        except ImportError:
            log_mlflow = False
    if log_mlflow:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment("doclens-extraction")
        with mlflow.start_run(run_name=f"{strategy}-{model_name}"):
            mlflow.log_params(
                {
                    "strategy": strategy,
                    "model": model_name,
                    "prompt_version": prompt_version,
                    "dataset": dataset,
                    "documents": len(files),
                    "temperature": 0,
                }
            )
            mlflow.log_metrics(
                {
                    "accuracy": report.accuracy,
                    "latency_ms_mean": report.latency_ms_mean,
                    "correct": report.correct,
                    "incorrect": report.incorrect,
                    "missing": report.missing,
                    **{f"acc_{k}": v for k, v in report.field_accuracy.items()},
                    **{f"fail_{k}": v for k, v in report.failure_counts.items()},
                }
            )
            mlflow.log_artifact(str(out))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a DocLens extraction experiment")
    parser.add_argument("--strategy", default="heuristic", choices=list(STRATEGIES))
    parser.add_argument("--model", default=None)
    parser.add_argument("--dataset", default="demo")
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()
    report = run_experiment(
        strategy=args.strategy,
        model=args.model,
        dataset=args.dataset,
        log_mlflow=not args.no_mlflow,
    )
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

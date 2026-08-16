from __future__ import annotations

from pathlib import Path

from app.config import PROJECT_ROOT, get_settings
from app.schemas.evaluation import EvalReport


def load_reports() -> list[EvalReport]:
    settings = get_settings()
    reports = []
    for path in sorted(settings.results_dir.glob("*.json")):
        reports.append(EvalReport.model_validate_json(path.read_text(encoding="utf-8")))
    return reports


def markdown_table(reports: list[EvalReport]) -> str:
    lines = [
        "| Strategy | Model | Accuracy | Correct | Incorrect | Missing | Fields | Latency |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in sorted(reports, key=lambda item: item.accuracy):
        lines.append(
            f"| {report.strategy} | {report.model} | {report.accuracy:.1f}% | "
            f"{report.correct} | {report.incorrect} | {report.missing} | "
            f"{report.total_fields} | {report.latency_ms_mean/1000:.2f}s |"
        )
    return "\n".join(lines)


def write_results_md(path: Path | None = None) -> Path:
    reports = load_reports()
    dest = path or (PROJECT_ROOT / "experiments" / "RESULTS.md")
    heuristic = next((report for report in reports if report.strategy == "heuristic"), None)
    best = max(reports, key=lambda report: report.accuracy) if reports else None
    parts = ["# DocLens extraction results\n", markdown_table(reports), ""]
    if heuristic and best and best.strategy != "heuristic":
        delta = best.accuracy - heuristic.accuracy
        parts.append(
            f"Best strategy **{best.strategy}** ({best.model}) improved field accuracy "
            f"from **{heuristic.accuracy:.1f}%** to **{best.accuracy:.1f}%** "
            f"(+{delta:.1f} points) on {best.total_fields} fields.\n"
        )
    if best:
        parts.append("## Field accuracy (best run)\n")
        for field, value in sorted(best.field_accuracy.items()):
            parts.append(f"- {field}: {value:.1f}%")
        parts.append("\n## Failure counts (best run)\n")
        for name, count in sorted(best.failure_counts.items(), key=lambda kv: -kv[1]):
            parts.append(f"- {name}: {count}")
        parts.append("")
    dest.write_text("\n".join(parts), encoding="utf-8")
    return dest

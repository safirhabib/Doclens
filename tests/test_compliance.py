from app.agents.compare import apply_operator
from app.agents.pipeline import run_compliance
from app.demo.render import write_generator_schedule, write_requirements
from app.schemas.compliance import ComplianceResult, Operator


def test_450_kw_fails_500_kw_minimum() -> None:
    assert apply_operator(450, Operator.GTE, 500) is False
    assert apply_operator(25000, Operator.GTE, 10000) is True


def test_demo_generator_is_non_compliant(tmp_path) -> None:
    req = tmp_path / "requirements.pdf"
    sched = tmp_path / "generator_schedule.pdf"
    write_requirements(req)
    write_generator_schedule(sched)
    report = run_compliance(
        req,
        sched,
        requirements_filename="requirements.pdf",
        schedule_filename="generator_schedule.pdf",
        strategy="heuristic",
    )
    capacity_findings = [
        finding
        for finding in report.findings
        if finding.requirement.metric == "capacity"
        and "generator" in (finding.requirement.equipment_type or "").lower()
    ]
    assert capacity_findings
    finding = capacity_findings[0]
    assert finding.result == ComplianceResult.FAIL
    assert finding.detected_tag == "G-01"
    assert "450" in (finding.detected_value or "")
    steps = [step.step for step in finding.evidence_chain]
    assert "deterministic_comparison" in steps
    assert report.failed >= 1

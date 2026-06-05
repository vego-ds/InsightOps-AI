from pathlib import Path

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.api.contracts import AnalysisResponse
from insightops.charts.chart_data import SalesChartData
from insightops.insights.generator import ExecutiveInsightReport
from insightops.metrics.kpis import SalesKPIResult
from insightops.pipeline.sample_analysis import analyze_sample_sales_data
from insightops.reports.artifacts import ReportArtifact
from insightops.reports.markdown_report import (
    generate_executive_markdown_report,
)
from insightops.security.policy import SecurityScanResult
from insightops.validation.report import ValidationReport


def test_generate_executive_markdown_report_creates_output_directory(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "reports"

    generate_executive_markdown_report(
        analyze_sample_sales_data(),
        str(output_dir),
    )

    assert output_dir.exists()


def test_generate_executive_markdown_report_creates_markdown_file(
    tmp_path: Path,
) -> None:
    artifact = generate_executive_markdown_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )

    assert isinstance(artifact, ReportArtifact)
    assert artifact.file_name == "executive_sales_report.md"
    assert artifact.file_name.endswith(".md")
    assert Path(artifact.file_path).exists()


def test_markdown_report_contains_expected_sections(tmp_path: Path) -> None:
    artifact = generate_executive_markdown_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )
    report_text = Path(artifact.file_path).read_text()

    assert "Executive Sales Report" in report_text
    assert "Data Quality" in report_text
    assert "KPI Summary" in report_text
    assert "Executive Insights" in report_text
    assert "Audit Events" in report_text


def test_markdown_report_is_deterministic_for_same_input(tmp_path: Path) -> None:
    analysis = analyze_sample_sales_data()

    first_artifact = generate_executive_markdown_report(analysis, str(tmp_path))
    first_text = Path(first_artifact.file_path).read_text()

    second_artifact = generate_executive_markdown_report(analysis, str(tmp_path))
    second_text = Path(second_artifact.file_path).read_text()

    assert first_artifact == second_artifact
    assert first_text == second_text


def test_minimal_analysis_input_does_not_crash(tmp_path: Path) -> None:
    artifact = generate_executive_markdown_report(
        _minimal_analysis_response(),
        str(tmp_path),
    )

    report_text = Path(artifact.file_path).read_text()

    assert "No anomalies detected" in report_text
    assert "No audit events" in report_text


def _minimal_analysis_response() -> AnalysisResponse:
    return AnalysisResponse(
        validation=ValidationReport(total_rows=0, valid_rows=0, invalid_rows=0),
        kpis=SalesKPIResult(
            total_revenue=0.0,
            total_orders=0,
            total_units_sold=0,
            average_order_value=0.0,
        ),
        security=SecurityScanResult(
            prompt_injection_detected=False,
            flagged_fields=[],
            human_review_required=False,
        ),
        anomalies=AnomalyDetectionResult(total_anomalies=0, anomalies=[]),
        charts=SalesChartData(charts=[]),
        insights=ExecutiveInsightReport(
            summary="No notable issues.",
            insights=[],
            recommended_actions=[],
        ),
        audit_events=[],
    )

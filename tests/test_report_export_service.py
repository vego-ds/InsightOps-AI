from pathlib import Path

import pytest

from insightops.pipeline.sample_analysis import analyze_sample_sales_data
from insightops.reports.export_service import (
    ReportExportResult,
    ReportGenerationBlockedError,
    UnsupportedReportFormatError,
    export_analysis_report,
)


def test_markdown_export_returns_report_result() -> None:
    report = export_analysis_report(analyze_sample_sales_data(), "markdown")

    assert isinstance(report, ReportExportResult)
    assert report.report_id == "executive_sales_report"
    assert report.file_name == "executive_sales_report.md"
    assert report.format == "markdown"
    assert report.media_type == "text/markdown"
    assert b"Executive Sales Report" in report.content
    assert report.size_bytes == len(report.content)


def test_pdf_export_returns_report_result() -> None:
    report = export_analysis_report(analyze_sample_sales_data(), "pdf")

    assert report.file_name == "executive_sales_report.pdf"
    assert report.format == "pdf"
    assert report.media_type == "application/pdf"
    assert report.content.startswith(b"%PDF")
    assert report.size_bytes == len(report.content)


def test_markdown_alias_is_supported() -> None:
    report = export_analysis_report(analyze_sample_sales_data(), "md")

    assert report.format == "markdown"
    assert report.file_name == "executive_sales_report.md"


def test_invalid_report_format_raises_controlled_error() -> None:
    with pytest.raises(UnsupportedReportFormatError):
        export_analysis_report(analyze_sample_sales_data(), "xlsx")


def test_quality_gate_blocks_report_generation() -> None:
    analysis = analyze_sample_sales_data()
    analysis.quality_gate.can_generate_reports = False

    with pytest.raises(ReportGenerationBlockedError):
        export_analysis_report(analysis, "pdf")


def test_report_export_does_not_persist_files_in_repository() -> None:
    export_analysis_report(analyze_sample_sales_data(), "markdown")
    export_analysis_report(analyze_sample_sales_data(), "pdf")

    assert not Path("executive_sales_report.md").exists()
    assert not Path("executive_sales_report.pdf").exists()

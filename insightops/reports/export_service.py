from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel, Field

from insightops.api.contracts import AnalysisResponse
from insightops.reports.markdown_report import generate_executive_markdown_report
from insightops.reports.pdf_report import generate_executive_pdf_report

REPORT_ID = "executive_sales_report"


class UnsupportedReportFormatError(ValueError):
    pass


class ReportGenerationBlockedError(ValueError):
    pass


class ReportExportResult(BaseModel):
    report_id: str
    file_name: str
    format: str
    media_type: str
    size_bytes: int
    content: bytes = Field(repr=False)


def export_analysis_report(
    analysis: AnalysisResponse,
    report_format: str = "pdf",
) -> ReportExportResult:
    normalized_format = normalize_report_format(report_format)
    if not analysis.quality_gate.can_generate_reports:
        raise ReportGenerationBlockedError(
            "Report generation is blocked by the quality gate."
        )

    with TemporaryDirectory() as output_dir:
        if normalized_format == "markdown":
            artifact = generate_executive_markdown_report(
                analysis,
                output_dir,
                report_id=REPORT_ID,
            )
            media_type = "text/markdown"
        else:
            artifact = generate_executive_pdf_report(
                analysis,
                output_dir,
                report_id=REPORT_ID,
            )
            media_type = "application/pdf"

        report_path = Path(artifact.file_path)
        content = report_path.read_bytes()

    return ReportExportResult(
        report_id=REPORT_ID,
        file_name=artifact.file_name,
        format=normalized_format,
        media_type=media_type,
        size_bytes=len(content),
        content=content,
    )


def normalize_report_format(report_format: str) -> str:
    normalized = report_format.strip().casefold()
    if normalized == "md":
        return "markdown"
    if normalized in {"markdown", "pdf"}:
        return normalized
    raise UnsupportedReportFormatError(
        "Unsupported report format. Use 'pdf' or 'markdown'."
    )

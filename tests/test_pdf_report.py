from pathlib import Path

from tests.test_markdown_report import _minimal_analysis_response

from insightops.pipeline.sample_analysis import analyze_sample_sales_data
from insightops.reports.artifacts import ReportArtifact
from insightops.reports.pdf_report import generate_executive_pdf_report


def test_generate_executive_pdf_report_creates_output_directory(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "reports"

    generate_executive_pdf_report(analyze_sample_sales_data(), str(output_dir))

    assert output_dir.exists()


def test_generate_executive_pdf_report_creates_pdf_file(tmp_path: Path) -> None:
    artifact = generate_executive_pdf_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )

    assert isinstance(artifact, ReportArtifact)
    assert artifact.format == "pdf"
    assert artifact.file_name == "executive_sales_report.pdf"
    assert artifact.file_name.endswith(".pdf")
    assert Path(artifact.file_path).exists()


def test_generated_pdf_has_pdf_header_and_content(tmp_path: Path) -> None:
    artifact = generate_executive_pdf_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )
    pdf_path = Path(artifact.file_path)

    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert pdf_path.stat().st_size > 0


def test_pdf_report_generation_handles_profile_and_quality_score(
    tmp_path: Path,
) -> None:
    artifact = generate_executive_pdf_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )

    assert Path(artifact.file_path).exists()


def test_pdf_report_generation_handles_lifecycle_sections(
    tmp_path: Path,
) -> None:
    artifact = generate_executive_pdf_report(
        analyze_sample_sales_data(),
        str(tmp_path),
    )

    assert Path(artifact.file_path).exists()


def test_generate_executive_pdf_report_can_run_twice(tmp_path: Path) -> None:
    analysis = analyze_sample_sales_data()

    first_artifact = generate_executive_pdf_report(analysis, str(tmp_path))
    second_artifact = generate_executive_pdf_report(analysis, str(tmp_path))

    assert first_artifact == second_artifact
    assert Path(second_artifact.file_path).exists()


def test_minimal_analysis_input_does_not_crash(tmp_path: Path) -> None:
    artifact = generate_executive_pdf_report(
        _minimal_analysis_response(),
        str(tmp_path),
    )

    assert Path(artifact.file_path).exists()
    assert Path(artifact.file_path).read_bytes().startswith(b"%PDF")

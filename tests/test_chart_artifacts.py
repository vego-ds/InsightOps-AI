from pathlib import Path

from insightops.charts.artifacts import render_chart_artifacts
from insightops.charts.chart_data import (
    ChartDataPoint,
    ChartSeries,
    SalesChartData,
)


def test_render_chart_artifacts_creates_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "charts"

    render_chart_artifacts(_chart_data(), str(output_dir))

    assert output_dir.exists()


def test_render_chart_artifacts_creates_png_files_for_series(
    tmp_path: Path,
) -> None:
    result = render_chart_artifacts(_chart_data(), str(tmp_path))

    assert result.total_artifacts == 2

    for artifact in result.artifacts:
        assert artifact.chart_id
        assert artifact.title
        assert artifact.chart_type
        assert artifact.file_path
        assert artifact.file_name.endswith(".png")
        assert Path(artifact.file_path).exists()


def test_empty_chart_data_returns_zero_artifacts(tmp_path: Path) -> None:
    result = render_chart_artifacts(SalesChartData(charts=[]), str(tmp_path))

    assert result.total_artifacts == 0
    assert result.artifacts == []


def test_empty_chart_series_creates_placeholder_png(tmp_path: Path) -> None:
    chart_data = SalesChartData(
        charts=[
            ChartSeries(
                chart_id="empty_chart",
                title="Empty Chart",
                chart_type="bar",
                metric="revenue",
                x_axis="region",
                y_axis="revenue",
                data=[],
            )
        ]
    )

    result = render_chart_artifacts(chart_data, str(tmp_path))

    assert result.total_artifacts == 1
    artifact = result.artifacts[0]
    assert artifact.file_name == "empty_chart.png"
    assert Path(artifact.file_path).exists()


def _chart_data() -> SalesChartData:
    return SalesChartData(
        charts=[
            ChartSeries(
                chart_id="revenue_by_region",
                title="Revenue by Region",
                chart_type="bar",
                metric="revenue",
                x_axis="region",
                y_axis="revenue",
                data=[
                    ChartDataPoint(label="North", value=300.0),
                    ChartDataPoint(label="West", value=200.0),
                ],
            ),
            ChartSeries(
                chart_id="anomalies_by_severity",
                title="Anomalies by Severity",
                chart_type="bar",
                metric="anomaly_count",
                x_axis="severity",
                y_axis="count",
                data=[ChartDataPoint(label="high", value=1)],
            ),
        ]
    )

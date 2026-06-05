from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pydantic import BaseModel, Field

from insightops.charts.chart_data import ChartSeries, SalesChartData


class ChartArtifact(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    file_path: str
    file_name: str


class ChartArtifactResult(BaseModel):
    total_artifacts: int
    artifacts: list[ChartArtifact] = Field(default_factory=list)


def render_chart_artifacts(
    chart_data: SalesChartData,
    output_dir: str,
) -> ChartArtifactResult:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    artifacts = [
        _render_chart_series(chart, output_path)
        for chart in chart_data.charts
    ]

    return ChartArtifactResult(
        total_artifacts=len(artifacts),
        artifacts=artifacts,
    )


def _render_chart_series(
    chart: ChartSeries,
    output_path: Path,
) -> ChartArtifact:
    file_name = f"{chart.chart_id}.png"
    file_path = output_path / file_name

    figure, axis = plt.subplots()
    axis.set_title(chart.title)
    axis.set_xlabel(chart.x_axis)
    axis.set_ylabel(chart.y_axis)

    if chart.data:
        labels = [point.label for point in chart.data]
        values = [point.value for point in chart.data]
        axis.bar(labels, values)
        figure.autofmt_xdate(rotation=30, ha="right")
    else:
        axis.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
        axis.set_xticks([])
        axis.set_yticks([])

    figure.tight_layout()
    figure.savefig(file_path, format="png")
    plt.close(figure)

    return ChartArtifact(
        chart_id=chart.chart_id,
        title=chart.title,
        chart_type=chart.chart_type,
        file_path=str(file_path),
        file_name=file_name,
    )

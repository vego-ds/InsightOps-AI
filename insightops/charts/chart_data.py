from collections import Counter

from pydantic import BaseModel, Field

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.metrics.kpis import SalesKPIResult


class ChartDataPoint(BaseModel):
    label: str
    value: float | int


class ChartSeries(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    metric: str
    x_axis: str
    y_axis: str
    data: list[ChartDataPoint] = Field(default_factory=list)


class SalesChartData(BaseModel):
    charts: list[ChartSeries] = Field(default_factory=list)


def build_sales_chart_data(
    kpis: SalesKPIResult,
    anomalies: AnomalyDetectionResult,
) -> SalesChartData:
    return SalesChartData(
        charts=[
            _build_revenue_chart(
                chart_id="revenue_by_region",
                title="Revenue by Region",
                metric="revenue",
                x_axis="region",
                grouped_revenue=kpis.revenue_by_region,
            ),
            _build_revenue_chart(
                chart_id="revenue_by_product",
                title="Revenue by Product",
                metric="revenue",
                x_axis="product",
                grouped_revenue=kpis.revenue_by_product,
            ),
            _build_revenue_chart(
                chart_id="revenue_by_sales_rep",
                title="Revenue by Sales Rep",
                metric="revenue",
                x_axis="sales_rep",
                grouped_revenue=kpis.revenue_by_sales_rep,
            ),
            _build_anomalies_by_severity_chart(anomalies),
        ]
    )


def _build_revenue_chart(
    *,
    chart_id: str,
    title: str,
    metric: str,
    x_axis: str,
    grouped_revenue: dict[str, float],
) -> ChartSeries:
    return ChartSeries(
        chart_id=chart_id,
        title=title,
        chart_type="bar",
        metric=metric,
        x_axis=x_axis,
        y_axis="revenue",
        data=[
            ChartDataPoint(label=label, value=value)
            for label, value in sorted(
                grouped_revenue.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    )


def _build_anomalies_by_severity_chart(
    anomalies: AnomalyDetectionResult,
) -> ChartSeries:
    severity_counts = Counter(
        anomaly.severity for anomaly in anomalies.anomalies
    )

    return ChartSeries(
        chart_id="anomalies_by_severity",
        title="Anomalies by Severity",
        chart_type="bar",
        metric="anomaly_count",
        x_axis="severity",
        y_axis="count",
        data=[
            ChartDataPoint(label=severity, value=count)
            for severity, count in sorted(severity_counts.items())
        ],
    )

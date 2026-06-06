from pydantic import BaseModel, Field

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.anomalies.interpretation import summarize_anomaly_methods
from insightops.governance.quality_gate import QualityGateResult
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import ManipulationSummary
from insightops.preparation.prepared_dataset import (
    PreparedSalesDataset,
    PreparedSalesRecord,
)
from insightops.profiling.data_profile import SalesDataProfile
from insightops.profiling.quality_score import DataQualityScore
from insightops.security.policy import SecurityScanResult
from insightops.trends.time_series import TimeSeriesTrendAnalysis
from insightops.validation.report import ValidationReport

InsightEvidenceValue = str | int | float | bool


class ExecutiveInsight(BaseModel):
    insight_id: str
    insight_type: str
    severity: str
    title: str
    message: str
    evidence: dict[str, InsightEvidenceValue] = Field(default_factory=dict)


class ExecutiveInsightReport(BaseModel):
    summary: str
    insights: list[ExecutiveInsight] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


def generate_executive_insights(
    validation_report: ValidationReport,
    kpis: SalesKPIResult,
    anomalies: AnomalyDetectionResult,
    security: SecurityScanResult,
    data_profile: SalesDataProfile | None = None,
    quality_score: DataQualityScore | None = None,
    quality_gate: QualityGateResult | None = None,
    preparation: PreparedSalesDataset | None = None,
    manipulation_summary: ManipulationSummary | None = None,
    trend_analysis: TimeSeriesTrendAnalysis | None = None,
) -> ExecutiveInsightReport:
    insights: list[ExecutiveInsight] = []
    recommended_actions: list[str] = []

    if validation_report.invalid_rows > 0:
        insights.append(
            ExecutiveInsight(
                insight_id="data_quality_001",
                insight_type="data_quality",
                severity="medium",
                title="Invalid sales rows detected",
                message=(
                    f"{validation_report.invalid_rows} invalid sales rows "
                    "were found."
                ),
                evidence={
                    "total_rows": validation_report.total_rows,
                    "valid_rows": validation_report.valid_rows,
                    "invalid_rows": validation_report.invalid_rows,
                },
            )
        )
        recommended_actions.append(
            "Review and correct invalid sales records before executive "
            "reporting."
        )

    if quality_gate and quality_gate.status == "blocked":
        insights.append(
            ExecutiveInsight(
                insight_id="governance_blocked_001",
                insight_type="governance",
                severity="high",
                title="Analysis governance gate blocked executive reporting",
                message=(
                    "The data quality gate determined that executive "
                    "reporting should not proceed without remediation."
                ),
                evidence={
                    "status": quality_gate.status,
                    "confidence_level": quality_gate.confidence_level,
                },
            )
        )
        recommended_actions.extend(quality_gate.required_actions)
    elif quality_gate and quality_gate.status == "warning":
        insights.append(
            ExecutiveInsight(
                insight_id="governance_warning_001",
                insight_type="governance",
                severity="medium",
                title="Analysis governance gate issued warnings",
                message=(
                    "The data quality gate allows analysis to proceed with "
                    "reduced confidence and required review actions."
                ),
                evidence={
                    "status": quality_gate.status,
                    "confidence_level": quality_gate.confidence_level,
                },
            )
        )
        recommended_actions.extend(quality_gate.required_actions)

    if quality_gate and quality_gate.confidence_level == "low":
        insights.append(
            ExecutiveInsight(
                insight_id="low_confidence_001",
                insight_type="analysis_confidence",
                severity="high",
                title="Executive reporting confidence is low",
                message=(
                    "The analysis confidence level is low, so executive "
                    "outputs require remediation before use."
                ),
                evidence={
                    "confidence_level": quality_gate.confidence_level,
                    "status": quality_gate.status,
                },
            )
        )

    if quality_score and quality_score.grade in {"poor", "fair"}:
        insights.append(
            ExecutiveInsight(
                insight_id="data_quality_risk_001",
                insight_type="data_quality_risk",
                severity="medium",
                title="Data quality risk may affect analysis",
                message=(
                    "The sales dataset quality score is below the preferred "
                    "range for executive reporting."
                ),
                evidence={
                    "quality_score": quality_score.score,
                    "quality_grade": quality_score.grade,
                },
            )
        )
        recommended_actions.append(
            "Improve data quality score before using outputs for strategic "
            "decisions."
        )

    if data_profile and data_profile.duplicate_order_ids > 0:
        insights.append(
            ExecutiveInsight(
                insight_id="data_integrity_001",
                insight_type="data_integrity",
                severity="medium",
                title="Duplicate order IDs detected",
                message=(
                    f"{data_profile.duplicate_order_ids} duplicate order IDs "
                    "were found in valid records."
                ),
                evidence={
                    "duplicate_order_ids": data_profile.duplicate_order_ids,
                },
            )
        )
        recommended_actions.append(
            "Deduplicate order IDs before forecasting or attribution analysis."
        )

    if data_profile:
        missing_field_total = sum(data_profile.missing_field_counts.values())
        if missing_field_total > 0:
            insights.append(
                ExecutiveInsight(
                    insight_id="data_completeness_001",
                    insight_type="data_completeness",
                    severity="medium",
                    title="Missing required field values detected",
                    message=(
                        f"{missing_field_total} missing required field values "
                        "were found in invalid rows."
                    ),
                    evidence={
                        "missing_field_total": missing_field_total,
                    },
                )
            )
            recommended_actions.append(
                "Fill missing required fields before advanced analytics."
            )

    if preparation:
        reconciliation_records = [
            record
            for record in preparation.records
            if round(abs(record.revenue_reconciliation_difference), 2) > 0
        ]
        if reconciliation_records:
            max_difference = max(
                abs(record.revenue_reconciliation_difference)
                for record in reconciliation_records
            )
            insights.append(
                ExecutiveInsight(
                    insight_id="reconciliation_001",
                    insight_type="data_reconciliation",
                    severity="medium",
                    title="Revenue reconciliation differences detected",
                    message=(
                        f"{len(reconciliation_records)} prepared sales "
                        "records have revenue reconciliation differences."
                    ),
                    evidence={
                        "affected_records": len(reconciliation_records),
                        "max_absolute_difference": round(max_difference, 2),
                    },
                )
            )
            recommended_actions.append(
                "Review revenue, discount, and unit price calculations before "
                "financial reporting."
            )

        high_value_records = [
            record for record in preparation.records if record.is_high_value_order
        ]
        concentration = _high_value_concentration(high_value_records)
        if concentration is not None:
            field_name, label, count = concentration
            insights.append(
                ExecutiveInsight(
                    insight_id="high_value_concentration_001",
                    insight_type="business_concentration",
                    severity="info",
                    title="High-value orders are concentrated",
                    message=(
                        f"High-value orders are concentrated in "
                        f"{field_name} '{label}'."
                    ),
                    evidence={
                        "field": field_name,
                        "label": label,
                        "high_value_order_count": count,
                    },
                )
            )

    if manipulation_summary:
        discount_concentration = _discount_concentration(
            manipulation_summary,
        )
        if discount_concentration is not None:
            product, discounted_order_count = discount_concentration
            insights.append(
                ExecutiveInsight(
                    insight_id="discount_concentration_001",
                    insight_type="discount_concentration",
                    severity="info",
                    title="Discounted orders are concentrated",
                    message=(
                        "Discounted orders are concentrated in product "
                        f"'{product}'."
                    ),
                    evidence={
                        "product": product,
                        "discounted_order_count": discounted_order_count,
                    },
                )
            )

    if security.human_review_required:
        insights.append(
            ExecutiveInsight(
                insight_id="security_001",
                insight_type="security",
                severity="high",
                title="Human review required",
                message=(
                    "Prompt injection or suspicious text was detected in "
                    "sales records."
                ),
                evidence={
                    "prompt_injection_detected": (
                        security.prompt_injection_detected
                    ),
                    "human_review_required": security.human_review_required,
                },
            )
        )
        recommended_actions.append(
            "Escalate flagged records for human security review."
        )

    if kpis.revenue_by_region:
        region, revenue = _top_group(kpis.revenue_by_region)
        insights.append(
            ExecutiveInsight(
                insight_id="revenue_001",
                insight_type="revenue",
                severity="info",
                title="Top revenue region identified",
                message=f"{region} is the top revenue region at {revenue}.",
                evidence={"region": region, "revenue": revenue},
            )
        )

    if kpis.revenue_by_product:
        product, revenue = _top_group(kpis.revenue_by_product)
        insights.append(
            ExecutiveInsight(
                insight_id="product_001",
                insight_type="product",
                severity="info",
                title="Top product identified",
                message=f"{product} is the top product at {revenue}.",
                evidence={"product": product, "revenue": revenue},
            )
        )

    if kpis.revenue_by_sales_rep:
        sales_rep, revenue = _top_group(kpis.revenue_by_sales_rep)
        insights.append(
            ExecutiveInsight(
                insight_id="sales_rep_001",
                insight_type="sales_rep",
                severity="info",
                title="Top sales rep identified",
                message=f"{sales_rep} is the top sales rep at {revenue}.",
                evidence={"sales_rep": sales_rep, "revenue": revenue},
            )
        )

    if anomalies.total_anomalies > 0:
        insights.append(
            ExecutiveInsight(
                insight_id="anomaly_001",
                insight_type="anomaly",
                severity="high",
                title="Sales anomalies detected",
                message=(
                    f"{anomalies.total_anomalies} sales anomalies were "
                    "detected."
                ),
                evidence={"total_anomalies": anomalies.total_anomalies},
            )
        )
        recommended_actions.append(
            "Investigate high-severity sales anomalies before final "
            "reporting."
        )

    if trend_analysis:
        if trend_analysis.revenue_trend.direction == "increasing":
            insights.append(
                ExecutiveInsight(
                    insight_id="trend_revenue_001",
                    insight_type="trend_revenue",
                    severity="info",
                    title="Revenue trend is improving",
                    message="Monthly revenue increased across the observed period range.",
                    evidence={
                        "percent_change": trend_analysis.revenue_trend.percent_change
                        or 0.0,
                        "direction": trend_analysis.revenue_trend.direction,
                    },
                )
            )
        elif trend_analysis.revenue_trend.direction == "decreasing":
            insights.append(
                ExecutiveInsight(
                    insight_id="trend_revenue_001",
                    insight_type="trend_revenue",
                    severity="high",
                    title="Revenue trend is declining",
                    message="Monthly revenue decreased across the observed period range.",
                    evidence={
                        "percent_change": trend_analysis.revenue_trend.percent_change
                        or 0.0,
                        "direction": trend_analysis.revenue_trend.direction,
                    },
                )
            )
            recommended_actions.append(
                "Review revenue drivers behind the declining monthly trend."
            )

        if trend_analysis.order_count_trend.direction == "decreasing":
            insights.append(
                ExecutiveInsight(
                    insight_id="trend_order_volume_001",
                    insight_type="trend_order_volume",
                    severity="medium",
                    title="Order volume trend is declining",
                    message="Monthly order count decreased across the observed period range.",
                    evidence={
                        "percent_change": trend_analysis.order_count_trend.percent_change
                        or 0.0,
                        "direction": trend_analysis.order_count_trend.direction,
                    },
                )
            )

        if (
            trend_analysis.average_discount_trend.direction == "increasing"
            and trend_analysis.average_discount_trend.percent_change is not None
            and trend_analysis.average_discount_trend.percent_change >= 10
        ):
            insights.append(
                ExecutiveInsight(
                    insight_id="trend_discount_001",
                    insight_type="trend_discount",
                    severity="medium",
                    title="Average discount trend is increasing",
                    message="Average discount increased materially across the observed period range.",
                    evidence={
                        "percent_change": (
                            trend_analysis.average_discount_trend.percent_change
                        ),
                        "direction": trend_analysis.average_discount_trend.direction,
                    },
                )
            )

        if trend_analysis.total_periods < 2:
            insights.append(
                ExecutiveInsight(
                    insight_id="trend_insufficient_data_001",
                    insight_type="trend_insufficient_data",
                    severity="low",
                    title="Trend analysis needs more monthly periods",
                    message="At least two monthly periods are needed for trend analysis.",
                    evidence={"total_periods": trend_analysis.total_periods},
                )
            )

    anomaly_method_summary = summarize_anomaly_methods(anomalies)
    total_statistical_anomalies = int(
        anomaly_method_summary["total_statistical_anomalies"]
    )
    if total_statistical_anomalies > 0:
        insights.append(
            ExecutiveInsight(
                insight_id="statistical_outliers_001",
                insight_type="statistical_outliers",
                severity="medium",
                title="Statistical sales outliers detected",
                message=(
                    f"{total_statistical_anomalies} sales anomalies were "
                    "detected using transparent statistical thresholds."
                ),
                evidence={
                    "total_statistical_anomalies": total_statistical_anomalies,
                },
            )
        )
        recommended_actions.append(
            "Review statistical outliers before using results for executive decisions."
        )

    product_relative_count = sum(
        1
        for anomaly in anomalies.anomalies
        if anomaly.anomaly_type == "product_relative_high_revenue"
    )
    if product_relative_count > 0:
        insights.append(
            ExecutiveInsight(
                insight_id="product_relative_outliers_001",
                insight_type="product_relative_outliers",
                severity="medium",
                title="Product-relative revenue irregularities detected",
                message=(
                    f"{product_relative_count} records exceeded product-level "
                    "revenue outlier thresholds."
                ),
                evidence={"product_relative_outlier_count": product_relative_count},
            )
        )

    recommended_actions.append(
        "Use KPI and chart outputs to support executive sales review."
    )

    if insights:
        summary = (
            f"{len(insights)} executive insights were generated from the "
            "sales analysis."
        )
    else:
        summary = (
            "The sales dataset passed validation, security, KPI, and anomaly "
            "checks without notable issues."
        )

    return ExecutiveInsightReport(
        summary=summary,
        insights=insights,
        recommended_actions=recommended_actions,
    )


def _top_group(grouped_revenue: dict[str, float]) -> tuple[str, float]:
    return sorted(
        grouped_revenue.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]


def _discount_concentration(
    manipulation_summary: ManipulationSummary,
) -> tuple[str, int] | None:
    discounted_total = sum(
        item.discounted_order_count
        for item in manipulation_summary.discount_summary_by_product
    )
    if discounted_total == 0:
        return None

    top_product = sorted(
        manipulation_summary.discount_summary_by_product,
        key=lambda item: (-item.discounted_order_count, item.product),
    )[0]
    if top_product.discounted_order_count / discounted_total >= 0.5:
        return top_product.product, top_product.discounted_order_count

    return None


def _high_value_concentration(
    records: list[PreparedSalesRecord],
) -> tuple[str, str, int] | None:
    if not records:
        return None

    for field_name in ("region", "product"):
        counts: dict[str, int] = {}
        for record in records:
            label = getattr(record, field_name)
            counts[label] = counts.get(label, 0) + 1

        label, count = sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0]
        if count / len(records) >= 0.5:
            return field_name, label, count

    return None

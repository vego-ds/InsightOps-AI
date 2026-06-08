from insightops.anomalies.detector import (
    AnomalyDetectionResult,
    SalesAnomaly,
)
from insightops.forecasting.baselines import (
    ForecastAnalysis,
    ForecastPoint,
    MetricForecast,
)
from insightops.governance.quality_gate import QualityGateResult
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.insights.generator import generate_executive_insights
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import build_manipulation_summary
from insightops.preparation.transformations import prepare_sales_records
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import compute_data_quality_score
from insightops.security.policy import SecurityScanResult
from insightops.trends.time_series import (
    MetricTrendSummary,
    TimeSeriesTrendAnalysis,
)
from insightops.validation.report import ValidationReport


def test_invalid_rows_produce_data_quality_insight() -> None:
    report = generate_executive_insights(
        _validation_report(invalid_rows=2),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "data_quality")

    assert insight.title == "Invalid sales rows detected"
    assert insight.insight_id == "data_quality_001"
    assert insight.evidence["invalid_rows"] == 2


def test_security_human_review_produces_security_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        SecurityScanResult(
            prompt_injection_detected=True,
            flagged_fields=["row_1.product"],
            human_review_required=True,
        ),
    )

    insight = _insight_by_type(report.insights, "security")

    assert insight.severity == "high"
    assert insight.insight_id == "security_001"
    assert insight.evidence["human_review_required"] is True


def test_fair_quality_score_produces_data_quality_risk_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        data_profile,
        quality_score,
    )

    insight = _insight_by_type(report.insights, "data_quality_risk")

    assert insight.insight_id == "data_quality_risk_001"
    assert insight.evidence["quality_score"] == 60
    assert insight.evidence["quality_grade"] == "fair"


def test_duplicate_order_ids_produce_data_integrity_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    validation_report.records[1].order_id = validation_report.records[0].order_id
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        data_profile,
        quality_score,
    )

    insight = _insight_by_type(report.insights, "data_integrity")

    assert insight.insight_id == "data_integrity_001"
    assert insight.evidence["duplicate_order_ids"] == 2


def test_missing_fields_produce_data_completeness_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        data_profile,
        quality_score,
    )

    insight = _insight_by_type(report.insights, "data_completeness")

    assert insight.insight_id == "data_completeness_001"
    assert insight.evidence["missing_field_total"] == 2


def test_reconciliation_difference_produces_reconciliation_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    preparation, _ = prepare_sales_records(validation_report.records)
    preparation.records[0].revenue_reconciliation_difference = 10.0

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        preparation=preparation,
    )

    insight = _insight_by_type(report.insights, "data_reconciliation")

    assert insight.insight_id == "reconciliation_001"
    assert insight.evidence["affected_records"] == 1
    assert insight.evidence["max_absolute_difference"] == 10.0


def test_discount_concentration_produces_discount_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    preparation, _ = prepare_sales_records(validation_report.records)
    manipulation_summary = build_manipulation_summary(preparation)
    # Mock to ensure concentration
    manipulation_summary.discount_summary_by_product[0].discounted_order_count = 100
    manipulation_summary.discount_summary_by_product[0].total_orders = 100
    for item in manipulation_summary.discount_summary_by_product[1:]:
        item.discounted_order_count = 0

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        manipulation_summary=manipulation_summary,
    )

    insight = _insight_by_type(report.insights, "discount_concentration")

    assert insight.insight_id == "discount_concentration_001"
    assert insight.evidence["discounted_order_count"] == 100


def test_high_value_concentration_produces_business_insight() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    preparation, _ = prepare_sales_records(validation_report.records)
    for r in preparation.records:
        r.is_high_value_order = False
    preparation.records[0].is_high_value_order = True

    report = generate_executive_insights(
        validation_report,
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        preparation=preparation,
    )

    insight = _insight_by_type(report.insights, "business_concentration")

    assert insight.insight_id == "high_value_concentration_001"
    assert insight.evidence["high_value_order_count"] == 1


def test_top_revenue_region_is_detected() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "revenue")

    assert insight.insight_id == "revenue_001"
    assert insight.evidence == {"region": "East", "revenue": 300.0}


def test_top_revenue_product_is_detected() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "product")

    assert insight.insight_id == "product_001"
    assert insight.evidence == {
        "product": "Analytics Pro",
        "revenue": 500.0,
    }


def test_top_sales_rep_is_detected() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "sales_rep")

    assert insight.insight_id == "sales_rep_001"
    assert insight.evidence == {"sales_rep": "Ava Singh", "revenue": 450.0}


def test_anomalies_produce_anomaly_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "anomaly")

    assert insight.title == "Sales anomalies detected"
    assert insight.insight_id == "anomaly_001"
    assert insight.evidence["total_anomalies"] == 1


def test_statistical_anomalies_produce_statistical_outlier_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        AnomalyDetectionResult(
            total_anomalies=1,
            anomalies=[
                SalesAnomaly(
                    anomaly_type="iqr_high_revenue",
                    severity="medium",
                    order_id="ORD-1",
                    field="revenue",
                    value=1000.0,
                    message="Revenue is above the IQR upper bound.",
                    method="iqr",
                    threshold=160.0,
                    comparison="value > upper_bound",
                )
            ],
        ),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "statistical_outliers")

    assert insight.insight_id == "statistical_outliers_001"
    assert insight.evidence["total_statistical_anomalies"] == 1


def test_product_relative_anomalies_produce_product_relative_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        AnomalyDetectionResult(
            total_anomalies=1,
            anomalies=[
                SalesAnomaly(
                    anomaly_type="product_relative_high_revenue",
                    severity="medium",
                    order_id="ORD-1",
                    field="revenue",
                    value=1000.0,
                    message="Revenue is above product-level threshold.",
                    method="segment_iqr",
                    threshold=160.0,
                    comparison="value > product_upper_bound",
                )
            ],
        ),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "product_relative_outliers")

    assert insight.insight_id == "product_relative_outliers_001"
    assert insight.evidence["product_relative_outlier_count"] == 1


def test_warning_quality_gate_produces_governance_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        quality_gate=_quality_gate(status="warning", confidence_level="medium"),
    )

    insight = _insight_by_type(report.insights, "governance")

    assert insight.insight_id == "governance_warning_001"
    assert insight.severity == "medium"


def test_blocked_quality_gate_produces_governance_and_low_confidence_insights() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        quality_gate=_quality_gate(status="blocked", confidence_level="low"),
    )

    governance = _insight_by_type(report.insights, "governance")
    confidence = _insight_by_type(report.insights, "analysis_confidence")

    assert governance.insight_id == "governance_blocked_001"
    assert governance.severity == "high"
    assert confidence.insight_id == "low_confidence_001"
    assert confidence.severity == "high"


def test_generated_insight_ids_are_unique() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    data_profile = build_sales_data_profile(validation_report)
    quality_score = compute_data_quality_score(data_profile)
    preparation, _ = prepare_sales_records(validation_report.records)
    manipulation_summary = build_manipulation_summary(preparation)

    report = generate_executive_insights(
        validation_report,
        _kpis(),
        _anomalies(),
        _safe_security(),
        data_profile,
        quality_score,
        preparation=preparation,
        manipulation_summary=manipulation_summary,
    )

    insight_ids = [insight.insight_id for insight in report.insights]

    assert len(insight_ids) == len(set(insight_ids))


def test_recommended_actions_include_data_quality_action() -> None:
    report = generate_executive_insights(
        _validation_report(invalid_rows=1),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    assert (
        "Review and correct invalid sales records before executive reporting."
        in report.recommended_actions
    )


def test_clean_inputs_return_safe_deterministic_summary() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    assert "contains $0.00 in valid revenue" in report.summary
    assert report.insights == []
    assert report.recommended_actions == [
        "Use KPI and chart outputs to support executive sales review."
    ]


def test_decreasing_revenue_trend_produces_trend_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        trend_analysis=_trend_analysis(revenue_direction="decreasing"),
    )

    insight = _insight_by_type(report.insights, "trend_revenue")

    assert insight.insight_id == "trend_revenue_001"
    assert insight.severity == "high"


def test_decreasing_order_count_trend_produces_volume_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        trend_analysis=_trend_analysis(order_direction="decreasing"),
    )

    insight = _insight_by_type(report.insights, "trend_order_volume")

    assert insight.insight_id == "trend_order_volume_001"
    assert insight.severity == "medium"


def test_material_discount_increase_produces_discount_trend_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        trend_analysis=_trend_analysis(discount_direction="increasing"),
    )

    insight = _insight_by_type(report.insights, "trend_discount")

    assert insight.insight_id == "trend_discount_001"
    assert insight.severity == "medium"


def test_insufficient_trend_data_produces_low_severity_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        trend_analysis=_trend_analysis(total_periods=1),
    )

    insight = _insight_by_type(report.insights, "trend_insufficient_data")

    assert insight.insight_id == "trend_insufficient_data_001"
    assert insight.severity == "low"


def test_forecast_readiness_insight_is_generated() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        forecast_analysis=_forecast_analysis(readiness_status="not_ready"),
    )

    insight = _insight_by_type(report.insights, "forecast_readiness")

    assert insight.insight_id == "forecast_readiness_001"
    assert insight.severity == "medium"


def test_revenue_forecast_insight_is_generated_when_ready() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        forecast_analysis=_forecast_analysis(readiness_status="ready"),
    )

    insight = _insight_by_type(report.insights, "forecast_revenue")

    assert insight.insight_id == "forecast_revenue_001"
    assert insight.evidence["selected_forecast_value"] == 120.0


def test_discount_forecast_pressure_generates_pricing_insight() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _empty_kpis(),
        _empty_anomalies(),
        _safe_security(),
        forecast_analysis=_forecast_analysis(
            readiness_status="ready",
            discount_selected=0.2,
            discount_latest=0.1,
        ),
    )

    insight = _insight_by_type(report.insights, "forecast_discount")

    assert insight.insight_id == "forecast_discount_001"
    assert insight.severity == "medium"


def _insight_by_type(insights: list, insight_type: str):
    return next(insight for insight in insights if insight.insight_type == insight_type)


def _validation_report(
    *,
    total_rows: int = 3,
    valid_rows: int = 3,
    invalid_rows: int = 0,
) -> ValidationReport:
    return ValidationReport(
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
    )


def _kpis() -> SalesKPIResult:
    return SalesKPIResult(
        total_revenue=1000.0,
        total_orders=3,
        total_units_sold=5,
        average_order_value=333.33,
        revenue_by_region={"West": 300.0, "East": 300.0},
        revenue_by_product={
            "Insights Basic": 200.0,
            "Analytics Pro": 500.0,
        },
        revenue_by_sales_rep={
            "Noah Chen": 450.0,
            "Ava Singh": 450.0,
        },
    )


def _empty_kpis() -> SalesKPIResult:
    return SalesKPIResult(
        total_revenue=0.0,
        total_orders=0,
        total_units_sold=0,
        average_order_value=0.0,
    )


def _anomalies() -> AnomalyDetectionResult:
    return AnomalyDetectionResult(
        total_anomalies=1,
        anomalies=[
            SalesAnomaly(
                anomaly_type="high_discount",
                severity="high",
                order_id="ORD-1",
                field="discount",
                value=0.5,
                message="Discount is unusually high.",
            )
        ],
    )


def _empty_anomalies() -> AnomalyDetectionResult:
    return AnomalyDetectionResult(total_anomalies=0, anomalies=[])


def _safe_security() -> SecurityScanResult:
    return SecurityScanResult(
        prompt_injection_detected=False,
        flagged_fields=[],
        human_review_required=False,
    )


def _trend_analysis(
    *,
    revenue_direction: str = "flat",
    order_direction: str = "flat",
    discount_direction: str = "flat",
    total_periods: int = 2,
) -> TimeSeriesTrendAnalysis:
    return TimeSeriesTrendAnalysis(
        period_grain="month",
        total_periods=total_periods,
        data=[],
        revenue_trend=_trend_summary("revenue", revenue_direction),
        order_count_trend=_trend_summary("order_count", order_direction),
        average_order_value_trend=_trend_summary(
            "average_order_value",
            "flat",
        ),
        units_sold_trend=_trend_summary("units_sold", "flat"),
        average_discount_trend=_trend_summary(
            "average_discount",
            discount_direction,
            percent_change=100.0 if discount_direction == "increasing" else 0.0,
        ),
        warnings=[],
    )


def _trend_summary(
    metric: str,
    direction: str,
    *,
    percent_change: float = 10.0,
) -> MetricTrendSummary:
    return MetricTrendSummary(
        metric=metric,
        start_value=100.0,
        end_value=90.0 if direction == "decreasing" else 110.0,
        absolute_change=-10.0 if direction == "decreasing" else 10.0,
        percent_change=percent_change,
        direction=direction,
        interpretation=f"{metric} is {direction}.",
    )


def _forecast_analysis(
    *,
    readiness_status: str,
    discount_selected: float = 0.1,
    discount_latest: float = 0.1,
) -> ForecastAnalysis:
    confidence = "medium" if readiness_status == "ready" else "low"
    return ForecastAnalysis(
        readiness_status=readiness_status,
        confidence_level=confidence,
        next_period="2026-04",
        revenue_forecast=_metric_forecast("revenue", 120.0, 100.0, confidence),
        order_count_forecast=_metric_forecast("order_count", 4.0, 3.0, confidence),
        average_order_value_forecast=_metric_forecast(
            "average_order_value",
            30.0,
            30.0,
            confidence,
        ),
        units_sold_forecast=_metric_forecast("units_sold", 12.0, 10.0, confidence),
        average_discount_forecast=_metric_forecast(
            "average_discount",
            discount_selected,
            discount_latest,
            confidence,
        ),
        warnings=["Forecasts are deterministic baselines."],
        recommended_actions=[],
    )


def _metric_forecast(
    metric: str,
    selected_value: float,
    latest_value: float,
    confidence: str,
) -> MetricForecast:
    latest = ForecastPoint(
        period="2026-04",
        metric=metric,
        forecast_value=latest_value,
        method="last_period",
        confidence=confidence,
        explanation="Uses latest observed value.",
    )
    selected = ForecastPoint(
        period="2026-04",
        metric=metric,
        forecast_value=selected_value,
        method="moving_average",
        confidence=confidence,
        explanation="Uses baseline moving average.",
    )
    return MetricForecast(
        metric=metric,
        next_period="2026-04",
        last_period_forecast=latest,
        moving_average_forecast=selected,
        trend_projection_forecast=selected,
        selected_baseline_method="moving_average",
        selected_forecast_value=selected_value,
        confidence=confidence,
        warnings=[],
    )


def _quality_gate(
    *,
    status: str,
    confidence_level: str,
) -> QualityGateResult:
    return QualityGateResult(
        status=status,
        confidence_level=confidence_level,
        can_generate_kpis=status != "blocked",
        can_generate_charts=status != "blocked",
        can_generate_reports=status != "blocked",
        can_generate_llm_narrative=False,
        human_review_required=status == "blocked",
        reasons=["Governance test reason."],
        required_actions=["Governance test action."],
    )

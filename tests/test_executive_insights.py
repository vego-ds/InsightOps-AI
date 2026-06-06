from insightops.anomalies.detector import (
    AnomalyDetectionResult,
    SalesAnomaly,
)
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.insights.generator import generate_executive_insights
from insightops.metrics.kpis import SalesKPIResult
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import compute_data_quality_score
from insightops.security.policy import SecurityScanResult
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

    assert insight.evidence["quality_score"] == 70
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

    assert insight.evidence["duplicate_order_ids"] == 1


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

    assert insight.evidence["missing_field_total"] == 2


def test_top_revenue_region_is_detected() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "revenue")

    assert insight.evidence == {"region": "East", "revenue": 300.0}


def test_top_revenue_product_is_detected() -> None:
    report = generate_executive_insights(
        _validation_report(),
        _kpis(),
        _empty_anomalies(),
        _safe_security(),
    )

    insight = _insight_by_type(report.insights, "product")

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
    assert insight.evidence["total_anomalies"] == 1


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

    assert report.summary == (
        "The sales dataset passed validation, security, KPI, and anomaly "
        "checks without notable issues."
    )
    assert report.insights == []
    assert report.recommended_actions == [
        "Use KPI and chart outputs to support executive sales review."
    ]


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

from insightops.governance.quality_gate import evaluate_quality_gate
from insightops.ingestion.csv_loader import load_sales_csv
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import DataQualityScore
from insightops.security.policy import SecurityScanResult
from insightops.validation.models import SalesRecord
from insightops.validation.report import ValidationReport


def test_quality_gate_pass_case_returns_high_confidence() -> None:
    result = evaluate_quality_gate(
        _clean_validation_report(),
        _clean_profile(),
        DataQualityScore(score=100, grade="excellent"),
        _safe_security(),
    )

    assert result.status == "pass"
    assert result.confidence_level == "high"
    assert result.can_generate_kpis is True
    assert result.can_generate_charts is True
    assert result.can_generate_reports is True
    assert result.can_generate_llm_narrative is True
    assert result.human_review_required is False


def test_invalid_rows_produce_warning() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    profile = build_sales_data_profile(validation_report)

    result = evaluate_quality_gate(
        validation_report,
        profile,
        DataQualityScore(score=80, grade="good"),
        _safe_security(),
    )

    assert result.status == "warning"
    assert result.confidence_level == "medium"
    assert any("invalid rows" in reason for reason in result.reasons)


def test_duplicate_order_ids_produce_warning() -> None:
    validation_report = _clean_validation_report(record_count=2)
    validation_report.records[1].order_id = validation_report.records[0].order_id
    profile = build_sales_data_profile(validation_report)

    result = evaluate_quality_gate(
        validation_report,
        profile,
        DataQualityScore(score=80, grade="good"),
        _safe_security(),
    )

    assert result.status == "warning"
    assert any("duplicate order IDs" in reason for reason in result.reasons)


def test_missing_fields_produce_warning() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    profile = build_sales_data_profile(validation_report)

    result = evaluate_quality_gate(
        validation_report,
        profile,
        DataQualityScore(score=80, grade="good"),
        _safe_security(),
    )

    assert result.status == "warning"
    assert any("missing required field" in reason for reason in result.reasons)


def test_quality_score_below_50_blocks_reporting() -> None:
    result = evaluate_quality_gate(
        _clean_validation_report(),
        _clean_profile(),
        DataQualityScore(score=40, grade="poor"),
        _safe_security(),
    )

    assert result.status == "blocked"
    assert result.confidence_level == "low"
    assert result.can_generate_reports is False
    assert result.can_generate_llm_narrative is False


def test_zero_valid_rows_blocks_analysis() -> None:
    validation_report = ValidationReport(
        total_rows=2,
        valid_rows=0,
        invalid_rows=2,
    )
    profile = build_sales_data_profile(validation_report)

    result = evaluate_quality_gate(
        validation_report,
        profile,
        DataQualityScore(score=80, grade="good"),
        _safe_security(),
    )

    assert result.status == "blocked"
    assert result.can_generate_kpis is False
    assert result.can_generate_charts is False
    assert result.human_review_required is True


def test_prompt_injection_blocks_llm_narrative() -> None:
    result = evaluate_quality_gate(
        _clean_validation_report(),
        _clean_profile(),
        DataQualityScore(score=100, grade="excellent"),
        SecurityScanResult(
            prompt_injection_detected=True,
            flagged_fields=["row_2.product"],
            human_review_required=False,
        ),
    )

    assert result.status == "pass"
    assert result.can_generate_llm_narrative is False
    assert result.human_review_required is True


def test_human_review_blocks_llm_narrative() -> None:
    result = evaluate_quality_gate(
        _clean_validation_report(),
        _clean_profile(),
        DataQualityScore(score=100, grade="excellent"),
        SecurityScanResult(
            prompt_injection_detected=False,
            flagged_fields=["row_2.product"],
            human_review_required=True,
        ),
    )

    assert result.can_generate_llm_narrative is False
    assert result.human_review_required is True


def test_blocked_overrides_warning() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    profile = build_sales_data_profile(validation_report)

    result = evaluate_quality_gate(
        validation_report,
        profile,
        DataQualityScore(score=40, grade="poor"),
        _safe_security(),
    )

    assert result.status == "blocked"
    assert result.confidence_level == "low"
    assert result.can_generate_reports is False


def _clean_profile():
    return build_sales_data_profile(_clean_validation_report())


def _clean_validation_report(record_count: int = 1) -> ValidationReport:
    records = [
        SalesRecord(
            order_id=f"ORD-{index}",
            order_date="2026-01-01",
            customer_id=f"CUST-{index}",
            region="North",
            product="Analytics Pro",
            sales_rep="Ava Singh",
            quantity=1,
            unit_price=100.0,
            discount=0.0,
            revenue=100.0,
        )
        for index in range(1, record_count + 1)
    ]
    return ValidationReport(
        total_rows=record_count,
        valid_rows=record_count,
        invalid_rows=0,
        records=records,
    )


def _safe_security() -> SecurityScanResult:
    return SecurityScanResult(
        prompt_injection_detected=False,
        flagged_fields=[],
        human_review_required=False,
    )

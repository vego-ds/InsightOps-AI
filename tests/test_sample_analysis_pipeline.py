from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_analysis_pipeline_returns_expected_sections() -> None:
    result = analyze_sample_sales_data()

    assert result.source_metadata
    assert result.validation
    assert result.data_profile
    assert result.quality_score
    assert result.quality_gate
    assert result.preparation
    assert result.transformation_log
    assert result.manipulation_summary
    assert result.trend_analysis
    assert result.forecast_analysis
    assert result.kpis
    assert result.security
    assert result.anomalies
    assert result.charts
    assert result.insights
    assert result.recommendation_plan
    assert result.workflow_improvement_plan
    assert result.audit_events

    assert result.validation.total_rows == 200
    assert result.validation.valid_rows == 198
    assert result.validation.invalid_rows == 2


def test_sample_analysis_pipeline_returns_data_profile_details() -> None:
    result = analyze_sample_sales_data()

    assert result.data_profile.total_rows == 200
    assert result.data_profile.valid_rows == 198
    assert result.data_profile.invalid_rows == 2
    assert result.data_profile.unique_customers == 85
    assert result.data_profile.unique_regions == 5
    assert result.data_profile.unique_products == 9
    assert result.data_profile.unique_sales_reps == 10
    assert result.data_profile.duplicate_order_ids == 1
    assert result.data_profile.missing_field_counts["order_id"] == 1
    assert result.data_profile.revenue_summary.maximum == 40500.0
    assert result.data_profile.quantity_summary.maximum == 15.0


def test_sample_analysis_pipeline_returns_preparation_details() -> None:
    result = analyze_sample_sales_data()

    assert result.source_metadata.source_type == "sample_csv"
    assert result.source_metadata.record_count == 200
    assert result.preparation.total_records == 198
    assert result.preparation.records[0].gross_revenue > 0.0
    assert len(result.transformation_log.entries) == 2
    assert result.manipulation_summary.monthly_revenue[0].label == "2026-01"
    assert result.manipulation_summary.ranked_products[0].label == "Analytics Pro"
    assert result.trend_analysis.period_grain == "month"
    assert result.trend_analysis.total_periods >= 1
    assert result.trend_analysis.revenue_trend.metric == "revenue"
    assert result.forecast_analysis.readiness_status in {
        "ready",
        "limited",
        "not_ready",
    }


def test_sample_analysis_pipeline_returns_quality_score_details() -> None:
    result = analyze_sample_sales_data()

    assert result.quality_score.score == 60
    assert result.quality_score.grade == "fair"
    assert result.quality_score.issues
    assert result.quality_score.recommendations


def test_sample_analysis_pipeline_returns_quality_gate_details() -> None:
    result = analyze_sample_sales_data()

    assert result.quality_gate.status == "warning"
    assert result.quality_gate.confidence_level == "medium"
    assert result.quality_gate.can_generate_kpis is True
    assert result.quality_gate.can_generate_charts is True
    assert result.quality_gate.can_generate_reports is True
    assert result.quality_gate.can_generate_llm_narrative is False
    assert any(
        event.event_type == "quality_gate_evaluated" for event in result.audit_events
    )


def test_sample_analysis_pipeline_returns_recommendations_and_workflows() -> None:
    result = analyze_sample_sales_data()

    assert result.recommendation_plan.total_recommendations >= 1
    assert result.workflow_improvement_plan.total_workflows == (
        result.recommendation_plan.total_recommendations
    )
    assert any(
        event.event_type == "recommendations_generated" for event in result.audit_events
    )
    assert any(
        event.event_type == "trend_analysis_completed" for event in result.audit_events
    )
    assert any(
        event.event_type == "forecast_analysis_completed"
        for event in result.audit_events
    )
    assert any(
        event.event_type == "workflow_improvements_generated"
        for event in result.audit_events
    )

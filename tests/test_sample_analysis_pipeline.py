from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_analysis_pipeline_returns_expected_sections() -> None:
    result = analyze_sample_sales_data()

    assert result.source_metadata
    assert result.validation
    assert result.data_profile
    assert result.quality_score
    assert result.preparation
    assert result.transformation_log
    assert result.manipulation_summary
    assert result.kpis
    assert result.security
    assert result.anomalies
    assert result.charts
    assert result.insights
    assert result.audit_events

    assert result.validation.total_rows == 5
    assert result.validation.valid_rows == 3
    assert result.validation.invalid_rows == 2


def test_sample_analysis_pipeline_returns_data_profile_details() -> None:
    result = analyze_sample_sales_data()

    assert result.data_profile.total_rows == 5
    assert result.data_profile.valid_rows == 3
    assert result.data_profile.invalid_rows == 2
    assert result.data_profile.unique_customers == 3
    assert result.data_profile.unique_regions == 3
    assert result.data_profile.unique_products == 3
    assert result.data_profile.unique_sales_reps == 3
    assert result.data_profile.duplicate_order_ids == 0
    assert result.data_profile.missing_field_counts["order_id"] == 1
    assert result.data_profile.revenue_summary.maximum == 2160.0
    assert result.data_profile.quantity_summary.maximum == 3.0


def test_sample_analysis_pipeline_returns_preparation_details() -> None:
    result = analyze_sample_sales_data()

    assert result.source_metadata.source_type == "sample_csv"
    assert result.source_metadata.record_count == 5
    assert result.preparation.total_records == 3
    assert result.preparation.records[0].gross_revenue == 2400.0
    assert len(result.transformation_log.entries) == 2
    assert result.manipulation_summary.monthly_revenue[0].label == "2026-01"
    assert result.manipulation_summary.ranked_products[0].label == (
        "Analytics Pro"
    )


def test_sample_analysis_pipeline_returns_quality_score_details() -> None:
    result = analyze_sample_sales_data()

    assert result.quality_score.score == 70
    assert result.quality_score.grade == "fair"
    assert result.quality_score.issues
    assert result.quality_score.recommendations

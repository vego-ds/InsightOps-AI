from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_analysis_pipeline_returns_expected_sections() -> None:
    result = analyze_sample_sales_data()

    assert result.validation
    assert result.data_profile
    assert result.quality_score
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


def test_sample_analysis_pipeline_returns_quality_score_details() -> None:
    result = analyze_sample_sales_data()

    assert result.quality_score.score == 70
    assert result.quality_score.grade == "fair"
    assert result.quality_score.issues
    assert result.quality_score.recommendations

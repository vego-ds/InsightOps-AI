from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_analysis_pipeline_returns_expected_sections() -> None:
    result = analyze_sample_sales_data()

    assert result.validation
    assert result.kpis
    assert result.security
    assert result.anomalies
    assert result.charts
    assert result.insights
    assert result.audit_events

    assert result.validation.total_rows == 5
    assert result.validation.valid_rows == 3
    assert result.validation.invalid_rows == 2

from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_analysis_pipeline_returns_expected_sections() -> None:
    result = analyze_sample_sales_data()

    assert "validation" in result
    assert "kpis" in result
    assert "security" in result
    assert "anomalies" in result
    assert "charts" in result
    assert "insights" in result
    assert "audit_events" in result

    validation = result["validation"]
    assert validation["total_rows"] == 5
    assert validation["valid_rows"] == 3
    assert validation["invalid_rows"] == 2

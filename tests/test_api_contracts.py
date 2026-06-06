from insightops.api.contracts import AnalysisResponse
from insightops.pipeline.sample_analysis import (
    analyze_sales_csv_file,
    analyze_sample_sales_data,
)


def test_analysis_response_can_be_created_from_sample_pipeline_result() -> None:
    pipeline_result = analyze_sample_sales_data()

    response = AnalysisResponse.model_validate(pipeline_result)

    assert response.source_metadata
    assert response.validation
    assert response.data_profile
    assert response.quality_score
    assert response.quality_gate
    assert response.preparation
    assert response.transformation_log
    assert response.manipulation_summary
    assert response.trend_analysis
    assert response.forecast_analysis
    assert response.kpis
    assert response.security
    assert response.anomalies
    assert response.charts
    assert response.insights
    assert response.recommendation_plan
    assert response.workflow_improvement_plan
    assert response.audit_events


def test_sample_pipeline_returns_analysis_response_instance() -> None:
    result = analyze_sample_sales_data()

    assert isinstance(result, AnalysisResponse)


def test_csv_file_pipeline_returns_analysis_response_instance() -> None:
    result = analyze_sales_csv_file("data/sample/sales_sample.csv")

    assert isinstance(result, AnalysisResponse)

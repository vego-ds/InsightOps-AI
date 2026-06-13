from insightops.answers import synthesize_final_answer
from insightops.planning import AnalysisIntent, AnalysisPlan


ARTIFACTS = [
    {"id": "chart", "kind": "chart", "title": "Chart"},
    {"id": "table", "kind": "table", "title": "Table"},
    {"id": "markdown", "kind": "markdown", "title": "Summary"},
]


def test_dataset_summary_final_answer_mentions_profile_summary_artifacts() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.dataset_summary),
        artifacts=ARTIFACTS,
        row_count=10,
        column_count=3,
    )

    assert "dataset summary/profile analysis" in answer
    assert "chart artifact, table artifact, and markdown summary artifact" in answer
    assert "Artifacts tab" in answer


def test_missing_values_final_answer_mentions_missing_values_table() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.missing_values),
        artifacts=[{"id": "missing", "kind": "table", "title": "Missing Values"}],
    )

    assert "missing-values analysis" in answer
    assert "table artifact" in answer


def test_grouped_metric_final_answer_mentions_x_and_y_columns() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.grouped_metric, x_column="region", y_column="revenue"),
        artifacts=ARTIFACTS,
    )

    assert "grouped metric analysis" in answer
    assert "revenue by region" in answer


def test_top_categories_final_answer_mentions_ranking() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.top_categories, x_column="product", y_column="revenue"),
        artifacts=ARTIFACTS,
    )

    assert "top categories ranking analysis" in answer


def test_trend_over_time_final_answer_mentions_time_trend() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.trend_over_time, x_column="order_date", y_column="revenue"),
        artifacts=ARTIFACTS,
    )

    assert "time trend analysis" in answer
    assert "revenue by order_date" in answer


def test_final_answer_is_plain_text_without_raw_html() -> None:
    answer = synthesize_final_answer(
        plan=_plan(AnalysisIntent.dataset_summary),
        artifacts=ARTIFACTS,
    )

    assert "<" not in answer
    assert ">" not in answer


def _plan(
    intent: AnalysisIntent,
    *,
    x_column: str | None = None,
    y_column: str | None = None,
) -> AnalysisPlan:
    return AnalysisPlan(
        intent=intent,
        title="Test Plan",
        requested_columns=[column for column in [x_column, y_column] if column],
        artifact_builders=[],
        x_column=x_column,
        y_column=y_column,
        explanation="test",
    )

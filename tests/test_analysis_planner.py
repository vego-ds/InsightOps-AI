from insightops.planning import AnalysisIntent, build_analysis_plan, resolve_column


SCHEMA = [
    {"key": "region", "label": "Region", "dataType": "string"},
    {"key": "product", "label": "Product", "dataType": "string"},
    {"key": "order_date", "label": "Order Date", "dataType": "date"},
    {"key": "revenue", "label": "Revenue", "dataType": "number"},
]


def test_planner_detects_dataset_summary() -> None:
    plan = build_analysis_plan("Give me an overview", SCHEMA)

    assert plan.intent == AnalysisIntent.dataset_summary


def test_planner_detects_missing_values() -> None:
    plan = build_analysis_plan("Show missing and null values", SCHEMA)

    assert plan.intent == AnalysisIntent.missing_values


def test_planner_detects_grouped_metric_for_revenue_by_region() -> None:
    plan = build_analysis_plan("revenue by region", SCHEMA)

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "revenue"


def test_planner_detects_top_categories_for_top_product() -> None:
    plan = build_analysis_plan("top product", SCHEMA)

    assert plan.intent == AnalysisIntent.top_categories
    assert plan.x_column == "product"


def test_planner_detects_trend_over_time() -> None:
    plan = build_analysis_plan("revenue over time", SCHEMA)

    assert plan.intent == AnalysisIntent.trend_over_time
    assert plan.x_column == "order_date"
    assert plan.y_column == "revenue"


def test_column_resolver_maps_sales_to_revenue_when_revenue_exists() -> None:
    assert resolve_column("sales", SCHEMA, preferred_type="number") == "revenue"

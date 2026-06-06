from insightops.ingestion.csv_loader import load_sales_csv
from insightops.profiling.data_profile import build_sales_data_profile
from insightops.profiling.quality_score import compute_data_quality_score


def test_quality_score_returns_score_and_grade() -> None:
    score = _sample_quality_score()

    assert score.score == 70
    assert score.grade == "fair"


def test_quality_score_reports_invalid_rows() -> None:
    score = _sample_quality_score()

    assert "2 invalid rows detected" in score.issues
    assert (
        "Review invalid rows before executive reporting"
        in score.recommendations
    )


def test_quality_score_reports_duplicate_order_ids() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    validation_report.records[1].order_id = validation_report.records[0].order_id
    profile = build_sales_data_profile(validation_report)

    score = compute_data_quality_score(profile)

    assert "1 duplicate order IDs detected" in score.issues
    assert "Deduplicate order IDs before forecasting" in score.recommendations


def test_quality_score_reports_missing_fields() -> None:
    score = _sample_quality_score()

    assert "2 missing field values detected" in score.issues
    assert "Fill missing fields before advanced analytics" in score.recommendations


def test_quality_score_for_clean_profile_is_excellent() -> None:
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    validation_report.total_rows = validation_report.valid_rows
    validation_report.invalid_rows = 0
    validation_report.errors = []
    profile = build_sales_data_profile(validation_report)

    score = compute_data_quality_score(profile)

    assert score.score == 100
    assert score.grade == "excellent"
    assert score.issues == []


def _sample_quality_score():
    validation_report = load_sales_csv("data/sample/sales_sample.csv")
    profile = build_sales_data_profile(validation_report)
    return compute_data_quality_score(profile)

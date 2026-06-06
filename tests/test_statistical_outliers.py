from insightops.statistics.outliers import (
    IQRBounds,
    calculate_iqr_bounds,
    detect_iqr_outliers,
)


def test_iqr_bounds_are_calculated() -> None:
    bounds = calculate_iqr_bounds([100.0, 110.0, 120.0, 130.0, 1000.0])

    assert isinstance(bounds, IQRBounds)
    assert bounds.q1 == 110.0
    assert bounds.q3 == 130.0
    assert bounds.iqr == 20.0
    assert bounds.lower_bound == 80.0
    assert bounds.upper_bound == 160.0


def test_iqr_outliers_are_detected_by_index() -> None:
    indexes = detect_iqr_outliers([100.0, 110.0, 120.0, 130.0, 1000.0])

    assert indexes == [4]


def test_insufficient_data_returns_safe_result() -> None:
    assert calculate_iqr_bounds([100.0, 110.0, 120.0]) is None
    assert detect_iqr_outliers([100.0, 110.0, 120.0]) == []

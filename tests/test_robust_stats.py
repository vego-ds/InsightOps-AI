from insightops.statistics.robust_stats import (
    iqr,
    mean,
    median,
    quartiles,
    standard_deviation,
)


def test_median_handles_odd_and_even_lists() -> None:
    assert median([3.0, 1.0, 2.0]) == 2.0
    assert median([4.0, 1.0, 2.0, 3.0]) == 2.5


def test_quartiles_and_iqr_work() -> None:
    values = [100.0, 110.0, 120.0, 130.0, 1000.0]

    assert quartiles(values) == (110.0, 130.0)
    assert iqr(values) == 20.0


def test_empty_lists_are_handled_safely() -> None:
    assert median([]) is None
    assert quartiles([]) is None
    assert iqr([]) is None
    assert mean([]) is None
    assert standard_deviation([]) is None


def test_standard_deviation_handles_one_value() -> None:
    assert standard_deviation([10.0]) == 0.0

from math import sqrt


def median(values: list[float]) -> float | None:
    if not values:
        return None

    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2

    if len(sorted_values) % 2 == 1:
        return round(sorted_values[midpoint], 2)

    return round(
        (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2,
        2,
    )


def quartiles(values: list[float]) -> tuple[float, float] | None:
    if len(values) < 4:
        return None

    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2

    if len(sorted_values) % 2 == 0:
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[midpoint:]
    else:
        lower_half = sorted_values[: midpoint + 1]
        upper_half = sorted_values[midpoint:]

    q1 = median(lower_half)
    q3 = median(upper_half)
    if q1 is None or q3 is None:
        return None

    return q1, q3


def iqr(values: list[float]) -> float | None:
    quartile_values = quartiles(values)
    if quartile_values is None:
        return None

    q1, q3 = quartile_values
    return round(q3 - q1, 2)


def mean(values: list[float]) -> float | None:
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def standard_deviation(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0

    average = mean(values)
    if average is None:
        return None

    variance = sum((value - average) ** 2 for value in values) / (
        len(values) - 1
    )
    return round(sqrt(variance), 2)

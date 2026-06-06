from pydantic import BaseModel

from insightops.statistics.robust_stats import iqr, quartiles


class IQRBounds(BaseModel):
    q1: float
    q3: float
    iqr: float
    lower_bound: float
    upper_bound: float


def calculate_iqr_bounds(values: list[float]) -> IQRBounds | None:
    quartile_values = quartiles(values)
    iqr_value = iqr(values)
    if quartile_values is None or iqr_value is None:
        return None

    q1, q3 = quartile_values
    lower_bound = round(q1 - (1.5 * iqr_value), 2)
    upper_bound = round(q3 + (1.5 * iqr_value), 2)

    return IQRBounds(
        q1=q1,
        q3=q3,
        iqr=iqr_value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )


def detect_iqr_outliers(values: list[float]) -> list[int]:
    bounds = calculate_iqr_bounds(values)
    if bounds is None:
        return []

    return [
        index
        for index, value in enumerate(values)
        if value < bounds.lower_bound or value > bounds.upper_bound
    ]

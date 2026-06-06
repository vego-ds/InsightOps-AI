from pydantic import BaseModel, Field

from insightops.profiling.data_profile import SalesDataProfile


class DataQualityScore(BaseModel):
    score: int
    grade: str
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


def compute_data_quality_score(profile: SalesDataProfile) -> DataQualityScore:
    issues: list[str] = []
    recommendations: list[str] = []
    score = 100

    if profile.invalid_rows > 0:
        score -= min(40, profile.invalid_rows * 10)
        issues.append(f"{profile.invalid_rows} invalid rows detected")
        recommendations.append(
            "Review invalid rows before executive reporting"
        )

    if profile.duplicate_order_ids > 0:
        score -= min(20, profile.duplicate_order_ids * 10)
        issues.append(
            f"{profile.duplicate_order_ids} duplicate order IDs detected"
        )
        recommendations.append("Deduplicate order IDs before forecasting")

    missing_field_total = sum(profile.missing_field_counts.values())
    if missing_field_total > 0:
        score -= min(20, missing_field_total * 5)
        issues.append(f"{missing_field_total} missing field values detected")
        recommendations.append("Fill missing fields before advanced analytics")

    score = max(score, 0)

    return DataQualityScore(
        score=score,
        grade=_grade_for_score(score),
        issues=issues,
        recommendations=recommendations,
    )


def _grade_for_score(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 60:
        return "fair"
    return "poor"

from collections import Counter

from insightops.anomalies.detector import AnomalyDetectionResult


def summarize_anomaly_methods(
    anomalies: AnomalyDetectionResult,
) -> dict[str, int | dict[str, int]]:
    statistical_anomalies = [
        anomaly for anomaly in anomalies.anomalies if anomaly.method is not None
    ]
    rule_based_anomalies = [
        anomaly for anomaly in anomalies.anomalies if anomaly.method is None
    ]
    field_counts = Counter(anomaly.field for anomaly in anomalies.anomalies)

    return {
        "total_statistical_anomalies": len(statistical_anomalies),
        "total_rule_based_anomalies": len(rule_based_anomalies),
        "high_severity_count": sum(
            1 for anomaly in anomalies.anomalies if anomaly.severity == "high"
        ),
        "fields_most_often_flagged": dict(sorted(field_counts.items())),
    }

from pydantic import BaseModel

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.audit.events import AuditEvent
from insightops.charts.chart_data import SalesChartData
from insightops.insights.generator import ExecutiveInsightReport
from insightops.metrics.kpis import SalesKPIResult
from insightops.profiling.data_profile import SalesDataProfile
from insightops.profiling.quality_score import DataQualityScore
from insightops.security.policy import SecurityScanResult
from insightops.validation.report import ValidationReport


class AnalysisResponse(BaseModel):
    validation: ValidationReport
    data_profile: SalesDataProfile
    quality_score: DataQualityScore
    kpis: SalesKPIResult
    security: SecurityScanResult
    anomalies: AnomalyDetectionResult
    charts: SalesChartData
    insights: ExecutiveInsightReport
    audit_events: list[AuditEvent]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str

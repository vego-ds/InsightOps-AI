from pydantic import BaseModel

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.audit.events import AuditEvent
from insightops.charts.chart_data import SalesChartData
from insightops.insights.generator import ExecutiveInsightReport
from insightops.metrics.kpis import SalesKPIResult
from insightops.security.policy import SecurityScanResult
from insightops.validation.report import ValidationReport


class AnalysisResponse(BaseModel):
    validation: ValidationReport
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

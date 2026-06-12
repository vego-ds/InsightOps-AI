from pydantic import BaseModel, Field

from insightops.anomalies.detector import AnomalyDetectionResult
from insightops.audit.events import AuditEvent
from insightops.charts.chart_data import SalesChartData
from insightops.forecasting.baselines import ForecastAnalysis
from insightops.governance.quality_gate import QualityGateResult
from insightops.insights.generator import ExecutiveInsightReport
from insightops.lineage.transformation_log import TransformationLog
from insightops.metrics.kpis import SalesKPIResult
from insightops.preparation.manipulations import ManipulationSummary
from insightops.preparation.prepared_dataset import PreparedSalesDataset
from insightops.profiling.data_profile import SalesDataProfile
from insightops.profiling.quality_score import DataQualityScore
from insightops.recommendations.action_plan import RecommendationPlan
from insightops.recommendations.workflow_improvements import WorkflowImprovementPlan
from insightops.security.policy import SecurityScanResult
from insightops.sources.source_metadata import DatasetSourceMetadata
from insightops.trends.time_series import TimeSeriesTrendAnalysis
from insightops.validation.report import ValidationReport


class AnalysisResponse(BaseModel):
    source_metadata: DatasetSourceMetadata
    validation: ValidationReport
    data_profile: SalesDataProfile
    quality_score: DataQualityScore
    quality_gate: QualityGateResult
    preparation: PreparedSalesDataset
    transformation_log: TransformationLog
    manipulation_summary: ManipulationSummary
    trend_analysis: TimeSeriesTrendAnalysis
    forecast_analysis: ForecastAnalysis
    kpis: SalesKPIResult
    security: SecurityScanResult
    anomalies: AnomalyDetectionResult
    charts: SalesChartData
    insights: ExecutiveInsightReport
    recommendation_plan: RecommendationPlan
    workflow_improvement_plan: WorkflowImprovementPlan
    audit_events: list[AuditEvent]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str


class CsvUploadPreviewResponse(BaseModel):
    filename: str
    size_bytes: int
    detected_schema: str
    original_headers: list[str]
    normalized_headers: list[str]
    is_canonical: bool
    is_mappable: bool
    mapped_columns: dict[str, str]
    missing_required_columns: list[str]
    warnings: list[str]
    compatible: bool
    detected_encoding: str


class DatasetPreviewColumn(BaseModel):
    key: str
    label: str
    dataType: str
    nullable: bool
    sampleValues: list[object | None]


class DatasetPreview(BaseModel):
    id: str
    fileName: str
    mimeType: str
    sizeBytes: int
    rowCount: int
    previewRowCount: int
    columnCount: int
    columns: list[DatasetPreviewColumn]
    previewRows: list[dict[str, object | None]]


class DatasetUploadErrorDetail(BaseModel):
    code: str
    message: str
    recoverable: bool


class DatasetUploadSuccessResponse(BaseModel):
    version: str
    status: str
    dataset: DatasetPreview
    warnings: list[str]


class DatasetUploadErrorResponse(BaseModel):
    version: str
    status: str
    error: DatasetUploadErrorDetail


class AnalysisRequestColumn(BaseModel):
    key: str
    label: str
    dataType: str
    nullable: bool


class AnalysisRequest(BaseModel):
    version: str
    datasetId: str
    message: str
    schema_: list[AnalysisRequestColumn] = Field(alias="schema")
    previewRows: list[dict[str, object | None]]


class AnalysisRequestResponse(BaseModel):
    version: str
    status: str
    runId: str
    assistantMessage: str

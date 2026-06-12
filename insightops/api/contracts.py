from typing import Literal

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


class AnalysisRunCreateRequest(BaseModel):
    version: str
    datasetId: str
    message: str
    schema_: list[AnalysisRequestColumn] = Field(alias="schema")
    previewRows: list[dict[str, object | None]]


class AnalysisRunCreatedResponse(BaseModel):
    version: str
    status: str
    runId: str
    streamUrl: str


class RunEventBase(BaseModel):
    version: str
    runId: str
    sequence: int
    type: str


class RunStatusEvent(RunEventBase):
    status: str


class RunCodeEvent(RunEventBase):
    language: str
    code: str


class RunStdoutEvent(RunEventBase):
    stdout: str


class RunErrorEvent(RunEventBase):
    errorMessage: str


class RunCellStartedEvent(RunEventBase):
    cellId: str
    title: str
    language: str
    code: str
    attempt: int


class RunCellStdoutEvent(RunEventBase):
    cellId: str
    stdout: str


class RunCellStderrEvent(RunEventBase):
    cellId: str
    stderr: str


class RunCellCompletedEvent(RunEventBase):
    cellId: str
    durationMs: int


class RunCellFailedEvent(RunEventBase):
    cellId: str
    errorMessage: str
    traceback: str
    durationMs: int


class RunRepairStartedEvent(RunEventBase):
    failedCellId: str
    repairCellId: str
    reason: str


class RunRepairCompletedEvent(RunEventBase):
    failedCellId: str
    repairCellId: str
    outcome: str


ArtifactKind = Literal["table", "chart", "markdown"]


class TableArtifact(BaseModel):
    id: str
    kind: Literal["table"]
    title: str
    columns: list[str]
    rows: list[dict[str, object | None]]


class ChartArtifact(BaseModel):
    id: str
    kind: Literal["chart"]
    title: str
    chartType: Literal["bar", "line"]
    xKey: str
    yKey: str
    data: list[dict[str, str | int | float]]


class MarkdownArtifact(BaseModel):
    id: str
    kind: Literal["markdown"]
    title: str
    text: str


class RunArtifactEvent(RunEventBase):
    artifact: TableArtifact | ChartArtifact | MarkdownArtifact


class RunFinalEvent(RunEventBase):
    assistantMessage: str

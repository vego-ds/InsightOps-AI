import type {
  DatasetColumnType,
  FilePreviewDataset,
  PreviewRow,
} from "@/types/dataset";
import type { InsightArtifact } from "@/types/artifact";
import type { NotebookRunEvent } from "@/types/notebook";

export type AnalysisRunCreateColumn = {
  key: string;
  label: string;
  dataType: DatasetColumnType;
  nullable: boolean;
};

export type AnalysisRunCreateRequest = {
  version: "insightops.analysis-run-create.v1";
  datasetId: string;
  message: string;
  schema: AnalysisRunCreateColumn[];
  previewRows: PreviewRow[];
};

export type AnalysisRunCreatedResponse = {
  version: "insightops.analysis-run-created.v1";
  status: "created";
  runId: string;
  streamUrl: string;
};

export type RunEventBase = {
  version: "insightops.run-event.v1";
  runId: string;
  sequence: number;
};

export type RunStatusEvent = RunEventBase & {
  type: "run.status";
  status: "agent_planning" | "rendering_view" | string;
};

export type RunCodeEvent = RunEventBase & {
  type: "run.code";
  language: "python" | string;
  code: string;
};

export type RunStdoutEvent = RunEventBase & {
  type: "run.stdout";
  stdout: string;
};

export type RunErrorEvent = RunEventBase & {
  type: "run.error";
  errorMessage: string;
};

export type RunFinalEvent = RunEventBase & {
  type: "run.final";
  assistantMessage: string;
};

export type RunArtifactEvent = RunEventBase & {
  type: "artifact";
  artifact: InsightArtifact;
};

export type AnalysisRunEvent =
  | RunStatusEvent
  | RunCodeEvent
  | RunStdoutEvent
  | RunErrorEvent
  | RunArtifactEvent
  | NotebookRunEvent
  | RunFinalEvent;

export function buildAnalysisRunCreateRequest(
  dataset: FilePreviewDataset,
  message: string,
): AnalysisRunCreateRequest {
  return {
    version: "insightops.analysis-run-create.v1",
    datasetId: dataset.id,
    message,
    schema: dataset.columns.map((column) => ({
      key: column.key,
      label: column.label,
      dataType: column.dataType,
      nullable: column.nullable,
    })),
    previewRows: dataset.previewRows,
  };
}

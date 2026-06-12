import type {
  DatasetColumnType,
  FilePreviewDataset,
  PreviewRow,
} from "@/types/dataset";

export type AnalysisRequestColumn = {
  key: string;
  label: string;
  dataType: DatasetColumnType;
  nullable: boolean;
};

export type AnalysisRequestBody = {
  version: "insightops.analysis-request.v1";
  datasetId: string;
  message: string;
  schema: AnalysisRequestColumn[];
  previewRows: PreviewRow[];
};

export type AnalysisResponseBody = {
  version: "insightops.analysis-response.v1";
  status: "accepted";
  runId: string;
  assistantMessage: string;
};

export function buildAnalysisRequestBody(
  dataset: FilePreviewDataset,
  message: string,
): AnalysisRequestBody {
  return {
    version: "insightops.analysis-request.v1",
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

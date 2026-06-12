export type DatasetColumnType =
  | "string"
  | "number"
  | "integer"
  | "boolean"
  | "date"
  | "datetime"
  | "categorical"
  | "unknown";

export type PreviewCellValue = string | number | boolean | null;

export type DatasetColumn = {
  key: string;
  label: string;
  dataType: DatasetColumnType;
  nullable: boolean;
  sampleValues: PreviewCellValue[];
};

export type PreviewRow = Record<string, PreviewCellValue>;

export type FilePreviewDataset = {
  id: string;
  fileName: string;
  mimeType: string;
  sizeBytes: number;
  rowCount: number;
  previewRowCount: number;
  columnCount: number;
  columns: DatasetColumn[];
  previewRows: PreviewRow[];
};

export type FilePreviewSuccessResponse = {
  version: "insightops.file-preview.v1";
  status: "ok";
  dataset: FilePreviewDataset;
  warnings: string[];
};

export type FilePreviewErrorResponse = {
  version: "insightops.file-preview.v1";
  status: "error";
  error: {
    code: string;
    message: string;
    recoverable: boolean;
  };
};

export type FilePreviewResponse =
  | FilePreviewSuccessResponse
  | FilePreviewErrorResponse;

export type DatasetUploadStatus =
  | "idle"
  | "dragging"
  | "uploading"
  | "parsing_schema"
  | "success"
  | "runtime_error";

"use client";

import * as React from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
  UploadCloud,
  X,
} from "lucide-react";

import { useDatasetStore } from "@/stores/dataset-store";
import type {
  DatasetColumn,
  DatasetColumnType,
  FilePreviewDataset,
  FilePreviewErrorResponse,
  FilePreviewResponse,
  FilePreviewSuccessResponse,
  PreviewCellValue,
  PreviewRow,
} from "@/types/dataset";

const FILE_PREVIEW_VERSION = "insightops.file-preview.v1";
const DEFAULT_ACCEPTED_EXTENSIONS = [".csv"];
const NUMBER_FORMATTER = new Intl.NumberFormat("en");

type UploadState =
  | { status: "idle" }
  | { status: "dragging" }
  | { status: "parsing_schema"; fileName: string }
  | { status: "success"; response: FilePreviewSuccessResponse }
  | { status: "runtime_error"; message: string };

type FileUploadPreviewGridProps = {
  uploadUrl?: string;
  maxFileSizeMb?: number;
  acceptedExtensions?: readonly string[];
  className?: string;
};

export function FileUploadPreviewGrid({
  uploadUrl = "/api/datasets/upload",
  maxFileSizeMb = 50,
  acceptedExtensions = DEFAULT_ACCEPTED_EXTENSIONS,
  className = "",
}: FileUploadPreviewGridProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const [state, setState] = React.useState<UploadState>({ status: "idle" });

  const clearActiveDataset = useDatasetStore((store) => store.clearActiveDataset);
  const setActiveDataset = useDatasetStore((store) => store.setActiveDataset);
  const setErrorMessage = useDatasetStore((store) => store.setErrorMessage);
  const setUploadStatus = useDatasetStore((store) => store.setUploadStatus);

  const acceptedLabel = acceptedExtensions.join(", ");
  const maxFileSizeBytes = maxFileSizeMb * 1024 * 1024;
  const uploadLocked = state.status === "parsing_schema";
  const showUploadZone = state.status !== "success";

  const failUpload = React.useCallback(
    (message: string) => {
      setState({ status: "runtime_error", message });
      setErrorMessage(message);
    },
    [setErrorMessage],
  );

  const reset = React.useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    if (inputRef.current) {
      inputRef.current.value = "";
    }

    clearActiveDataset();
    setErrorMessage(null);
    setUploadStatus("idle");
    setState({ status: "idle" });
  }, [clearActiveDataset, setErrorMessage, setUploadStatus]);

  const uploadFile = React.useCallback(
    async (file: File) => {
      if (!hasAcceptedExtension(file.name, acceptedExtensions)) {
        failUpload(`Unsupported file type. Accepted files: ${acceptedLabel}.`);
        return;
      }

      if (file.size > maxFileSizeBytes) {
        failUpload(`File exceeds the ${maxFileSizeMb} MB upload limit.`);
        return;
      }

      abortControllerRef.current?.abort();
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState({ status: "parsing_schema", fileName: file.name });
      setUploadStatus("parsing_schema");
      setErrorMessage(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(uploadUrl, {
          method: "POST",
          body: formData,
          signal: abortController.signal,
        });
        const payload = parseFilePreviewResponse(await response.json());

        if (!payload) {
          failUpload(
            "The upload service returned an invalid dataset preview response.",
          );
          return;
        }

        if (payload.status === "error") {
          failUpload(payload.error.message);
          return;
        }

        if (!response.ok) {
          failUpload("The dataset preview could not be created.");
          return;
        }

        setActiveDataset(payload.dataset);
        setState({ status: "success", response: payload });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        failUpload(getUploadErrorMessage(error));
      }
    },
    [
      acceptedExtensions,
      acceptedLabel,
      failUpload,
      maxFileSizeBytes,
      maxFileSizeMb,
      setActiveDataset,
      setErrorMessage,
      setUploadStatus,
      uploadUrl,
    ],
  );

  const handleInputChange = React.useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];

      if (file) {
        void uploadFile(file);
      }
    },
    [uploadFile],
  );

  const handleDrop = React.useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();

      if (uploadLocked) {
        return;
      }

      const file = event.dataTransfer.files?.[0];

      if (file) {
        void uploadFile(file);
        return;
      }

      setState({ status: "idle" });
      setUploadStatus("idle");
    },
    [setUploadStatus, uploadFile, uploadLocked],
  );

  const handleDragOver = React.useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();

      if (!uploadLocked) {
        setState({ status: "dragging" });
        setUploadStatus("dragging");
      }
    },
    [setUploadStatus, uploadLocked],
  );

  const handleDragLeave = React.useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();

      if (!uploadLocked) {
        setState({ status: "idle" });
        setUploadStatus("idle");
      }
    },
    [setUploadStatus, uploadLocked],
  );

  return (
    <section
      className={[
        "w-full rounded-3xl border border-white/10 bg-[#080A12] p-4 text-slate-100 shadow-2xl shadow-black/40 ring-1 ring-white/5",
        className,
      ].join(" ")}
    >
      <div className="rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.07] to-white/[0.02] p-5">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-200">
              <FileSpreadsheet className="h-3.5 w-3.5" />
              Dataset ingest
            </div>

            <h2 className="mt-4 text-2xl font-semibold tracking-tight text-white">
              Upload your data file
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Drop a CSV file to create a typed dataset preview before analysis
              begins.
            </p>
          </div>

          {state.status === "success" ? (
            <button
              type="button"
              onClick={reset}
              className="inline-flex h-9 items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 text-sm text-slate-300 transition hover:bg-white/10 hover:text-white"
            >
              <X className="h-4 w-4" />
              Replace
            </button>
          ) : null}
        </div>

        {showUploadZone ? (
          <UploadDropZone
            acceptedExtensions={acceptedExtensions}
            inputRef={inputRef}
            maxFileSizeMb={maxFileSizeMb}
            state={state}
            uploadLocked={uploadLocked}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onInputChange={handleInputChange}
          />
        ) : (
          <DatasetPreviewTable dataset={state.response.dataset} />
        )}
      </div>
    </section>
  );
}

type UploadDropZoneProps = {
  acceptedExtensions: readonly string[];
  inputRef: React.RefObject<HTMLInputElement | null>;
  maxFileSizeMb: number;
  state: Exclude<UploadState, { status: "success" }>;
  uploadLocked: boolean;
  onDragLeave: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  onInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
};

function UploadDropZone({
  acceptedExtensions,
  inputRef,
  maxFileSizeMb,
  state,
  uploadLocked,
  onDragLeave,
  onDragOver,
  onDrop,
  onInputChange,
}: UploadDropZoneProps) {
  const isDragging = state.status === "dragging";
  const isParsing = state.status === "parsing_schema";

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={uploadLocked}
      aria-label="Upload CSV dataset"
      onClick={() => {
        if (!uploadLocked) {
          inputRef.current?.click();
        }
      }}
      onKeyDown={(event) => {
        if (!uploadLocked && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={[
        "group relative overflow-hidden rounded-2xl border border-dashed p-8 outline-none transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-cyan-200",
        isDragging
          ? "border-cyan-300/70 bg-cyan-400/[0.08] shadow-2xl shadow-cyan-950/40"
          : "border-white/15 bg-black/20 hover:border-cyan-300/50 hover:bg-cyan-400/[0.04]",
        isParsing ? "cursor-wait" : "cursor-pointer",
      ].join(" ")}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_34rem)]" />

      <input
        ref={inputRef}
        type="file"
        accept={acceptedExtensions.join(",")}
        className="hidden"
        disabled={uploadLocked}
        onChange={onInputChange}
      />

      <div className="relative flex flex-col items-center justify-center text-center">
        <div
          className={[
            "mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border transition",
            isDragging
              ? "border-cyan-300/40 bg-cyan-300/15"
              : "border-white/10 bg-white/[0.06] group-hover:border-cyan-300/30 group-hover:bg-cyan-300/10",
          ].join(" ")}
        >
          {isParsing ? (
            <Loader2 className="h-7 w-7 animate-spin text-cyan-200" />
          ) : (
            <UploadCloud className="h-7 w-7 text-cyan-200" />
          )}
        </div>

        <div className="text-base font-medium text-white">
          {getDropZoneTitle(state.status)}
        </div>

        <p className="mt-2 text-sm text-slate-400">
          {state.status === "parsing_schema"
            ? state.fileName
            : `or click to browse. Max file size ${maxFileSizeMb} MB.`}
        </p>

        {state.status === "runtime_error" ? (
          <UploadErrorMessage message={state.message} />
        ) : null}
      </div>
    </div>
  );
}

function UploadErrorMessage({ message }: { message: string }) {
  return (
    <div className="mt-5 flex max-w-xl items-start gap-3 rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-left">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-300" />
      <div>
        <p className="text-sm font-medium text-red-100">Upload failed</p>
        <p className="mt-1 text-sm leading-5 text-red-200/80">{message}</p>
      </div>
    </div>
  );
}

export function DatasetPreviewTable({ dataset }: { dataset: FilePreviewDataset }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
      <div className="flex flex-col gap-3 border-b border-white/10 bg-white/[0.03] px-4 py-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-300" />
            <p className="truncate text-sm font-medium text-white">
              {dataset.fileName}
            </p>
          </div>

          <p className="mt-1 text-xs text-slate-400">
            {formatNumber(dataset.rowCount)} rows ·{" "}
            {formatNumber(dataset.columnCount)} columns ·{" "}
            {formatFileSize(dataset.sizeBytes)}
          </p>
        </div>

        <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">
          Preview ready
        </div>
      </div>

      <div className="max-h-[520px] overflow-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="sticky top-0 z-10 bg-[#10131F]">
            <tr>
              <th className="sticky left-0 z-20 border-b border-r border-white/10 bg-[#10131F] px-4 py-3 text-xs font-medium uppercase text-slate-400">
                #
              </th>

              {dataset.columns.map((column) => (
                <th
                  key={column.key}
                  className="whitespace-nowrap border-b border-white/10 px-4 py-3 align-bottom"
                >
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase text-slate-200">
                      {column.label}
                    </span>
                    <span className="inline-flex w-fit rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[11px] font-medium text-slate-400">
                      {column.dataType}
                      {column.nullable ? " · nullable" : ""}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {dataset.previewRows.map((row, rowIndex) => (
              <tr
                key={`row-${rowIndex}`}
                className="transition hover:bg-white/[0.04]"
              >
                <td className="sticky left-0 z-10 border-b border-r border-white/10 bg-[#0B0E18] px-4 py-3 text-xs text-slate-500">
                  {rowIndex + 1}
                </td>

                {dataset.columns.map((column) => {
                  const value = row[column.key] ?? null;

                  return (
                    <td
                      key={`${rowIndex}-${column.key}`}
                      className="max-w-[280px] truncate border-b border-white/10 px-4 py-3 text-slate-300"
                      title={formatCellTitle(value)}
                    >
                      <CellValue value={value} />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-white/10 bg-white/[0.03] px-4 py-3 text-xs text-slate-500">
        Showing {formatNumber(dataset.previewRowCount)} preview rows from{" "}
        {formatNumber(dataset.rowCount)} total rows.
      </div>
    </div>
  );
}

function CellValue({ value }: { value: PreviewCellValue }) {
  if (value === null) {
    return <span className="font-mono text-xs text-slate-600">NULL</span>;
  }

  if (typeof value === "boolean") {
    return (
      <span className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-xs text-slate-300">
        {value ? "true" : "false"}
      </span>
    );
  }

  if (typeof value === "number") {
    return <span className="font-mono text-cyan-100">{value}</span>;
  }

  return <span>{value}</span>;
}

function parseFilePreviewResponse(payload: unknown): FilePreviewResponse | null {
  if (!isRecord(payload) || payload.version !== FILE_PREVIEW_VERSION) {
    return null;
  }

  if (payload.status === "error") {
    return parsePreviewError(payload);
  }

  if (payload.status !== "ok" || !isRecord(payload.dataset)) {
    return null;
  }

  const dataset = parsePreviewDataset(payload.dataset);

  if (!dataset || !isStringArray(payload.warnings)) {
    return null;
  }

  return {
    version: FILE_PREVIEW_VERSION,
    status: "ok",
    dataset,
    warnings: payload.warnings,
  };
}

function parsePreviewError(
  payload: Record<string, unknown>,
): FilePreviewErrorResponse | null {
  if (!isRecord(payload.error)) {
    return null;
  }

  const { code, message, recoverable } = payload.error;

  if (
    typeof code !== "string" ||
    typeof message !== "string" ||
    typeof recoverable !== "boolean"
  ) {
    return null;
  }

  return {
    version: FILE_PREVIEW_VERSION,
    status: "error",
    error: { code, message, recoverable },
  };
}

function parsePreviewDataset(payload: Record<string, unknown>): FilePreviewDataset | null {
  if (
    typeof payload.id !== "string" ||
    typeof payload.fileName !== "string" ||
    typeof payload.mimeType !== "string" ||
    !isNonNegativeInteger(payload.sizeBytes) ||
    !isNonNegativeInteger(payload.rowCount) ||
    !isNonNegativeInteger(payload.previewRowCount) ||
    !isNonNegativeInteger(payload.columnCount) ||
    !Array.isArray(payload.columns) ||
    !Array.isArray(payload.previewRows)
  ) {
    return null;
  }

  const columns = parseColumns(payload.columns);

  if (!columns) {
    return null;
  }

  const previewRows = parsePreviewRows(payload.previewRows, columns);

  if (!previewRows) {
    return null;
  }

  return {
    id: payload.id,
    fileName: payload.fileName,
    mimeType: payload.mimeType,
    sizeBytes: payload.sizeBytes,
    rowCount: payload.rowCount,
    previewRowCount: payload.previewRowCount,
    columnCount: payload.columnCount,
    columns,
    previewRows,
  };
}

function parseColumns(payload: unknown[]): DatasetColumn[] | null {
  const columns: DatasetColumn[] = [];

  for (const column of payload) {
    if (!isRecord(column)) {
      return null;
    }

    const { key, label, dataType, nullable, sampleValues } = column;

    if (
      typeof key !== "string" ||
      typeof label !== "string" ||
      !isDatasetColumnType(dataType) ||
      typeof nullable !== "boolean" ||
      !Array.isArray(sampleValues) ||
      !sampleValues.every(isPreviewCellValue)
    ) {
      return null;
    }

    columns.push({ key, label, dataType, nullable, sampleValues });
  }

  return columns;
}

function parsePreviewRows(
  payload: unknown[],
  columns: DatasetColumn[],
): PreviewRow[] | null {
  const previewRows: PreviewRow[] = [];

  for (const row of payload) {
    if (!isRecord(row)) {
      return null;
    }

    const safeRow: PreviewRow = {};

    for (const column of columns) {
      const value = row[column.key];

      if (typeof value === "undefined") {
        safeRow[column.key] = null;
        continue;
      }

      if (!isPreviewCellValue(value)) {
        return null;
      }

      safeRow[column.key] = value;
    }

    previewRows.push(safeRow);
  }

  return previewRows;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isNonNegativeInteger(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    Number.isFinite(value) &&
    value >= 0
  );
}

function isPreviewCellValue(value: unknown): value is PreviewCellValue {
  if (value === null) {
    return true;
  }

  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  return typeof value === "string" || typeof value === "boolean";
}

function isDatasetColumnType(value: unknown): value is DatasetColumnType {
  return (
    value === "string" ||
    value === "number" ||
    value === "integer" ||
    value === "boolean" ||
    value === "date" ||
    value === "datetime" ||
    value === "categorical" ||
    value === "unknown"
  );
}

function hasAcceptedExtension(
  fileName: string,
  acceptedExtensions: readonly string[],
): boolean {
  const normalizedFileName = fileName.toLowerCase();

  return acceptedExtensions.some((extension) =>
    normalizedFileName.endsWith(extension.toLowerCase()),
  );
}

function getDropZoneTitle(status: UploadState["status"]): string {
  if (status === "parsing_schema") {
    return "Parsing CSV...";
  }

  if (status === "dragging") {
    return "Drop the file here";
  }

  return "Drag and drop your CSV here";
}

function formatNumber(value: number): string {
  return NUMBER_FORMATTER.format(value);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kb = bytes / 1024;

  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }

  return `${(kb / 1024).toFixed(1)} MB`;
}

function formatCellTitle(value: PreviewCellValue): string {
  return value === null ? "NULL" : String(value);
}

function getUploadErrorMessage(error: unknown): string {
  if (error instanceof TypeError) {
    return "The upload service is unavailable. Confirm the API is running, then try again.";
  }

  return "The dataset preview could not be created. Please try again with a valid CSV file.";
}

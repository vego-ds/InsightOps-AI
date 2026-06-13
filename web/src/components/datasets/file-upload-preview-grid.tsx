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
  FilePreviewResponse,
  FilePreviewSuccessResponse,
  PreviewCellValue,
  PreviewRow,
} from "@/types/dataset";

type UploadState =
  | { status: "idle" }
  | { status: "dragging" }
  | { status: "parsing_schema"; fileName: string }
  | { status: "success"; response: FilePreviewSuccessResponse }
  | { status: "runtime_error"; message: string };

type FileUploadPreviewGridProps = {
  uploadUrl?: string;
  maxFileSizeMb?: number;
  acceptedExtensions?: string[];
  className?: string;
};

export function FileUploadPreviewGrid({
  uploadUrl = "/api/datasets/upload",
  maxFileSizeMb = 50,
  acceptedExtensions = [".csv"],
  className = "",
}: FileUploadPreviewGridProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);
  const [state, setState] = React.useState<UploadState>({ status: "idle" });
  const clearActiveDataset = useDatasetStore((store) => store.clearActiveDataset);
  const setActiveDataset = useDatasetStore((store) => store.setActiveDataset);
  const setErrorMessage = useDatasetStore((store) => store.setErrorMessage);
  const setUploadStatus = useDatasetStore((store) => store.setUploadStatus);

  const maxFileSizeBytes = maxFileSizeMb * 1024 * 1024;

  const reset = React.useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    if (inputRef.current) {
      inputRef.current.value = "";
    }

    clearActiveDataset();
    setUploadStatus("idle");
    setErrorMessage(null);
    setState({ status: "idle" });
  }, [clearActiveDataset, setErrorMessage, setUploadStatus]);

  const uploadFile = React.useCallback(
    async (file: File) => {
      const extensionIsAllowed = acceptedExtensions.some((extension) =>
        file.name.toLowerCase().endsWith(extension.toLowerCase()),
      );

      if (!extensionIsAllowed) {
        const message = `Unsupported file type. Accepted files: ${acceptedExtensions.join(", ")}`;
        setState({
          status: "runtime_error",
          message,
        });
        setErrorMessage(message);
        return;
      }

      if (file.size > maxFileSizeBytes) {
        const message = `File is too large. Maximum allowed size is ${maxFileSizeMb} MB.`;
        setState({
          status: "runtime_error",
          message,
        });
        setErrorMessage(message);
        return;
      }

      abortControllerRef.current?.abort();

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState({
        status: "parsing_schema",
        fileName: file.name,
      });
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

        const payload: unknown = await response.json();
        const parsed = parseFilePreviewResponse(payload);

        if (!parsed) {
          const message =
            "The backend returned an invalid file preview contract. Rendering was blocked.";
          setState({
            status: "runtime_error",
            message,
          });
          setErrorMessage(message);
          return;
        }

        if (parsed.status === "error") {
          setState({
            status: "runtime_error",
            message: parsed.error.message,
          });
          setErrorMessage(parsed.error.message);
          return;
        }

        if (!response.ok) {
          const message = "Upload failed before the preview dataset could be created.";
          setState({
            status: "runtime_error",
            message,
          });
          setErrorMessage(message);
          return;
        }

        setActiveDataset(parsed.dataset);
        setState({
          status: "success",
          response: parsed,
        });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        const message = getUploadErrorMessage(error);
        setState({
          status: "runtime_error",
          message,
        });
        setErrorMessage(message);
      }
    },
    [
      acceptedExtensions,
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

      const file = event.dataTransfer.files?.[0];

      if (file) {
        void uploadFile(file);
      } else {
        setState({ status: "idle" });
      }
    },
    [uploadFile],
  );

  const showUploadZone =
    state.status === "idle" ||
    state.status === "dragging" ||
    state.status === "parsing_schema" ||
    state.status === "runtime_error";

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
              Drop a CSV file to create a typed dataset preview before the agent
              starts analysis.
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
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                inputRef.current?.click();
              }
            }}
            onDrop={handleDrop}
            onDragOver={(event) => {
              event.preventDefault();
              event.stopPropagation();

              if (state.status !== "parsing_schema") {
                setState({ status: "dragging" });
                setUploadStatus("dragging");
              }
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              event.stopPropagation();

              if (state.status !== "parsing_schema") {
                setState({ status: "idle" });
                setUploadStatus("idle");
              }
            }}
            className={[
              "group relative overflow-hidden rounded-2xl border border-dashed p-8 outline-none transition",
              state.status === "dragging"
                ? "border-cyan-300/70 bg-cyan-400/[0.08] shadow-2xl shadow-cyan-950/40"
                : "border-white/15 bg-black/20 hover:border-cyan-300/50 hover:bg-cyan-400/[0.04]",
              state.status === "parsing_schema"
                ? "cursor-wait"
                : "cursor-pointer",
            ].join(" ")}
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.12),transparent_34rem)]" />

            <input
              ref={inputRef}
              type="file"
              accept={acceptedExtensions.join(",")}
              className="hidden"
              disabled={state.status === "parsing_schema"}
              onChange={handleInputChange}
            />

            <div className="relative flex flex-col items-center justify-center text-center">
              <div
                className={[
                  "mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border transition",
                  state.status === "dragging"
                    ? "border-cyan-300/40 bg-cyan-300/15"
                    : "border-white/10 bg-white/[0.06] group-hover:border-cyan-300/30 group-hover:bg-cyan-300/10",
                ].join(" ")}
              >
                {state.status === "parsing_schema" ? (
                  <Loader2 className="h-7 w-7 animate-spin text-cyan-200" />
                ) : (
                  <UploadCloud className="h-7 w-7 text-cyan-200" />
                )}
              </div>

              <div className="text-base font-medium text-white">
                {state.status === "parsing_schema"
                  ? "Parsing CSV..."
                  : state.status === "dragging"
                    ? "Drop the file here"
                    : "Drag and drop your CSV here"}
              </div>

              <p className="mt-2 text-sm text-slate-400">
                {state.status === "parsing_schema"
                  ? state.fileName
                  : `or click to browse. Max file size ${maxFileSizeMb} MB.`}
              </p>

              {state.status === "runtime_error" ? (
                <div className="mt-5 flex max-w-xl items-start gap-3 rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-left">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-300" />
                  <div>
                    <p className="text-sm font-medium text-red-100">
                      Upload failed
                    </p>
                    <p className="mt-1 text-sm leading-5 text-red-200/80">
                      {state.message}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {state.status === "success" ? (
          <DatasetPreviewTable dataset={state.response.dataset} />
        ) : null}
      </div>
    </section>
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
              <th className="sticky left-0 z-20 border-b border-r border-white/10 bg-[#10131F] px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-400">
                #
              </th>

              {dataset.columns.map((column) => (
                <th
                  key={column.key}
                  className="whitespace-nowrap border-b border-white/10 px-4 py-3 align-bottom"
                >
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-200">
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

                {dataset.columns.map((column) => (
                  <td
                    key={`${rowIndex}-${column.key}`}
                    className="max-w-[280px] truncate border-b border-white/10 px-4 py-3 text-slate-300"
                    title={formatCellTitle(row[column.key])}
                  >
                    <CellValue value={row[column.key]} />
                  </td>
                ))}
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

function CellValue({ value }: { value: PreviewCellValue | undefined }) {
  if (value === null || typeof value === "undefined") {
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
  if (!isRecord(payload)) {
    return null;
  }

  if (payload.version !== "insightops.file-preview.v1") {
    return null;
  }

  if (payload.status === "error") {
    if (!isRecord(payload.error)) {
      return null;
    }

    if (
      typeof payload.error.code !== "string" ||
      typeof payload.error.message !== "string" ||
      typeof payload.error.recoverable !== "boolean"
    ) {
      return null;
    }

    return {
      version: "insightops.file-preview.v1",
      status: "error",
      error: {
        code: payload.error.code,
        message: payload.error.message,
        recoverable: payload.error.recoverable,
      },
    };
  }

  if (payload.status !== "ok" || !isRecord(payload.dataset)) {
    return null;
  }

  const dataset = payload.dataset;

  if (
    typeof dataset.id !== "string" ||
    typeof dataset.fileName !== "string" ||
    typeof dataset.mimeType !== "string" ||
    typeof dataset.sizeBytes !== "number" ||
    typeof dataset.rowCount !== "number" ||
    typeof dataset.previewRowCount !== "number" ||
    typeof dataset.columnCount !== "number" ||
    !Array.isArray(dataset.columns) ||
    !Array.isArray(dataset.previewRows) ||
    !Array.isArray(payload.warnings)
  ) {
    return null;
  }

  const columns: DatasetColumn[] = [];

  for (const column of dataset.columns) {
    if (!isRecord(column)) {
      return null;
    }

    if (
      typeof column.key !== "string" ||
      typeof column.label !== "string" ||
      !isDatasetColumnType(column.dataType) ||
      typeof column.nullable !== "boolean" ||
      !Array.isArray(column.sampleValues) ||
      !column.sampleValues.every(isPreviewCellValue)
    ) {
      return null;
    }

    columns.push({
      key: column.key,
      label: column.label,
      dataType: column.dataType,
      nullable: column.nullable,
      sampleValues: column.sampleValues,
    });
  }

  const previewRows: PreviewRow[] = [];

  for (const row of dataset.previewRows) {
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

  return {
    version: "insightops.file-preview.v1",
    status: "ok",
    dataset: {
      id: dataset.id,
      fileName: dataset.fileName,
      mimeType: dataset.mimeType,
      sizeBytes: dataset.sizeBytes,
      rowCount: dataset.rowCount,
      previewRowCount: dataset.previewRowCount,
      columnCount: dataset.columnCount,
      columns,
      previewRows,
    },
    warnings: payload.warnings.filter(
      (warning): warning is string => typeof warning === "string",
    ),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPreviewCellValue(value: unknown): value is PreviewCellValue {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null
  );
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

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en").format(value);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kb = bytes / 1024;

  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }

  const mb = kb / 1024;

  return `${mb.toFixed(1)} MB`;
}

function formatCellTitle(value: PreviewCellValue | undefined): string {
  if (value === null || typeof value === "undefined") {
    return "NULL";
  }

  return String(value);
}

function getUploadErrorMessage(error: unknown): string {
  if (error instanceof TypeError) {
    return "Could not reach the backend upload service. Check that the API is running, then try again.";
  }
  if (error instanceof Error && error.message.trim()) {
    return "Upload failed before the dataset preview could be created. Please try again with a valid CSV file.";
  }
  return "An unknown upload error occurred. Please try again.";
}

"use client";

import * as React from "react";
import { AlertCircle, Database, Loader2, Rows3, Table2, Trash2 } from "lucide-react";

import { ArtifactGallery } from "@/components/artifacts/artifact-gallery";
import {
  DatasetPreviewTable,
  FileUploadPreviewGrid,
} from "@/components/datasets/file-upload-preview-grid";
import { SchemaInspector } from "@/components/datasets/schema-inspector";
import {
  CanvasModeTabs,
  type CanvasMode,
} from "@/components/workspace/canvas-mode-tabs";
import { deleteDataset } from "@/lib/dataset-client";
import { useArtifactStore } from "@/stores/artifact-store";
import { useCanvasStore } from "@/stores/canvas-store";
import { useChatStore } from "@/stores/chat-store";
import { useDatasetStore } from "@/stores/dataset-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useNotebookStore } from "@/stores/notebook-store";
import { useRunHistoryStore } from "@/stores/run-history-store";

export function DataCanvas() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
  const errorMessage = useDatasetStore((store) => store.errorMessage);
  const uploadStatus = useDatasetStore((store) => store.uploadStatus);
  const artifactCount = useArtifactStore((store) => store.artifacts.length);
  const activeRunId = useArtifactStore((store) => store.activeRunId);
  const mode = useCanvasStore((store) => store.activeMode);
  const setActiveMode = useCanvasStore((store) => store.setActiveMode);
  const visibleMode: CanvasMode =
    activeDataset && (mode !== "artifacts" || artifactCount > 0) ? mode : "preview";
  const handleModeChange = (nextMode: CanvasMode) => {
    setActiveMode(nextMode, "user", activeRunId);
  };

  if (!activeDataset) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-4">
        <CanvasModeTabs
          mode={visibleMode}
          schemaDisabled
          artifactsDisabled
          onModeChange={handleModeChange}
        />
        {errorMessage ? <RuntimeErrorPanel message={errorMessage} /> : null}
        <FileUploadPreviewGrid uploadUrl="/api/datasets/upload" />
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <DatasetSummaryBar />
      <CanvasModeTabs
        mode={visibleMode}
        schemaDisabled={false}
        artifactsDisabled={artifactCount === 0}
        onModeChange={handleModeChange}
      />

      {visibleMode === "preview" ? (
        <DatasetPreviewTable dataset={activeDataset} />
      ) : null}
      {visibleMode === "schema" ? (
        <SchemaInspector />
      ) : null}
      {visibleMode === "artifacts" ? <ArtifactGallery /> : null}

      {uploadStatus === "runtime_error" && errorMessage ? (
        <RuntimeErrorPanel message={errorMessage} />
      ) : null}
    </div>
  );
}

function DatasetSummaryBar() {
  const dataset = useDatasetStore((store) => store.activeDataset);
  const clearActiveDataset = useDatasetStore((store) => store.clearActiveDataset);
  const setErrorMessage = useDatasetStore((store) => store.setErrorMessage);
  const selectedColumnKey = useDatasetStore((store) => store.selectedColumnKey);
  const clearMessages = useChatStore((store) => store.clearMessages);
  const clearArtifacts = useArtifactStore((store) => store.clearArtifacts);
  const clearAllRunEvents = useExecutionStore((store) => store.clearAllRunEvents);
  const clearAllNotebooks = useNotebookStore((store) => store.clearAllNotebooks);
  const clearHistory = useRunHistoryStore((store) => store.clearHistory);
  const resetCanvas = useCanvasStore((store) => store.resetCanvas);
  const [isClearing, setIsClearing] = React.useState(false);

  const handleClearDataset = async () => {
    if (!dataset || isClearing) {
      return;
    }

    setIsClearing(true);
    setErrorMessage(null);
    try {
      await deleteDataset(dataset.id);
      clearMessages();
      clearArtifacts();
      clearAllRunEvents();
      clearAllNotebooks();
      clearHistory();
      resetCanvas();
      clearActiveDataset();
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Dataset deletion failed.";
      setErrorMessage(message);
    } finally {
      setIsClearing(false);
    }
  };

  if (!dataset) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
      <div className="grid gap-3 md:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
        <SummaryItem
          icon={<Database className="h-4 w-4" />}
          label="Active dataset"
          value={dataset.fileName}
        />
        <SummaryItem
          icon={<Rows3 className="h-4 w-4" />}
          label="Rows"
          value={formatNumber(dataset.rowCount)}
        />
        <SummaryItem
          icon={<Table2 className="h-4 w-4" />}
          label="Columns"
          value={formatNumber(dataset.columnCount)}
        />
        <SummaryItem
          icon={<Rows3 className="h-4 w-4" />}
          label="Selected column"
          value={selectedColumnKey ?? "None"}
        />
        <button
          type="button"
          onClick={() => void handleClearDataset()}
          disabled={isClearing}
          className="inline-flex min-h-[68px] items-center justify-center gap-2 rounded-xl border border-red-300/20 bg-red-500/10 px-4 text-sm font-medium text-red-100 transition hover:border-red-300/35 hover:bg-red-500/15 disabled:cursor-wait disabled:opacity-70"
        >
          {isClearing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          Clear
        </button>
      </div>
    </section>
  );
}

function SummaryItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-white/10 bg-black/20 px-3 py-3">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500">
        <span className="text-cyan-200">{icon}</span>
        {label}
      </div>
      <div className="mt-2 truncate text-sm font-semibold text-slate-100">
        {value}
      </div>
    </div>
  );
}

function RuntimeErrorPanel({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-red-100">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-300" />
      <div>
        <p className="text-sm font-medium">Runtime error</p>
        <p className="mt-1 text-sm leading-5 text-red-200/80">{message}</p>
      </div>
    </div>
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en").format(value);
}

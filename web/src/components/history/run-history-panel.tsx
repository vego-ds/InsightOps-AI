"use client";

import {
  Archive,
  CheckCircle2,
  Clock3,
  Download,
  History,
  Loader2,
  TriangleAlert,
} from "lucide-react";

import { ExecutionTimeline } from "@/components/execution/execution-timeline";
import { exportRunReport } from "@/lib/export-artifacts";
import { useArtifactStore } from "@/stores/artifact-store";
import { useCanvasStore } from "@/stores/canvas-store";
import {
  type RunHistoryRecord,
  useRunHistoryStore,
} from "@/stores/run-history-store";

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function RunHistoryPanel() {
  const runs = useRunHistoryStore((store) => store.runs);
  const selectedRunId = useRunHistoryStore((store) => store.selectedRunId);
  const selectRun = useRunHistoryStore((store) => store.selectRun);
  const setSelectedArtifactForRun = useRunHistoryStore(
    (store) => store.setSelectedArtifactForRun,
  );
  const setActiveRunId = useArtifactStore((store) => store.setActiveRunId);
  const selectBestArtifactForRun = useArtifactStore(
    (store) => store.selectBestArtifactForRun,
  );
  const allArtifacts = useArtifactStore((store) => store.artifacts);
  const setActiveMode = useCanvasStore((store) => store.setActiveMode);
  const selectedRun = runs.find((run) => run.runId === selectedRunId) ?? null;
  const selectedRunArtifacts = selectedRun
    ? allArtifacts.filter((artifact) => selectedRun.artifactIds.includes(artifact.id))
    : [];

  const handleSelectRun = (run: RunHistoryRecord) => {
    selectRun(run.runId);
    setActiveRunId(run.runId);

    if (run.artifactIds.length > 0) {
      setActiveMode("artifacts", "user", run.runId);
      const bestArtifact = selectBestArtifactForRun(run.runId, "user");
      setSelectedArtifactForRun(run.runId, bestArtifact?.id ?? null);
    }
  };

  return (
    <section className="flex min-h-0 flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
          <History className="h-4 w-4 text-cyan-200" />
          Run history
        </div>
        <span className="rounded-full border border-white/10 bg-black/20 px-2 py-0.5 text-[11px] font-medium text-slate-500">
          {runs.length}
        </span>
      </header>

      {runs.length === 0 ? (
        <div className="mt-4 rounded-xl border border-dashed border-white/10 bg-black/20 px-3 py-4">
          <p className="text-sm font-medium text-slate-200">No runs yet</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Completed analyses will appear here for quick artifact and timeline
            review.
          </p>
        </div>
      ) : (
        <div className="mt-4 max-h-[300px] space-y-2 overflow-y-auto pr-1">
          {runs.map((run) => (
            <button
              key={run.runId}
              type="button"
              onClick={() => handleSelectRun(run)}
              className={[
                "w-full rounded-xl border px-3 py-3 text-left transition",
                run.runId === selectedRunId
                  ? "border-cyan-300/30 bg-cyan-300/10"
                  : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-white/[0.04]",
              ].join(" ")}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="line-clamp-2 min-w-0 text-sm font-medium leading-5 text-slate-100">
                  {run.prompt}
                </p>
                <RunStatusBadge status={run.status} />
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Archive className="h-3.5 w-3.5" />
                  {run.artifactIds.length}
                </span>
                <span className="flex items-center gap-1">
                  <Clock3 className="h-3.5 w-3.5" />
                  {formatTimestamp(run.createdAt)}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {selectedRun ? (
        <div className="mt-4 border-t border-white/10 pt-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Selected timeline
            </p>
            <div className="flex items-center gap-2">
              <span className="truncate text-[11px] text-slate-600">
                {selectedRun.runId.slice(0, 8)}
              </span>
              <button
                type="button"
                onClick={() =>
                  exportRunReport({
                    run: selectedRun,
                    artifacts: selectedRunArtifacts,
                  })
                }
                className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-[11px] font-medium text-slate-400 transition hover:border-cyan-300/30 hover:bg-cyan-300/10 hover:text-cyan-100"
              >
                <Download className="h-3 w-3" />
                Export report
              </button>
            </div>
          </div>
          <ExecutionTimeline runId={selectedRun.runId} />
          {selectedRun.finalAnswer ? (
            <p className="mt-3 line-clamp-4 text-xs leading-5 text-slate-400">
              {selectedRun.finalAnswer}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function RunStatusBadge({ status }: { status: RunHistoryRecord["status"] }) {
  if (status === "running") {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-0.5 text-[11px] font-medium text-amber-100">
        <Loader2 className="h-3 w-3 animate-spin" />
        Running
      </span>
    );
  }

  if (status === "error") {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-red-300/20 bg-red-500/10 px-2 py-0.5 text-[11px] font-medium text-red-100">
        <TriangleAlert className="h-3 w-3" />
        Error
      </span>
    );
  }

  return (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2 py-0.5 text-[11px] font-medium text-emerald-100">
      <CheckCircle2 className="h-3 w-3" />
      Complete
    </span>
  );
}

function formatTimestamp(value: string): string {
  return DATE_TIME_FORMATTER.format(new Date(value));
}

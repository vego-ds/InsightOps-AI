"use client";

import * as React from "react";
import { Archive, CheckCircle2 } from "lucide-react";

import { ExecutionStatusCard } from "@/components/execution/execution-status-card";
import { RuntimeErrorCard } from "@/components/execution/runtime-error-card";
import { NotebookCell } from "@/components/notebook/notebook-cell";
import { useExecutionStore } from "@/stores/execution-store";
import { useNotebookStore } from "@/stores/notebook-store";
import type { AnalysisRunEvent } from "@/types/execution";
import type { NotebookCellModel, NotebookRepairState } from "@/types/notebook";

const EMPTY_EXECUTION_EVENTS: AnalysisRunEvent[] = [];
const EMPTY_NOTEBOOK_CELL_IDS: string[] = [];
const EMPTY_NOTEBOOK_CELLS: Record<string, NotebookCellModel> = {};
const EMPTY_NOTEBOOK_REPAIRS: NotebookRepairState[] = [];
const NOTEBOOK_UPDATE_EVENT_TYPES = new Set<AnalysisRunEvent["type"]>([
  "run.cell.stdout",
  "run.cell.stderr",
  "run.cell.completed",
  "run.cell.failed",
  "run.repair.started",
  "run.repair.completed",
]);

export function ExecutionTimeline({ runId }: { runId: string }) {
  const events = useExecutionStore(
    (store) => store.eventsByRunId[runId] ?? EMPTY_EXECUTION_EVENTS,
  );
  const cellIds = useNotebookStore(
    (store) => store.cellOrderByRunId[runId] ?? EMPTY_NOTEBOOK_CELL_IDS,
  );
  const cellsById = useNotebookStore(
    (store) => store.cellsByRunId[runId] ?? EMPTY_NOTEBOOK_CELLS,
  );
  const repairs = useNotebookStore(
    (store) => store.repairsByRunId[runId] ?? EMPTY_NOTEBOOK_REPAIRS,
  );
  const cellIdSet = React.useMemo(() => new Set(cellIds), [cellIds]);
  const repairsByCellId = React.useMemo(
    () => indexRepairsByCellId(repairs),
    [repairs],
  );

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-500">
        Waiting for execution events...
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-2">
      {events.map((event) => {
        if (NOTEBOOK_UPDATE_EVENT_TYPES.has(event.type)) {
          return null;
        }

        if (event.type === "run.cell.started") {
          const cell = cellsById[event.cellId];
          if (!cell || !cellIdSet.has(event.cellId)) {
            return null;
          }
          return (
            <NotebookCell
              key={event.cellId}
              cell={cell}
              repairs={repairsByCellId.get(event.cellId) ?? EMPTY_NOTEBOOK_REPAIRS}
            />
          );
        }

        if (event.type === "run.status") {
          return <ExecutionStatusCard key={event.sequence} event={event} />;
        }

        if (event.type === "run.error") {
          return <RuntimeErrorCard key={event.sequence} event={event} />;
        }

        if (event.type === "artifact") {
          return <ArtifactEventCard key={event.sequence} event={event} />;
        }

        if (event.type === "run.final") {
          return <FinalEventCard key={event.sequence} />;
        }

        return null;
      })}
    </div>
  );
}

function ArtifactEventCard({
  event,
}: {
  event: Extract<AnalysisRunEvent, { type: "artifact" }>;
}) {
  return (
    <div className="rounded-xl border border-violet-300/20 bg-violet-300/10 px-3 py-2">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-violet-100">
        <Archive className="h-3.5 w-3.5" />
        artifact: {event.artifact.kind}
      </div>
      <p className="mt-1 text-sm text-violet-50/90">{event.artifact.title}</p>
    </div>
  );
}

function FinalEventCard() {
  return (
    <div className="rounded-xl border border-emerald-300/20 bg-emerald-300/10 px-3 py-2">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-emerald-100">
        <CheckCircle2 className="h-3.5 w-3.5" />
        final response ready
      </div>
    </div>
  );
}

function indexRepairsByCellId(
  repairs: NotebookRepairState[],
): Map<string, NotebookRepairState[]> {
  const index = new Map<string, NotebookRepairState[]>();

  for (const repair of repairs) {
    appendRepair(index, repair.failedCellId, repair);

    if (repair.repairCellId !== repair.failedCellId) {
      appendRepair(index, repair.repairCellId, repair);
    }
  }

  return index;
}

function appendRepair(
  index: Map<string, NotebookRepairState[]>,
  cellId: string,
  repair: NotebookRepairState,
) {
  const existing = index.get(cellId);
  if (existing) {
    existing.push(repair);
    return;
  }

  index.set(cellId, [repair]);
}

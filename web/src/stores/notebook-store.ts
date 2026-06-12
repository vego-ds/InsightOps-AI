"use client";

import { create } from "zustand";

import type {
  NotebookCellModel,
  NotebookRepairState,
  NotebookRunEvent,
} from "@/types/notebook";

type NotebookStoreState = {
  cellOrderByRunId: Record<string, string[]>;
  cellsByRunId: Record<string, Record<string, NotebookCellModel>>;
  repairsByRunId: Record<string, NotebookRepairState[]>;
  appendNotebookEvent: (event: NotebookRunEvent) => void;
  clearRunNotebook: (runId: string) => void;
};

export const useNotebookStore = create<NotebookStoreState>((set) => ({
  cellOrderByRunId: {},
  cellsByRunId: {},
  repairsByRunId: {},

  appendNotebookEvent: (event) =>
    set((state) => {
      if (event.type === "run.repair.started") {
        return appendRepairStarted(state, event);
      }
      if (event.type === "run.repair.completed") {
        return appendRepairCompleted(state, event);
      }

      return appendCellEvent(state, event);
    }),

  clearRunNotebook: (runId) =>
    set((state) => {
      const nextCellOrderByRunId = { ...state.cellOrderByRunId };
      const nextCellsByRunId = { ...state.cellsByRunId };
      const nextRepairsByRunId = { ...state.repairsByRunId };
      delete nextCellOrderByRunId[runId];
      delete nextCellsByRunId[runId];
      delete nextRepairsByRunId[runId];
      return {
        cellOrderByRunId: nextCellOrderByRunId,
        cellsByRunId: nextCellsByRunId,
        repairsByRunId: nextRepairsByRunId,
      };
    }),
}));

function appendCellEvent(
  state: NotebookStoreState,
  event: Exclude<
    NotebookRunEvent,
    { type: "run.repair.started" | "run.repair.completed" }
  >,
) {
  const cellsForRun = state.cellsByRunId[event.runId] ?? {};
  const currentCell = cellsForRun[event.cellId];
  const nextCell = reduceCellEvent(currentCell, event);
  if (!nextCell) {
    return state;
  }

  const existingOrder = state.cellOrderByRunId[event.runId] ?? [];
  const nextOrder = existingOrder.includes(event.cellId)
    ? existingOrder
    : [...existingOrder, event.cellId];

  return {
    cellOrderByRunId: {
      ...state.cellOrderByRunId,
      [event.runId]: nextOrder,
    },
    cellsByRunId: {
      ...state.cellsByRunId,
      [event.runId]: {
        ...cellsForRun,
        [event.cellId]: nextCell,
      },
    },
    repairsByRunId: state.repairsByRunId,
  };
}

function reduceCellEvent(
  cell: NotebookCellModel | undefined,
  event: Exclude<
    NotebookRunEvent,
    { type: "run.repair.started" | "run.repair.completed" }
  >,
): NotebookCellModel | null {
  if (event.type === "run.cell.started") {
    return {
      runId: event.runId,
      cellId: event.cellId,
      title: event.title,
      language: event.language,
      code: event.code,
      attempt: event.attempt,
      status: "running",
      startedSequence: event.sequence,
      stdout: [],
      stderr: [],
    };
  }

  if (!cell) {
    return null;
  }

  if (event.type === "run.cell.stdout") {
    return {
      ...cell,
      stdout: [...cell.stdout, event.stdout],
    };
  }

  if (event.type === "run.cell.stderr") {
    return {
      ...cell,
      stderr: [...cell.stderr, event.stderr],
    };
  }

  if (event.type === "run.cell.completed") {
    return {
      ...cell,
      status: "completed",
      completedSequence: event.sequence,
      durationMs: event.durationMs,
    };
  }

  return {
    ...cell,
    status: "failed",
    completedSequence: event.sequence,
    durationMs: event.durationMs,
    errorMessage: event.errorMessage,
    traceback: event.traceback,
  };
}

function appendRepairStarted(
  state: NotebookStoreState,
  event: Extract<NotebookRunEvent, { type: "run.repair.started" }>,
) {
  const repairs = state.repairsByRunId[event.runId] ?? [];
  const existing = repairs.find(
    (repair) =>
      repair.failedCellId === event.failedCellId &&
      repair.repairCellId === event.repairCellId,
  );

  if (existing) {
    return state;
  }

  return {
    cellOrderByRunId: state.cellOrderByRunId,
    cellsByRunId: state.cellsByRunId,
    repairsByRunId: {
      ...state.repairsByRunId,
      [event.runId]: [
        ...repairs,
        {
          failedCellId: event.failedCellId,
          repairCellId: event.repairCellId,
          status: "started" as const,
          reason: event.reason,
        },
      ],
    },
  };
}

function appendRepairCompleted(
  state: NotebookStoreState,
  event: Extract<NotebookRunEvent, { type: "run.repair.completed" }>,
) {
  const repairs = state.repairsByRunId[event.runId] ?? [];
  const nextRepairs = repairs.map((repair) =>
    repair.failedCellId === event.failedCellId &&
    repair.repairCellId === event.repairCellId
      ? {
          ...repair,
          status: "completed" as const,
          outcome: event.outcome,
        }
      : repair,
  );

  return {
    cellOrderByRunId: state.cellOrderByRunId,
    cellsByRunId: state.cellsByRunId,
    repairsByRunId: {
      ...state.repairsByRunId,
      [event.runId]: nextRepairs,
    },
  };
}

import type { RunEventBase } from "@/types/execution";

export type NotebookCellStatus = "running" | "completed" | "failed";

export type RunCellStartedEvent = RunEventBase & {
  type: "run.cell.started";
  cellId: string;
  title: string;
  language: "python" | string;
  code: string;
  attempt: number;
};

export type RunCellStdoutEvent = RunEventBase & {
  type: "run.cell.stdout";
  cellId: string;
  stdout: string;
};

export type RunCellStderrEvent = RunEventBase & {
  type: "run.cell.stderr";
  cellId: string;
  stderr: string;
};

export type RunCellCompletedEvent = RunEventBase & {
  type: "run.cell.completed";
  cellId: string;
  durationMs: number;
};

export type RunCellFailedEvent = RunEventBase & {
  type: "run.cell.failed";
  cellId: string;
  errorMessage: string;
  traceback: string;
  durationMs: number;
};

export type RunRepairStartedEvent = RunEventBase & {
  type: "run.repair.started";
  failedCellId: string;
  repairCellId: string;
  reason: string;
};

export type RunRepairCompletedEvent = RunEventBase & {
  type: "run.repair.completed";
  failedCellId: string;
  repairCellId: string;
  outcome: string;
};

export type NotebookRunEvent =
  | RunCellStartedEvent
  | RunCellStdoutEvent
  | RunCellStderrEvent
  | RunCellCompletedEvent
  | RunCellFailedEvent
  | RunRepairStartedEvent
  | RunRepairCompletedEvent;

export type NotebookRepairState = {
  failedCellId: string;
  repairCellId: string;
  status: "started" | "completed";
  reason: string;
  outcome?: string;
};

export type NotebookCellModel = {
  runId: string;
  cellId: string;
  title: string;
  language: string;
  code: string;
  attempt: number;
  status: NotebookCellStatus;
  startedSequence: number;
  completedSequence?: number;
  durationMs?: number;
  stdout: string[];
  stderr: string[];
  errorMessage?: string;
  traceback?: string;
};

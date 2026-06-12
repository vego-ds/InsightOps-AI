import type {
  AnalysisRunCreatedResponse,
  AnalysisRunCreateRequest,
  AnalysisRunEvent,
} from "@/types/execution";
import { parseArtifact } from "@/lib/artifact-validators";

export async function createAnalysisRun(
  body: AnalysisRunCreateRequest,
): Promise<AnalysisRunCreatedResponse> {
  const response = await fetch("/api/analysis/runs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("Run creation endpoint returned a non-JSON response.");
  }

  if (!response.ok) {
    throw new Error("Analysis run creation was rejected by the backend.");
  }

  const parsed = parseRunCreatedResponse(payload);
  if (!parsed) {
    throw new Error("Run creation endpoint returned an invalid response contract.");
  }

  return parsed;
}

export function parseRunEvent(payload: unknown): AnalysisRunEvent | null {
  if (!isRecord(payload)) {
    return null;
  }

  if (
    payload.version !== "insightops.run-event.v1" ||
    typeof payload.runId !== "string" ||
    payload.runId.trim().length === 0 ||
    typeof payload.sequence !== "number" ||
    !Number.isInteger(payload.sequence) ||
    payload.sequence < 1 ||
    typeof payload.type !== "string"
  ) {
    return null;
  }

  if (payload.type === "run.status") {
    if (typeof payload.status !== "string" || !payload.status) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.status",
      status: payload.status,
    };
  }

  if (payload.type === "run.code") {
    if (typeof payload.language !== "string" || typeof payload.code !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.code",
      language: payload.language,
      code: payload.code,
    };
  }

  if (payload.type === "run.stdout") {
    if (typeof payload.stdout !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.stdout",
      stdout: payload.stdout,
    };
  }

  if (payload.type === "run.error") {
    if (typeof payload.errorMessage !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.error",
      errorMessage: payload.errorMessage,
    };
  }

  if (payload.type === "run.cell.started") {
    if (
      typeof payload.cellId !== "string" ||
      typeof payload.title !== "string" ||
      typeof payload.language !== "string" ||
      typeof payload.code !== "string" ||
      typeof payload.attempt !== "number" ||
      !Number.isInteger(payload.attempt) ||
      payload.attempt < 1
    ) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.cell.started",
      cellId: payload.cellId,
      title: payload.title,
      language: payload.language,
      code: payload.code,
      attempt: payload.attempt,
    };
  }

  if (payload.type === "run.cell.stdout") {
    if (typeof payload.cellId !== "string" || typeof payload.stdout !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.cell.stdout",
      cellId: payload.cellId,
      stdout: payload.stdout,
    };
  }

  if (payload.type === "run.cell.stderr") {
    if (typeof payload.cellId !== "string" || typeof payload.stderr !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.cell.stderr",
      cellId: payload.cellId,
      stderr: payload.stderr,
    };
  }

  if (payload.type === "run.cell.completed") {
    if (
      typeof payload.cellId !== "string" ||
      typeof payload.durationMs !== "number" ||
      !Number.isFinite(payload.durationMs) ||
      payload.durationMs < 0
    ) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.cell.completed",
      cellId: payload.cellId,
      durationMs: payload.durationMs,
    };
  }

  if (payload.type === "run.cell.failed") {
    if (
      typeof payload.cellId !== "string" ||
      typeof payload.errorMessage !== "string" ||
      typeof payload.traceback !== "string" ||
      typeof payload.durationMs !== "number" ||
      !Number.isFinite(payload.durationMs) ||
      payload.durationMs < 0
    ) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.cell.failed",
      cellId: payload.cellId,
      errorMessage: payload.errorMessage,
      traceback: payload.traceback,
      durationMs: payload.durationMs,
    };
  }

  if (payload.type === "run.repair.started") {
    if (
      typeof payload.failedCellId !== "string" ||
      typeof payload.repairCellId !== "string" ||
      typeof payload.reason !== "string"
    ) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.repair.started",
      failedCellId: payload.failedCellId,
      repairCellId: payload.repairCellId,
      reason: payload.reason,
    };
  }

  if (payload.type === "run.repair.completed") {
    if (
      typeof payload.failedCellId !== "string" ||
      typeof payload.repairCellId !== "string" ||
      typeof payload.outcome !== "string"
    ) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.repair.completed",
      failedCellId: payload.failedCellId,
      repairCellId: payload.repairCellId,
      outcome: payload.outcome,
    };
  }

  if (payload.type === "run.final") {
    if (typeof payload.assistantMessage !== "string") {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "run.final",
      assistantMessage: payload.assistantMessage,
    };
  }

  if (payload.type === "artifact") {
    const artifact = parseArtifact(payload.artifact);
    if (!artifact) {
      return null;
    }
    return {
      version: "insightops.run-event.v1",
      runId: payload.runId,
      sequence: payload.sequence,
      type: "artifact",
      artifact,
    };
  }

  return null;
}

function parseRunCreatedResponse(payload: unknown): AnalysisRunCreatedResponse | null {
  if (!isRecord(payload)) {
    return null;
  }

  if (
    payload.version !== "insightops.analysis-run-created.v1" ||
    payload.status !== "created" ||
    typeof payload.runId !== "string" ||
    payload.runId.trim().length === 0 ||
    typeof payload.streamUrl !== "string" ||
    !payload.streamUrl.startsWith("/api/analysis/runs/")
  ) {
    return null;
  }

  return {
    version: "insightops.analysis-run-created.v1",
    status: "created",
    runId: payload.runId,
    streamUrl: payload.streamUrl,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

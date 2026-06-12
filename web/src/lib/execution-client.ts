import type {
  AnalysisRunCreatedResponse,
  AnalysisRunCreateRequest,
  AnalysisRunEvent,
} from "@/types/execution";

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

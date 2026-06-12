import type {
  AnalysisRequestBody,
  AnalysisResponseBody,
} from "@/types/analysis";

export async function requestAnalysis(
  body: AnalysisRequestBody,
): Promise<AnalysisResponseBody> {
  const response = await fetch("/api/analysis/request", {
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
    throw new Error("Analysis endpoint returned a non-JSON response.");
  }

  if (!response.ok) {
    throw new Error("Analysis request was rejected by the backend.");
  }

  const parsed = parseAnalysisResponse(payload);
  if (!parsed) {
    throw new Error("Analysis endpoint returned an invalid response contract.");
  }

  return parsed;
}

function parseAnalysisResponse(payload: unknown): AnalysisResponseBody | null {
  if (!isRecord(payload)) {
    return null;
  }

  if (
    payload.version !== "insightops.analysis-response.v1" ||
    payload.status !== "accepted" ||
    typeof payload.runId !== "string" ||
    payload.runId.trim().length === 0 ||
    typeof payload.assistantMessage !== "string" ||
    payload.assistantMessage.trim().length === 0
  ) {
    return null;
  }

  return {
    version: "insightops.analysis-response.v1",
    status: "accepted",
    runId: payload.runId,
    assistantMessage: payload.assistantMessage,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

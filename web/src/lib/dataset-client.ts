type DatasetDeleteResponse = {
  version: "insightops.dataset-delete.v1";
  status: "deleted";
  datasetId: string;
};

type DatasetDeleteError = {
  detail?: string;
  error_code?: string;
};

export async function deleteDataset(
  datasetId: string,
): Promise<DatasetDeleteResponse> {
  const response = await fetch(`/api/datasets/${encodeURIComponent(datasetId)}`, {
    method: "DELETE",
  });
  const payload: unknown = await response.json();

  if (!response.ok) {
    throw new Error(getDeleteErrorMessage(payload));
  }

  if (!isDatasetDeleteResponse(payload) || payload.datasetId !== datasetId) {
    throw new Error("The backend returned an invalid dataset delete response.");
  }

  return payload;
}

function isDatasetDeleteResponse(
  payload: unknown,
): payload is DatasetDeleteResponse {
  if (!payload || typeof payload !== "object") {
    return false;
  }

  const record = payload as Record<string, unknown>;
  return (
    record.version === "insightops.dataset-delete.v1" &&
    record.status === "deleted" &&
    typeof record.datasetId === "string"
  );
}

function getDeleteErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "Dataset deletion failed.";
  }

  const error = payload as DatasetDeleteError;
  if (typeof error.detail === "string" && error.detail.trim()) {
    return error.detail;
  }
  if (error.error_code === "UNKNOWN_DATASET") {
    return "The active dataset is no longer available on the backend.";
  }
  return "Dataset deletion failed.";
}

import type {
  ArtifactScalar,
  ChartArtifact,
  InsightArtifact,
  MarkdownArtifact,
  TableArtifact,
} from "@/types/artifact";

export function parseArtifact(payload: unknown): InsightArtifact | null {
  if (!isRecord(payload)) {
    return null;
  }

  if (
    typeof payload.id !== "string" ||
    !payload.id ||
    typeof payload.kind !== "string" ||
    typeof payload.title !== "string" ||
    !payload.title
  ) {
    return null;
  }

  if (payload.kind === "table") {
    return parseTableArtifact(payload);
  }
  if (payload.kind === "chart") {
    return parseChartArtifact(payload);
  }
  if (payload.kind === "markdown") {
    return parseMarkdownArtifact(payload);
  }

  return null;
}

function parseTableArtifact(payload: Record<string, unknown>): TableArtifact | null {
  if (
    !Array.isArray(payload.columns) ||
    !payload.columns.every((column) => typeof column === "string" && column) ||
    !Array.isArray(payload.rows)
  ) {
    return null;
  }

  const rows: Record<string, ArtifactScalar>[] = [];
  for (const row of payload.rows) {
    if (!isRecord(row)) {
      return null;
    }

    const safeRow: Record<string, ArtifactScalar> = {};
    for (const column of payload.columns) {
      const value = row[column];
      if (!isArtifactScalar(value)) {
        return null;
      }
      safeRow[column] = value;
    }
    rows.push(safeRow);
  }

  return {
    id: payload.id as string,
    kind: "table",
    title: payload.title as string,
    columns: payload.columns,
    rows,
  };
}

function parseChartArtifact(payload: Record<string, unknown>): ChartArtifact | null {
  if (
    (payload.chartType !== "bar" && payload.chartType !== "line") ||
    typeof payload.xKey !== "string" ||
    !payload.xKey ||
    typeof payload.yKey !== "string" ||
    !payload.yKey ||
    !Array.isArray(payload.data)
  ) {
    return null;
  }

  const data: Record<string, string | number>[] = [];
  for (const point of payload.data) {
    if (!isRecord(point)) {
      return null;
    }
    const xValue = point[payload.xKey];
    const yValue = point[payload.yKey];
    if (
      (typeof xValue !== "string" && typeof xValue !== "number") ||
      typeof yValue !== "number" ||
      !Number.isFinite(yValue)
    ) {
      return null;
    }
    data.push({
      [payload.xKey]: xValue,
      [payload.yKey]: yValue,
    });
  }

  return {
    id: payload.id as string,
    kind: "chart",
    title: payload.title as string,
    chartType: payload.chartType,
    xKey: payload.xKey,
    yKey: payload.yKey,
    data,
  };
}

function parseMarkdownArtifact(
  payload: Record<string, unknown>,
): MarkdownArtifact | null {
  if (typeof payload.text !== "string") {
    return null;
  }

  return {
    id: payload.id as string,
    kind: "markdown",
    title: payload.title as string,
    text: payload.text,
  };
}

function isArtifactScalar(value: unknown): value is ArtifactScalar {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

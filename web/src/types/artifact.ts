export type ArtifactKind = "table" | "chart" | "markdown";

export type ArtifactScalar = string | number | boolean | null;

export type TableArtifactColumn = {
  key: string;
  label: string;
  dataType: "string" | "number" | "integer" | "boolean" | "unknown";
};

export type TableArtifact = {
  id: string;
  kind: "table";
  title: string;
  priority?: number;
  columns: TableArtifactColumn[];
  rows: Record<string, ArtifactScalar>[];
};

export type ChartArtifact = {
  id: string;
  kind: "chart";
  title: string;
  priority?: number;
  chartType: "bar" | "line";
  xKey: string;
  yKey: string;
  data: Record<string, string | number>[];
};

export type MarkdownArtifact = {
  id: string;
  kind: "markdown";
  title: string;
  priority?: number;
  text: string;
};

export type InsightArtifact = TableArtifact | ChartArtifact | MarkdownArtifact;

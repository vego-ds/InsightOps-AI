export type ArtifactKind = "table" | "chart" | "markdown";

export type ArtifactScalar = string | number | boolean | null;

export type TableArtifact = {
  id: string;
  kind: "table";
  title: string;
  columns: string[];
  rows: Record<string, ArtifactScalar>[];
};

export type ChartArtifact = {
  id: string;
  kind: "chart";
  title: string;
  chartType: "bar" | "line";
  xKey: string;
  yKey: string;
  data: Record<string, string | number>[];
};

export type MarkdownArtifact = {
  id: string;
  kind: "markdown";
  title: string;
  text: string;
};

export type InsightArtifact = TableArtifact | ChartArtifact | MarkdownArtifact;

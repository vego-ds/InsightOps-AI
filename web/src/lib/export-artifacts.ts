import type {
  ChartArtifact,
  InsightArtifact,
  MarkdownArtifact,
  TableArtifact,
} from "@/types/artifact";
import type { RunHistoryRecord } from "@/stores/run-history-store";

type RunReportInput = {
  run: RunHistoryRecord;
  artifacts: InsightArtifact[];
};

export function exportArtifact(artifact: InsightArtifact): void {
  if (artifact.kind === "table") {
    downloadTextFile(
      tableArtifactToCsv(artifact),
      `${sanitizeFilename(artifact.title)}.csv`,
      "text/csv;charset=utf-8",
    );
    return;
  }

  if (artifact.kind === "chart") {
    downloadTextFile(
      chartArtifactToCsv(artifact),
      `${sanitizeFilename(artifact.title)}-chart-data.csv`,
      "text/csv;charset=utf-8",
    );
    return;
  }

  downloadTextFile(
    markdownArtifactToMarkdown(artifact),
    `${sanitizeFilename(artifact.title)}.md`,
    "text/markdown;charset=utf-8",
  );
}

export function exportRunReport({ run, artifacts }: RunReportInput): void {
  downloadTextFile(
    buildRunReportMarkdown({ run, artifacts }),
    `${sanitizeFilename(`run-${run.runId.slice(0, 8)}-report`)}.md`,
    "text/markdown;charset=utf-8",
  );
}

export function tableArtifactToCsv(artifact: TableArtifact): string {
  const header = artifact.columns.map((column) => column.label);
  const rows = artifact.rows.map((row) =>
    artifact.columns.map((column) => row[column.key] ?? null),
  );

  return rowsToCsv([header, ...rows]);
}

export function chartArtifactToCsv(artifact: ChartArtifact): string {
  const keys = [artifact.xKey, artifact.yKey];
  const rows = artifact.data.map((row) => keys.map((key) => row[key] ?? ""));

  return rowsToCsv([keys, ...rows]);
}

export function markdownArtifactToMarkdown(artifact: MarkdownArtifact): string {
  return `# ${artifact.title}\n\n${artifact.text.trim()}\n`;
}

export function buildRunReportMarkdown({
  run,
  artifacts,
}: RunReportInput): string {
  const lines = [
    `# InsightOps-AI Run Report`,
    "",
    `- Run ID: ${run.runId}`,
    `- Dataset ID: ${run.datasetId}`,
    `- Status: ${run.status}`,
    `- Created: ${run.createdAt}`,
    `- Completed: ${run.completedAt ?? "Not completed"}`,
    "",
    "## Prompt",
    "",
    run.prompt,
    "",
    "## Final Answer",
    "",
    run.finalAnswer ?? "No final answer recorded.",
    "",
    "## Artifacts",
    "",
  ];

  if (artifacts.length === 0) {
    lines.push("No artifacts were generated for this run.", "");
    return `${lines.join("\n")}\n`;
  }

  for (const artifact of artifacts) {
    lines.push(`### ${artifact.title}`, "", `- Type: ${artifact.kind}`, "");
    if (artifact.kind === "table") {
      lines.push(`- Rows: ${artifact.rows.length}`);
      lines.push(`- Columns: ${artifact.columns.map((column) => column.label).join(", ")}`);
    } else if (artifact.kind === "chart") {
      lines.push(`- Chart type: ${artifact.chartType}`);
      lines.push(`- X axis: ${artifact.xKey}`);
      lines.push(`- Y axis: ${artifact.yKey}`);
      lines.push(`- Data points: ${artifact.data.length}`);
    } else {
      lines.push(artifact.text.trim());
    }
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

export function sanitizeFilename(value: string): string {
  const sanitized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 96);

  return sanitized || "insightops-export";
}

function rowsToCsv(rows: Array<Array<string | number | boolean | null>>): string {
  return rows.map((row) => row.map(formatCsvCell).join(",")).join("\n");
}

function formatCsvCell(value: string | number | boolean | null): string {
  if (value === null) {
    return "";
  }

  const text = String(value);
  if (/["\n\r,]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function downloadTextFile(
  content: string,
  filename: string,
  mimeType: string,
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

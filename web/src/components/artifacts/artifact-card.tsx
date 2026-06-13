"use client";

import { BarChart3, Download, FileText, Table2 } from "lucide-react";

import { ChartArtifactView } from "@/components/artifacts/chart-artifact-view";
import { MarkdownArtifactView } from "@/components/artifacts/markdown-artifact-view";
import { TableArtifactView } from "@/components/artifacts/table-artifact-view";
import { exportArtifact } from "@/lib/export-artifacts";
import type { InsightArtifact } from "@/types/artifact";

export function ArtifactCard({ artifact }: { artifact: InsightArtifact }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <ArtifactIcon kind={artifact.kind} />
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-white">
              {artifact.title}
            </h3>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {artifact.kind}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => exportArtifact(artifact)}
          className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-cyan-300/30 hover:bg-cyan-300/10 hover:text-cyan-100"
          aria-label={`Export ${artifact.title}`}
        >
          <Download className="h-3.5 w-3.5" />
          Export
        </button>
      </div>

      {artifact.kind === "table" ? <TableArtifactView artifact={artifact} /> : null}
      {artifact.kind === "chart" ? <ChartArtifactView artifact={artifact} /> : null}
      {artifact.kind === "markdown" ? (
        <MarkdownArtifactView artifact={artifact} />
      ) : null}
    </section>
  );
}

function ArtifactIcon({ kind }: { kind: InsightArtifact["kind"] }) {
  const className = "h-4 w-4 text-cyan-200";
  if (kind === "table") {
    return <Table2 className={className} />;
  }
  if (kind === "chart") {
    return <BarChart3 className={className} />;
  }
  return <FileText className={className} />;
}

"use client";

import { BarChart3, FileText, Table2 } from "lucide-react";

import { ArtifactCard } from "@/components/artifacts/artifact-card";
import { useArtifactStore } from "@/stores/artifact-store";
import { useRunHistoryStore } from "@/stores/run-history-store";
import type { InsightArtifact } from "@/types/artifact";

export function ArtifactGallery() {
  const activeRunId = useArtifactStore((store) => store.activeRunId);
  const allArtifacts = useArtifactStore((store) => store.artifacts);
  const selectedArtifactId = useArtifactStore((store) => store.selectedArtifactId);
  const selectArtifact = useArtifactStore((store) => store.selectArtifact);
  const setSelectedArtifactForRun = useRunHistoryStore(
    (store) => store.setSelectedArtifactForRun,
  );
  const activeRunArtifacts = activeRunId
    ? allArtifacts.filter((artifact) => artifact.runId === activeRunId)
    : [];
  const olderArtifacts = activeRunId
    ? allArtifacts.filter((artifact) => artifact.runId !== activeRunId)
    : allArtifacts;
  const artifacts = [...activeRunArtifacts, ...olderArtifacts];
  const selectedArtifact =
    artifacts.find((artifact) => artifact.id === selectedArtifactId) ??
    artifacts[0] ??
    null;

  if (!selectedArtifact) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <p className="text-sm font-medium text-white">No artifacts yet</p>
        <p className="mt-2 text-sm text-slate-400">
          Run an analysis from chat. Tables, charts, and summaries will appear
          here when the execution stream produces safe artifact payloads.
        </p>
      </section>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="rounded-2xl border border-white/10 bg-white/[0.03] p-2">
        {artifacts.map((artifact) => (
          <button
            key={artifact.id}
            type="button"
            onClick={() => {
              selectArtifact(artifact.id, "user");
              if (artifact.runId) {
                setSelectedArtifactForRun(artifact.runId, artifact.id);
              }
            }}
            className={[
              "mb-2 flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition",
              artifact.id === selectedArtifact.id
                ? "border-cyan-300/30 bg-cyan-300/10"
                : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-white/[0.04]",
            ].join(" ")}
          >
            <ArtifactIcon kind={artifact.kind} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-white">
                {artifact.title}
              </p>
              <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                {artifact.kind}
                {artifact.runId === activeRunId ? (
                  <span className="ml-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-100">
                    New
                  </span>
                ) : null}
              </p>
            </div>
          </button>
        ))}
      </aside>
      <ArtifactCard artifact={selectedArtifact} />
    </div>
  );
}

function ArtifactIcon({ kind }: { kind: InsightArtifact["kind"] }) {
  const className = "mt-0.5 h-4 w-4 shrink-0 text-cyan-200";
  if (kind === "table") {
    return <Table2 className={className} />;
  }
  if (kind === "chart") {
    return <BarChart3 className={className} />;
  }
  return <FileText className={className} />;
}

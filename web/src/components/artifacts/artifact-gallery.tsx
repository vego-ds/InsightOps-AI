"use client";

import * as React from "react";
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
  const artifacts = React.useMemo(() => {
    if (!activeRunId) {
      return allArtifacts;
    }

    const activeRunArtifacts = allArtifacts.filter(
      (artifact) => artifact.runId === activeRunId,
    );
    const olderArtifacts = allArtifacts.filter(
      (artifact) => artifact.runId !== activeRunId,
    );
    return [...activeRunArtifacts, ...olderArtifacts];
  }, [activeRunId, allArtifacts]);
  const selectedArtifact = React.useMemo(
    () =>
      artifacts.find((artifact) => artifact.id === selectedArtifactId) ??
      artifacts[0] ??
      null,
    [artifacts, selectedArtifactId],
  );

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
    <div className="grid min-h-0 gap-4 lg:grid-cols-[minmax(220px,280px)_minmax(0,1fr)]">
      <aside className="max-h-64 overflow-y-auto overscroll-contain rounded-2xl border border-white/10 bg-white/[0.03] p-2 lg:max-h-[min(640px,calc(100dvh-220px))]">
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
      <div className="min-w-0">
        <ArtifactCard artifact={selectedArtifact} />
      </div>
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

"use client";

import { Database, ShieldCheck } from "lucide-react";

import { ChatPanel } from "@/components/chat/chat-panel";
import { DataCanvas } from "@/components/workspace/data-canvas";
import { useDatasetStore } from "@/stores/dataset-store";

export function InsightOpsWorkspace() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);

  return (
    <main className="flex min-h-screen flex-col bg-[#050712] text-white">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-[#080A12]/95 px-4 backdrop-blur sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-100">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold tracking-tight text-white">
              InsightOps-AI
            </h1>
            <p className="truncate text-xs text-slate-500">
              Governed data analyst workspace
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-400 sm:flex">
          <Database className="h-3.5 w-3.5 text-cyan-200" />
          {activeDataset ? activeDataset.fileName : "No active dataset"}
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="min-h-[280px] border-b border-white/10 bg-[#080A12] p-4 lg:min-h-0 lg:border-b-0 lg:border-r">
          <ChatPanel />
        </aside>

        <section className="min-w-0 overflow-auto p-4 sm:p-6">
          <DataCanvas />
        </section>
      </div>
    </main>
  );
}

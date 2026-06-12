"use client";

import { Code2 } from "lucide-react";

import type { RunCodeEvent } from "@/types/execution";

export function CodeExecutionCard({ event }: { event: RunCodeEvent }) {
  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-black/30">
      <div className="flex items-center gap-2 border-b border-white/10 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-400">
        <Code2 className="h-3.5 w-3.5 text-cyan-200" />
        {event.language}
      </div>
      <pre className="overflow-x-auto p-3 text-xs leading-5 text-slate-300">
        <code>{event.code}</code>
      </pre>
    </div>
  );
}

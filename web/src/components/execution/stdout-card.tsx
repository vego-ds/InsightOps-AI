"use client";

import { TerminalSquare } from "lucide-react";

import type { RunStdoutEvent } from "@/types/execution";

export function StdoutCard({ event }: { event: RunStdoutEvent }) {
  return (
    <div className="rounded-xl border border-emerald-300/20 bg-emerald-300/10 px-3 py-2">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-emerald-100">
        <TerminalSquare className="h-3.5 w-3.5" />
        stdout
      </div>
      <p className="font-mono text-xs leading-5 text-emerald-50/90">
        {event.stdout}
      </p>
    </div>
  );
}

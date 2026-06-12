"use client";

import { Loader2 } from "lucide-react";

import type { RunStatusEvent } from "@/types/execution";

export function ExecutionStatusCard({ event }: { event: RunStatusEvent }) {
  return (
    <div className="rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-3 py-2">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-cyan-100">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        {formatStatus(event.status)}
      </div>
    </div>
  );
}

function formatStatus(status: string): string {
  return status.replaceAll("_", " ");
}

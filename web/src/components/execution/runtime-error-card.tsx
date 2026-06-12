"use client";

import { TriangleAlert } from "lucide-react";

import type { RunErrorEvent } from "@/types/execution";

export function RuntimeErrorCard({ event }: { event: RunErrorEvent }) {
  return (
    <div className="rounded-xl border border-red-300/20 bg-red-500/10 px-3 py-2">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-red-100">
        <TriangleAlert className="h-3.5 w-3.5" />
        runtime error
      </div>
      <p className="text-sm leading-5 text-red-100/90">{event.errorMessage}</p>
    </div>
  );
}

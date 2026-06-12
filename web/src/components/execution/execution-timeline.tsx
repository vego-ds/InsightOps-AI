"use client";

import { Archive, CheckCircle2 } from "lucide-react";

import { CodeExecutionCard } from "@/components/execution/code-execution-card";
import { ExecutionStatusCard } from "@/components/execution/execution-status-card";
import { RuntimeErrorCard } from "@/components/execution/runtime-error-card";
import { StdoutCard } from "@/components/execution/stdout-card";
import { useExecutionStore } from "@/stores/execution-store";
import type { AnalysisRunEvent } from "@/types/execution";

const EMPTY_EXECUTION_EVENTS: AnalysisRunEvent[] = [];

export function ExecutionTimeline({ runId }: { runId: string }) {
  const events = useExecutionStore(
    (store) => store.eventsByRunId[runId] ?? EMPTY_EXECUTION_EVENTS,
  );

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-500">
        Waiting for execution events...
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-2">
      {events.map((event) => {
        if (event.type === "run.status") {
          return <ExecutionStatusCard key={event.sequence} event={event} />;
        }
        if (event.type === "run.code") {
          return <CodeExecutionCard key={event.sequence} event={event} />;
        }
        if (event.type === "run.stdout") {
          return <StdoutCard key={event.sequence} event={event} />;
        }
        if (event.type === "run.error") {
          return <RuntimeErrorCard key={event.sequence} event={event} />;
        }
        if (event.type === "artifact") {
          return (
            <div
              key={event.sequence}
              className="rounded-xl border border-violet-300/20 bg-violet-300/10 px-3 py-2"
            >
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-violet-100">
                <Archive className="h-3.5 w-3.5" />
                artifact: {event.artifact.kind}
              </div>
              <p className="mt-1 text-sm text-violet-50/90">
                {event.artifact.title}
              </p>
            </div>
          );
        }
        return (
          <div
            key={event.sequence}
            className="rounded-xl border border-emerald-300/20 bg-emerald-300/10 px-3 py-2"
          >
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-emerald-100">
              <CheckCircle2 className="h-3.5 w-3.5" />
              final response ready
            </div>
          </div>
        );
      })}
    </div>
  );
}

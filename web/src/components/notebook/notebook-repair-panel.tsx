"use client";

import { ShieldCheck, Wrench } from "lucide-react";

import type { NotebookRepairState } from "@/types/notebook";

type NotebookRepairPanelProps = {
  repairs: NotebookRepairState[];
};

export function NotebookRepairPanel({ repairs }: NotebookRepairPanelProps) {
  if (repairs.length === 0) {
    return null;
  }

  return (
    <section className="rounded-lg border border-violet-300/20 bg-violet-300/10 px-3 py-2">
      <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-violet-100">
        <Wrench className="h-3.5 w-3.5" />
        self-healing
      </div>
      <div className="mt-2 space-y-2">
        {repairs.map((repair) => (
          <div
            key={`${repair.failedCellId}:${repair.repairCellId}`}
            className="rounded-lg border border-white/10 bg-black/20 px-2 py-2"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-violet-50/90">{repair.reason}</p>
              <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-violet-300/20 bg-violet-300/10 px-2 py-0.5 text-[11px] font-medium text-violet-100">
                <ShieldCheck className="h-3 w-3" />
                {repair.status}
              </span>
            </div>
            {repair.outcome ? (
              <p className="mt-1 text-xs leading-5 text-slate-300">{repair.outcome}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

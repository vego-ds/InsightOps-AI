"use client";

import { TriangleAlert } from "lucide-react";

import type { NotebookCellModel } from "@/types/notebook";

type NotebookErrorPanelProps = {
  cell: NotebookCellModel;
};

export function NotebookErrorPanel({ cell }: NotebookErrorPanelProps) {
  if (cell.status !== "failed") {
    return null;
  }

  return (
    <section className="rounded-lg border border-red-300/20 bg-red-500/10 px-3 py-2">
      <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-red-100">
        <TriangleAlert className="h-3.5 w-3.5" />
        traceback
      </div>
      <p className="mt-2 text-sm font-medium text-red-100">
        {cell.errorMessage ?? "Mock cell failure"}
      </p>
      {cell.traceback ? (
        <pre className="mt-2 overflow-auto whitespace-pre-wrap rounded-lg border border-red-300/10 bg-black/25 p-2 text-xs leading-5 text-red-50/90">
          {cell.traceback}
        </pre>
      ) : null}
    </section>
  );
}

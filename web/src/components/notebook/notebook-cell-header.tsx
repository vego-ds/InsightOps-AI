"use client";

import { ChevronDown, ChevronRight, CircleCheck, CircleX, Loader2 } from "lucide-react";

import type { NotebookCellModel } from "@/types/notebook";

type NotebookCellHeaderProps = {
  cell: NotebookCellModel;
  collapsed: boolean;
  onToggle: () => void;
};

export function NotebookCellHeader({
  cell,
  collapsed,
  onToggle,
}: NotebookCellHeaderProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex w-full items-center justify-between gap-3 rounded-t-xl border-b border-white/10 bg-white/[0.035] px-3 py-2 text-left transition hover:bg-white/[0.06]"
      aria-expanded={!collapsed}
    >
      <span className="flex min-w-0 items-center gap-2">
        {collapsed ? (
          <ChevronRight className="h-4 w-4 shrink-0 text-slate-500" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-slate-500" />
        )}
        <StatusIcon status={cell.status} />
        <span className="min-w-0">
          <span className="block truncate text-sm font-medium text-slate-100">
            {cell.title}
          </span>
          <span className="text-[11px] uppercase tracking-wide text-slate-500">
            {cell.language} cell · attempt {cell.attempt}
          </span>
        </span>
      </span>
      <span className="flex shrink-0 items-center gap-2">
        {typeof cell.durationMs === "number" ? (
          <span className="rounded-full border border-white/10 bg-black/20 px-2 py-0.5 text-[11px] text-slate-400">
            {cell.durationMs} ms
          </span>
        ) : null}
        <span
          className={[
            "rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize",
            cell.status === "completed"
              ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-100"
              : "",
            cell.status === "failed"
              ? "border-red-300/20 bg-red-500/10 text-red-100"
              : "",
            cell.status === "running"
              ? "border-amber-300/20 bg-amber-300/10 text-amber-100"
              : "",
          ].join(" ")}
        >
          {cell.status}
        </span>
      </span>
    </button>
  );
}

function StatusIcon({ status }: { status: NotebookCellModel["status"] }) {
  if (status === "completed") {
    return <CircleCheck className="h-4 w-4 shrink-0 text-emerald-200" />;
  }
  if (status === "failed") {
    return <CircleX className="h-4 w-4 shrink-0 text-red-200" />;
  }
  return <Loader2 className="h-4 w-4 shrink-0 animate-spin text-amber-100" />;
}

"use client";

import { Columns3, Database, KeyRound } from "lucide-react";

import { ColumnDetailCard } from "@/components/datasets/column-detail-card";
import { useDatasetStore } from "@/stores/dataset-store";
import type { DatasetColumn } from "@/types/dataset";

export function SchemaInspector() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
  const selectedColumnKey = useDatasetStore((store) => store.selectedColumnKey);
  const setSelectedColumnKey = useDatasetStore(
    (store) => store.setSelectedColumnKey,
  );

  if (!activeDataset) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Columns3 className="h-4 w-4 text-cyan-200" />
          Schema inspector
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Upload a dataset to inspect columns, data types, nullability, sample
          values, and recommended analysis actions.
        </p>
      </section>
    );
  }

  const selectedColumn =
    activeDataset.columns.find((column) => column.key === selectedColumnKey) ??
    activeDataset.columns[0] ??
    null;

  if (activeDataset.columns.length === 0) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Columns3 className="h-4 w-4 text-cyan-200" />
          No schema columns
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          The uploaded dataset did not expose any columns to inspect. Clear the
          dataset and upload a CSV with a header row.
        </p>
      </section>
    );
  }

  return (
    <section className="grid min-h-0 gap-4 lg:grid-cols-[minmax(280px,380px)_minmax(0,1fr)]">
      <div className="min-h-0 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
        <div className="border-b border-white/10 bg-white/[0.03] px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Database className="h-4 w-4 text-cyan-200" />
            Schema
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {activeDataset.columnCount} columns from {activeDataset.fileName}
          </p>
        </div>

        <div className="max-h-[620px] overflow-auto p-2">
          {activeDataset.columns.map((column) => (
            <ColumnListItem
              key={column.key}
              column={column}
              selected={column.key === selectedColumn?.key}
              onSelect={() => setSelectedColumnKey(column.key)}
            />
          ))}
        </div>
      </div>

      <ColumnDetailCard column={selectedColumn} />
    </section>
  );
}

function ColumnListItem({
  column,
  selected,
  onSelect,
}: {
  column: DatasetColumn;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={[
        "mb-2 flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition",
        selected
          ? "border-cyan-300/30 bg-cyan-300/10 shadow-sm shadow-cyan-950/30"
          : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-white/[0.04]",
      ].join(" ")}
      aria-pressed={selected}
    >
      <div
        className={[
          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
          selected
            ? "border-cyan-300/30 bg-cyan-300/10 text-cyan-100"
            : "border-white/10 bg-white/[0.04] text-slate-400",
        ].join(" ")}
      >
        <KeyRound className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center justify-between gap-3">
          <p className="truncate text-sm font-semibold text-slate-100">
            {column.label}
          </p>
          <span className="shrink-0 rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[11px] font-medium text-slate-400">
            {column.dataType}
          </span>
        </div>

        <p className="mt-1 truncate font-mono text-xs text-slate-500">
          {column.key}
        </p>

        <p
          className={[
            "mt-2 text-xs font-medium",
            column.nullable ? "text-amber-200" : "text-emerald-200",
          ].join(" ")}
        >
          {column.nullable ? "Nullable" : "Required"}
        </p>
      </div>
    </button>
  );
}

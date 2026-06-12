"use client";

import { Lightbulb, Sparkles } from "lucide-react";

import type { FilePreviewDataset } from "@/types/dataset";

type SuggestedPromptsProps = {
  dataset: FilePreviewDataset;
  onSelectPrompt: (prompt: string) => void;
};

export function SuggestedPrompts({
  dataset,
  onSelectPrompt,
}: SuggestedPromptsProps) {
  const prompts = buildSuggestedPrompts(dataset);

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
      <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500">
        <Lightbulb className="h-3.5 w-3.5 text-cyan-200" />
        Suggested prompts
      </div>

      <div className="flex flex-col gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            className="group flex items-start gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-left text-sm leading-5 text-slate-300 transition hover:border-cyan-300/25 hover:bg-cyan-300/10 hover:text-slate-100"
          >
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-200 transition group-hover:text-cyan-100" />
            {prompt}
          </button>
        ))}
      </div>
    </section>
  );
}

function buildSuggestedPrompts(dataset: FilePreviewDataset): string[] {
  const numericColumn = dataset.columns.find(
    (column) => column.dataType === "number" || column.dataType === "integer",
  );
  const dateColumn = dataset.columns.find(
    (column) => column.dataType === "date" || column.dataType === "datetime",
  );
  const categoricalColumn = dataset.columns.find(
    (column) => column.dataType === "categorical" || column.dataType === "string",
  );
  const nullableColumn = dataset.columns.find((column) => column.nullable);

  return [
    `Summarize the dataset ${dataset.fileName} in plain English.`,
    numericColumn
      ? `What should I inspect about the numeric column "${numericColumn.label}"?`
      : "Which columns look useful for KPI analysis?",
    dateColumn
      ? `How can I analyze trends using "${dateColumn.label}"?`
      : "Does this dataset contain any time-based analysis opportunities?",
    categoricalColumn
      ? `What grouping analysis should I run for "${categoricalColumn.label}"?`
      : "Which fields could segment this dataset?",
    nullableColumn
      ? `Are missing values in "${nullableColumn.label}" a data quality risk?`
      : "What data quality checks should I run first?",
  ];
}

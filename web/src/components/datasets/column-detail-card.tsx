"use client";

import {
  Binary,
  CalendarClock,
  CheckCircle2,
  Hash,
  ListChecks,
  Tags,
  TextCursorInput,
} from "lucide-react";

import type { DatasetColumn, DatasetColumnType } from "@/types/dataset";

type ColumnDetailCardProps = {
  column: DatasetColumn | null;
};

export function ColumnDetailCard({ column }: ColumnDetailCardProps) {
  if (!column) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
        <p className="text-sm font-medium text-white">No column selected</p>
        <p className="mt-2 text-sm text-slate-400">
          Select a column to inspect data type, nullability, sample values, and
          recommended analysis actions.
        </p>
      </section>
    );
  }

  const actions = recommendedActions(column.dataType);

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Selected column
          </p>
          <h3 className="mt-1 truncate text-lg font-semibold text-white">
            {column.label}
          </h3>
          <p className="mt-1 font-mono text-xs text-slate-500">{column.key}</p>
        </div>

        <DataTypeBadge dataType={column.dataType} />
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <Metric label="Data type" value={column.dataType} />
        <Metric label="Nullable" value={column.nullable ? "Yes" : "No"} />
      </dl>

      <div className="mt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Sample values
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {column.sampleValues.length > 0 ? (
            column.sampleValues.map((value, index) => (
              <span
                key={`${column.key}-sample-${index}`}
                className="max-w-full truncate rounded-lg border border-white/10 bg-black/20 px-2.5 py-1 font-mono text-xs text-slate-300"
              >
                {formatSampleValue(value)}
              </span>
            ))
          ) : (
            <span className="rounded-lg border border-white/10 bg-black/20 px-2.5 py-1 text-xs text-slate-500">
              No non-null samples
            </span>
          )}
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Recommended analysis actions
        </p>
        <ul className="mt-2 space-y-2">
          {actions.map((action) => (
            <li
              key={action}
              className="flex items-start gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm leading-5 text-slate-300"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
              {action}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-3">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold text-slate-100">{value}</dd>
    </div>
  );
}

function DataTypeBadge({ dataType }: { dataType: DatasetColumnType }) {
  return (
    <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-medium text-cyan-100">
      <DataTypeIcon dataType={dataType} />
      {dataType}
    </span>
  );
}

function DataTypeIcon({ dataType }: { dataType: DatasetColumnType }) {
  if (dataType === "integer" || dataType === "number") {
    return <Hash className="h-3.5 w-3.5" />;
  }
  if (dataType === "boolean") {
    return <Binary className="h-3.5 w-3.5" />;
  }
  if (dataType === "date" || dataType === "datetime") {
    return <CalendarClock className="h-3.5 w-3.5" />;
  }
  if (dataType === "categorical") {
    return <Tags className="h-3.5 w-3.5" />;
  }
  if (dataType === "unknown") {
    return <ListChecks className="h-3.5 w-3.5" />;
  }
  return <TextCursorInput className="h-3.5 w-3.5" />;
}

function recommendedActions(dataType: DatasetColumnType): string[] {
  if (dataType === "integer" || dataType === "number") {
    return [
      "Calculate distribution, outliers, minimum, maximum, and average.",
      "Compare aggregates by category, region, or time period.",
      "Use as a metric candidate for charts, correlations, and anomaly checks.",
    ];
  }
  if (dataType === "date" || dataType === "datetime") {
    return [
      "Build time-series trends and period-over-period comparisons.",
      "Check gaps, duplicate timestamps, and irregular reporting cadence.",
      "Use as the timeline axis for forecasts and seasonality checks.",
    ];
  }
  if (dataType === "boolean") {
    return [
      "Measure true and false rates across the dataset.",
      "Segment outcomes by this flag to compare behavior.",
      "Check whether missing values should be treated as a separate state.",
    ];
  }
  if (dataType === "categorical" || dataType === "string") {
    return [
      "Profile top values, rare values, and cardinality.",
      "Group metrics by this field for ranking and contribution analysis.",
      "Check inconsistent labels, casing, whitespace, and missing categories.",
    ];
  }
  return [
    "Review source values before using this column in analysis.",
    "Confirm whether the field should be parsed as numeric, date, or category.",
    "Exclude from automated metrics until the type is clarified.",
  ];
}

function formatSampleValue(value: string | number | boolean | null): string {
  if (value === null) {
    return "NULL";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

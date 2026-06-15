"use client";

import type { TableArtifact } from "@/types/artifact";

export function TableArtifactView({ artifact }: { artifact: TableArtifact }) {
  if (artifact.columns.length === 0 || artifact.rows.length === 0) {
    return (
      <div className="rounded-2xl border border-white/10 bg-black/20 p-6 text-sm text-slate-400">
        This table artifact does not contain renderable rows.
      </div>
    );
  }

  return (
    <div className="min-w-0 overflow-hidden rounded-2xl border border-white/10 bg-black/20">
      <div className="max-h-[min(560px,56dvh)] overflow-auto overscroll-contain">
        <table className="min-w-max border-separate border-spacing-0 text-left text-sm">
          <thead className="sticky top-0 z-10 bg-[#10131F]">
            <tr>
              {artifact.columns.map((column) => (
                <th
                  key={column.key}
                  className="max-w-64 whitespace-nowrap border-b border-white/10 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-300"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {artifact.rows.map((row, index) => (
              <tr key={`${artifact.id}-row-${index}`}>
                {artifact.columns.map((column) => (
                  <td
                    key={`${index}-${column.key}`}
                    className="max-w-72 border-b border-white/10 px-4 py-3 text-slate-300"
                  >
                    <span className="block truncate" title={formatScalar(row[column.key])}>
                      {formatScalar(row[column.key])}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatScalar(value: string | number | boolean | null): string {
  if (value === null) {
    return "NULL";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

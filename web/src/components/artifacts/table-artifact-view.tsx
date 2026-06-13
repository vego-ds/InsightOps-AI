"use client";

import type { TableArtifact } from "@/types/artifact";

export function TableArtifactView({ artifact }: { artifact: TableArtifact }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
      <div className="max-h-[520px] overflow-auto">
        <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
          <thead className="sticky top-0 bg-[#10131F]">
            <tr>
              {artifact.columns.map((column) => (
                <th
                  key={column.key}
                  className="whitespace-nowrap border-b border-white/10 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-300"
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
                    className="border-b border-white/10 px-4 py-3 text-slate-300"
                  >
                    {formatScalar(row[column.key])}
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

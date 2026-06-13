"use client";

import { TerminalSquare } from "lucide-react";

type NotebookOutputPanelProps = {
  title: "stdout" | "stderr";
  lines: string[];
};

export function NotebookOutputPanel({ title, lines }: NotebookOutputPanelProps) {
  if (lines.length === 0) {
    return null;
  }

  const isStderr = title === "stderr";

  return (
    <section
      className={[
        "rounded-lg border px-3 py-2",
        isStderr
          ? "border-amber-300/20 bg-amber-300/10"
          : "border-cyan-300/15 bg-cyan-300/10",
      ].join(" ")}
    >
      <div
        className={[
          "flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide",
          isStderr ? "text-amber-100" : "text-cyan-100",
        ].join(" ")}
      >
        <TerminalSquare className="h-3.5 w-3.5" />
        {title}
      </div>
      <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-200">
        {lines.join("\n")}
      </pre>
    </section>
  );
}

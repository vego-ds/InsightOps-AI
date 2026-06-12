"use client";

import { useState } from "react";

import { NotebookCellHeader } from "@/components/notebook/notebook-cell-header";
import { NotebookCodeBlock } from "@/components/notebook/notebook-code-block";
import { NotebookErrorPanel } from "@/components/notebook/notebook-error-panel";
import { NotebookOutputPanel } from "@/components/notebook/notebook-output-panel";
import { NotebookRepairPanel } from "@/components/notebook/notebook-repair-panel";
import type { NotebookCellModel, NotebookRepairState } from "@/types/notebook";

type NotebookCellProps = {
  cell: NotebookCellModel;
  repairs: NotebookRepairState[];
};

export function NotebookCell({ cell, repairs }: NotebookCellProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <article className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.035]">
      <NotebookCellHeader
        cell={cell}
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
      />

      {!collapsed ? (
        <>
          <NotebookCodeBlock code={cell.code} language={cell.language} />
          <div className="space-y-2 p-3">
            <NotebookOutputPanel title="stdout" lines={cell.stdout} />
            <NotebookOutputPanel title="stderr" lines={cell.stderr} />
            <NotebookErrorPanel cell={cell} />
            <NotebookRepairPanel repairs={repairs} />
          </div>
        </>
      ) : null}
    </article>
  );
}

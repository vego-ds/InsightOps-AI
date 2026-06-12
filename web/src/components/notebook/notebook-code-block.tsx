"use client";

import { Code2 } from "lucide-react";

import { CopyCodeButton } from "@/components/notebook/copy-code-button";

type NotebookCodeBlockProps = {
  code: string;
  language: string;
};

export function NotebookCodeBlock({ code, language }: NotebookCodeBlockProps) {
  return (
    <section className="border-b border-white/10 bg-black/20">
      <div className="flex items-center justify-between gap-3 px-3 py-2">
        <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">
          <Code2 className="h-3.5 w-3.5" />
          {language}
        </div>
        <CopyCodeButton code={code} />
      </div>
      <pre className="max-h-80 overflow-auto px-3 pb-3 text-xs leading-5 text-slate-200">
        <code>{code}</code>
      </pre>
    </section>
  );
}

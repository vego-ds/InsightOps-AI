"use client";

import type { MarkdownArtifact } from "@/types/artifact";

export function MarkdownArtifactView({ artifact }: { artifact: MarkdownArtifact }) {
  return (
    <pre className="whitespace-pre-wrap rounded-2xl border border-white/10 bg-black/20 p-4 text-sm leading-6 text-slate-300">
      {artifact.text}
    </pre>
  );
}

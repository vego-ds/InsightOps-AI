"use client";

import { Bot, Loader2, MessageSquareText, TriangleAlert, UserRound } from "lucide-react";

import type { ChatMessage } from "@/types/chat";

type ChatMessageListProps = {
  messages: ChatMessage[];
  hasDataset: boolean;
};

export function ChatMessageList({ messages, hasDataset }: ChatMessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-black/20 px-5 py-8 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05] text-cyan-100">
          <MessageSquareText className="h-5 w-5" />
        </div>
        <h3 className="mt-4 text-sm font-semibold text-white">
          {hasDataset ? "Ask about this dataset" : "Upload a dataset to begin"}
        </h3>
        <p className="mt-2 max-w-xs text-sm leading-6 text-slate-400">
          {hasDataset
            ? "Choose a suggested prompt or ask a focused question about columns, schema, or analysis direction."
            : "Chat activates after a CSV is uploaded and stored in the workspace state."}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto pr-1">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <article
      className={[
        "flex gap-3 rounded-2xl border px-3 py-3",
        isUser
          ? "border-cyan-300/20 bg-cyan-300/10"
          : "border-white/10 bg-white/[0.04]",
      ].join(" ")}
    >
      <div
        className={[
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border",
          isUser
            ? "border-cyan-300/25 bg-cyan-300/10 text-cyan-100"
            : "border-white/10 bg-black/20 text-slate-300",
        ].join(" ")}
      >
        {isUser ? <UserRound className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {isUser ? "You" : "InsightOps"}
          </p>
          {message.status === "loading" ? (
            <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-0.5 text-[11px] font-medium text-amber-100">
              Loading
            </span>
          ) : null}
          {message.status === "error" ? (
            <span className="rounded-full border border-red-300/20 bg-red-500/10 px-2 py-0.5 text-[11px] font-medium text-red-100">
              Error
            </span>
          ) : null}
        </div>
        <div className="mt-1 flex items-start gap-2">
          {message.status === "loading" ? (
            <Loader2 className="mt-1 h-3.5 w-3.5 shrink-0 animate-spin text-amber-100" />
          ) : null}
          {message.status === "error" ? (
            <TriangleAlert className="mt-1 h-3.5 w-3.5 shrink-0 text-red-200" />
          ) : null}
          <p className="whitespace-pre-wrap text-sm leading-6 text-slate-200">
            {message.content}
          </p>
        </div>
      </div>
    </article>
  );
}

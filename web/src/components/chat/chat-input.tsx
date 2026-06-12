"use client";

import { useState } from "react";
import { SendHorizontal } from "lucide-react";

type ChatInputProps = {
  disabled: boolean;
  onSend: (message: string) => void;
};

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [draft, setDraft] = useState("");

  const submit = () => {
    const trimmed = draft.trim();
    if (!trimmed || disabled) {
      return;
    }

    onSend(trimmed);
    setDraft("");
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-2">
      <label className="sr-only" htmlFor="chat-input">
        Ask a dataset question
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="chat-input"
          value={draft}
          disabled={disabled}
          rows={2}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder={
            disabled
              ? "Upload a dataset to enable chat"
              : "Ask about schema, columns, quality, or analysis ideas..."
          }
          className="min-h-11 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-5 text-slate-100 outline-none placeholder:text-slate-600 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          disabled={disabled || draft.trim().length === 0}
          onClick={submit}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-300/15 text-cyan-100 transition hover:bg-cyan-300/25 disabled:cursor-not-allowed disabled:bg-white/[0.04] disabled:text-slate-600"
          aria-label="Send message"
        >
          <SendHorizontal className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

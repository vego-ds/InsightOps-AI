"use client";

import { Bot, MessageSquareText, Trash2 } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { SuggestedPrompts } from "@/components/chat/suggested-prompts";
import { useAnalysisStream } from "../../lib/use-analysis-stream";
import { useChatStore } from "@/stores/chat-store";
import { useDatasetStore } from "@/stores/dataset-store";

export function ChatPanel() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
  const messages = useChatStore((store) => store.messages);
  const clearMessages = useChatStore((store) => store.clearMessages);
  const { canRetry, currentRunId, isStreaming, lastError, retryLastMessage, sendMessage } =
    useAnalysisStream();
  const hasDataset = Boolean(activeDataset);

  return (
    <div className="flex h-full min-h-[248px] flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <header className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
            <MessageSquareText className="h-4 w-4 text-cyan-200" />
            Analyst chat
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {activeDataset
              ? `Dataset context: ${activeDataset.fileName}`
              : "Upload a dataset to enable questions."}
          </p>
        </div>

        {messages.length > 0 ? (
          <button
            type="button"
            onClick={clearMessages}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-black/20 text-slate-500 transition hover:border-red-300/30 hover:bg-red-500/10 hover:text-red-200"
            aria-label="Clear chat messages"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        ) : null}
      </header>

      <div className="mt-4 flex min-h-0 flex-1 flex-col gap-3">
        {!activeDataset ? <ChatLockedState /> : null}

        {activeDataset && isStreaming ? (
          <StreamingState runId={currentRunId} />
        ) : null}

        {activeDataset && lastError ? (
          <StreamErrorState
            canRetry={canRetry}
            message={lastError}
            onRetry={retryLastMessage}
          />
        ) : null}

        {activeDataset && messages.length === 0 ? (
          <SuggestedPrompts dataset={activeDataset} onSelectPrompt={sendMessage} />
        ) : null}

        <ChatMessageList messages={messages} hasDataset={hasDataset} />
      </div>

      <div className="mt-4">
        <ChatInput disabled={!activeDataset || isStreaming} onSend={sendMessage} />
      </div>
    </div>
  );
}

function ChatLockedState() {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] text-cyan-100">
        <Bot className="h-5 w-5" />
      </div>
      <p className="mt-3 text-sm font-medium text-white">
        Chat is waiting for a dataset
      </p>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Upload a CSV in the data canvas. Once preview data is stored globally,
        the chat input and prompt suggestions will unlock.
      </p>
    </div>
  );
}

function StreamingState({ runId }: { runId: string | null }) {
  return (
    <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/10 px-3 py-2 text-xs text-cyan-100">
      {runId ? `Streaming analysis run ${runId.slice(0, 8)}...` : "Starting analysis stream..."}
    </div>
  );
}

function StreamErrorState({
  canRetry,
  message,
  onRetry,
}: {
  canRetry: boolean;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-2xl border border-red-300/20 bg-red-500/10 px-3 py-3">
      <p className="text-sm font-medium text-red-100">Stream interrupted</p>
      <p className="mt-1 text-sm leading-5 text-red-200/80">{message}</p>
      {canRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-lg border border-red-200/20 bg-red-200/10 px-3 py-1.5 text-xs font-medium text-red-100 transition hover:bg-red-200/15"
        >
          Retry last prompt
        </button>
      ) : null}
    </div>
  );
}

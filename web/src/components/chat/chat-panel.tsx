"use client";

import { Bot, MessageSquareText, Trash2 } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { SuggestedPrompts } from "@/components/chat/suggested-prompts";
import { requestAnalysis } from "@/lib/analysis-client";
import { useChatStore } from "@/stores/chat-store";
import { useDatasetStore } from "@/stores/dataset-store";
import { buildAnalysisRequestBody } from "@/types/analysis";

const ANALYSIS_FAILURE_MESSAGE =
  "Analysis request failed safely. The backend response could not be accepted by the frontend contract.";

export function ChatPanel() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
  const messages = useChatStore((store) => store.messages);
  const addUserMessage = useChatStore((store) => store.addUserMessage);
  const addPendingAssistantMessage = useChatStore(
    (store) => store.addPendingAssistantMessage,
  );
  const resolveAssistantMessage = useChatStore(
    (store) => store.resolveAssistantMessage,
  );
  const failAssistantMessage = useChatStore(
    (store) => store.failAssistantMessage,
  );
  const clearMessages = useChatStore((store) => store.clearMessages);
  const hasDataset = Boolean(activeDataset);

  const sendMessage = async (content: string) => {
    if (!activeDataset) {
      return;
    }

    addUserMessage(content);
    const pendingMessage = addPendingAssistantMessage();

    try {
      const response = await requestAnalysis(
        buildAnalysisRequestBody(activeDataset, content),
      );
      resolveAssistantMessage(pendingMessage.id, response.assistantMessage);
    } catch {
      failAssistantMessage(pendingMessage.id, ANALYSIS_FAILURE_MESSAGE);
    }
  };

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

        {activeDataset && messages.length === 0 ? (
          <SuggestedPrompts dataset={activeDataset} onSelectPrompt={sendMessage} />
        ) : null}

        <ChatMessageList messages={messages} hasDataset={hasDataset} />
      </div>

      <div className="mt-4">
        <ChatInput disabled={!activeDataset} onSend={sendMessage} />
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

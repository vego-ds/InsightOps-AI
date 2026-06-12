"use client";

import { Bot, MessageSquareText, Trash2 } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { SuggestedPrompts } from "@/components/chat/suggested-prompts";
import { createAnalysisRun, parseRunEvent } from "@/lib/execution-client";
import { useArtifactStore } from "@/stores/artifact-store";
import { useChatStore } from "@/stores/chat-store";
import { useDatasetStore } from "@/stores/dataset-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useNotebookStore } from "@/stores/notebook-store";
import {
  buildAnalysisRunCreateRequest,
  type AnalysisRunEvent,
} from "@/types/execution";

const ANALYSIS_FAILURE_MESSAGE =
  "Streaming analysis failed safely. The backend event stream could not be accepted by the frontend contract.";

export function ChatPanel() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
  const messages = useChatStore((store) => store.messages);
  const addUserMessage = useChatStore((store) => store.addUserMessage);
  const addPendingAssistantMessage = useChatStore(
    (store) => store.addPendingAssistantMessage,
  );
  const attachRunToAssistantMessage = useChatStore(
    (store) => store.attachRunToAssistantMessage,
  );
  const resolveAssistantMessage = useChatStore(
    (store) => store.resolveAssistantMessage,
  );
  const failAssistantMessage = useChatStore(
    (store) => store.failAssistantMessage,
  );
  const clearMessages = useChatStore((store) => store.clearMessages);
  const appendRunEvent = useExecutionStore((store) => store.appendRunEvent);
  const appendNotebookEvent = useNotebookStore(
    (store) => store.appendNotebookEvent,
  );
  const addArtifact = useArtifactStore((store) => store.addArtifact);
  const hasDataset = Boolean(activeDataset);

  const sendMessage = async (content: string) => {
    if (!activeDataset) {
      return;
    }

    addUserMessage(content);
    const pendingMessage = addPendingAssistantMessage();

    try {
      const run = await createAnalysisRun(
        buildAnalysisRunCreateRequest(activeDataset, content),
      );
      attachRunToAssistantMessage(pendingMessage.id, run.runId);

      const eventSource = new EventSource(run.streamUrl);
      const closeWithFailure = () => {
        eventSource.close();
        failAssistantMessage(pendingMessage.id, ANALYSIS_FAILURE_MESSAGE);
      };
      const handleRawEvent = (event: MessageEvent<string>) => {
        let payload: unknown;
        try {
          payload = JSON.parse(event.data);
        } catch {
          closeWithFailure();
          return;
        }

        const parsed = parseRunEvent(payload);
        if (!parsed || parsed.runId !== run.runId) {
          closeWithFailure();
          return;
        }

        appendRunEvent(parsed);

        if (isNotebookRunEvent(parsed)) {
          appendNotebookEvent(parsed);
        }

        if (parsed.type === "artifact") {
          addArtifact(parsed.artifact);
        }

        if (parsed.type === "run.error") {
          eventSource.close();
          failAssistantMessage(pendingMessage.id, parsed.errorMessage);
          return;
        }

        if (parsed.type === "run.final") {
          eventSource.close();
          resolveAssistantMessage(pendingMessage.id, parsed.assistantMessage);
        }
      };

      eventSource.addEventListener("run.status", handleRawEvent);
      eventSource.addEventListener("run.code", handleRawEvent);
      eventSource.addEventListener("run.stdout", handleRawEvent);
      eventSource.addEventListener("run.error", handleRawEvent);
      eventSource.addEventListener("run.cell.started", handleRawEvent);
      eventSource.addEventListener("run.cell.stdout", handleRawEvent);
      eventSource.addEventListener("run.cell.stderr", handleRawEvent);
      eventSource.addEventListener("run.cell.completed", handleRawEvent);
      eventSource.addEventListener("run.cell.failed", handleRawEvent);
      eventSource.addEventListener("run.repair.started", handleRawEvent);
      eventSource.addEventListener("run.repair.completed", handleRawEvent);
      eventSource.addEventListener("run.artifact", handleRawEvent);
      eventSource.addEventListener("run.final", handleRawEvent);
      eventSource.onerror = closeWithFailure;
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

function isNotebookRunEvent(
  event: AnalysisRunEvent,
): event is Extract<
  AnalysisRunEvent,
  {
    type:
      | "run.cell.started"
      | "run.cell.stdout"
      | "run.cell.stderr"
      | "run.cell.completed"
      | "run.cell.failed"
      | "run.repair.started"
      | "run.repair.completed";
  }
> {
  return event.type.startsWith("run.cell.") || event.type.startsWith("run.repair.");
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

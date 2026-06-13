"use client";

import { Bot, MessageSquareText, Trash2 } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { SuggestedPrompts } from "@/components/chat/suggested-prompts";
import { createAnalysisRun, parseRunEvent } from "@/lib/execution-client";
import { useArtifactStore } from "@/stores/artifact-store";
import { useCanvasStore } from "@/stores/canvas-store";
import { useChatStore } from "@/stores/chat-store";
import { useDatasetStore } from "@/stores/dataset-store";
import { useExecutionStore } from "@/stores/execution-store";
import { useNotebookStore } from "@/stores/notebook-store";
import { useRunHistoryStore } from "@/stores/run-history-store";
import {
  buildAnalysisRunCreateRequest,
  type AnalysisRunEvent,
} from "@/types/execution";

const ANALYSIS_FAILURE_MESSAGE =
  "Streaming analysis failed safely. The backend event stream could not be accepted by the frontend contract.";
const ANALYSIS_CONNECTION_FAILURE_MESSAGE =
  "Analysis could not start. Check that the backend is running, then try again.";
const ARTIFACT_VALIDATION_FAILURE_MESSAGE =
  "An artifact event was blocked because it did not match the expected safe rendering contract.";

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
  const setActiveRunId = useArtifactStore((store) => store.setActiveRunId);
  const selectBestArtifactForRun = useArtifactStore(
    (store) => store.selectBestArtifactForRun,
  );
  const resetRunFocusLock = useCanvasStore((store) => store.resetRunFocusLock);
  const setActiveMode = useCanvasStore((store) => store.setActiveMode);
  const addRun = useRunHistoryStore((store) => store.addRun);
  const markRunComplete = useRunHistoryStore((store) => store.markRunComplete);
  const markRunError = useRunHistoryStore((store) => store.markRunError);
  const attachArtifactToRun = useRunHistoryStore(
    (store) => store.attachArtifactToRun,
  );
  const setSelectedArtifactForRun = useRunHistoryStore(
    (store) => store.setSelectedArtifactForRun,
  );
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
      addRun({
        runId: run.runId,
        datasetId: activeDataset.id,
        prompt: content,
      });
      attachRunToAssistantMessage(pendingMessage.id, run.runId);
      setActiveRunId(run.runId);
      resetRunFocusLock(run.runId);

      const eventSource = new EventSource(run.streamUrl);
      const closeWithFailure = (message = ANALYSIS_FAILURE_MESSAGE) => {
        eventSource.close();
        markRunError(run.runId, message);
        failAssistantMessage(pendingMessage.id, message);
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
          closeWithFailure(
            isArtifactPayload(payload)
              ? ARTIFACT_VALIDATION_FAILURE_MESSAGE
              : ANALYSIS_FAILURE_MESSAGE,
          );
          return;
        }

        appendRunEvent(parsed);

        if (isNotebookRunEvent(parsed)) {
          appendNotebookEvent(parsed);
        }

        if (parsed.type === "artifact") {
          const storedArtifact = addArtifact(parsed.artifact, run.runId);
          attachArtifactToRun(run.runId, storedArtifact.id);
          const artifactState = useArtifactStore.getState();
          const canvasState = useCanvasStore.getState();
          if (
            artifactState.activeRunId === run.runId &&
            canvasState.userLockedModeForRunId !== run.runId
          ) {
            setActiveMode("artifacts", "system", run.runId);
            const bestArtifact = selectBestArtifactForRun(run.runId, "system");
            setSelectedArtifactForRun(run.runId, bestArtifact?.id ?? null);
          }
        }

        if (parsed.type === "run.error") {
          eventSource.close();
          markRunError(run.runId, parsed.errorMessage);
          failAssistantMessage(pendingMessage.id, parsed.errorMessage);
          return;
        }

        if (parsed.type === "run.final") {
          eventSource.close();
          markRunComplete(run.runId, parsed.assistantMessage);
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
      eventSource.onerror = () => closeWithFailure(ANALYSIS_CONNECTION_FAILURE_MESSAGE);
    } catch {
      failAssistantMessage(pendingMessage.id, ANALYSIS_CONNECTION_FAILURE_MESSAGE);
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

function isArtifactPayload(payload: unknown): boolean {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "type" in payload &&
    (payload as { type?: unknown }).type === "artifact"
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

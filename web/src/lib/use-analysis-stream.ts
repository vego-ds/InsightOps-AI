"use client";

import * as React from "react";

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

const STREAM_CONTRACT_FAILURE_MESSAGE =
  "Streaming analysis stopped because the event stream did not match the expected contract.";
const STREAM_CONNECTION_FAILURE_MESSAGE =
  "Analysis could not start. Confirm the backend is running, then try again.";
const ARTIFACT_CONTRACT_FAILURE_MESSAGE =
  "An artifact event was blocked because it did not match the safe rendering contract.";
const STREAM_BUSY_MESSAGE =
  "An analysis is already running. Wait for the current stream to finish before sending another prompt.";

const RUN_EVENT_NAMES = [
  "run.status",
  "run.code",
  "run.stdout",
  "run.error",
  "run.cell.started",
  "run.cell.stdout",
  "run.cell.stderr",
  "run.cell.completed",
  "run.cell.failed",
  "run.repair.started",
  "run.repair.completed",
  "run.artifact",
  "run.final",
] as const;

type StreamState = {
  isStreaming: boolean;
  currentRunId: string | null;
  lastError: string | null;
  canRetry: boolean;
};

type ActiveStream = {
  runId: string;
  pendingMessageId: string;
  eventSource: EventSource;
  removeListeners: () => void;
};

export function useAnalysisStream() {
  const activeDataset = useDatasetStore((store) => store.activeDataset);
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

  const activeStreamRef = React.useRef<ActiveStream | null>(null);
  const lastPromptRef = React.useRef<string | null>(null);
  const [state, setState] = React.useState<StreamState>({
    isStreaming: false,
    currentRunId: null,
    lastError: null,
    canRetry: false,
  });

  const closeActiveStream = React.useCallback(() => {
    const activeStream = activeStreamRef.current;
    if (!activeStream) {
      return;
    }

    activeStream.removeListeners();
    activeStream.eventSource.close();
    activeStreamRef.current = null;
  }, []);

  const finishStream = React.useCallback(
    (runId: string) => {
      if (activeStreamRef.current?.runId !== runId) {
        return;
      }

      closeActiveStream();
      setState((current) => ({
        ...current,
        isStreaming: false,
        currentRunId: null,
      }));
    },
    [closeActiveStream],
  );

  const failStream = React.useCallback(
    (runId: string, pendingMessageId: string, message: string) => {
      if (activeStreamRef.current?.runId === runId) {
        closeActiveStream();
      }

      markRunError(runId, message);
      failAssistantMessage(pendingMessageId, message);
      setState({
        isStreaming: false,
        currentRunId: null,
        lastError: message,
        canRetry: Boolean(lastPromptRef.current),
      });
    },
    [closeActiveStream, failAssistantMessage, markRunError],
  );

  const handleArtifactEvent = React.useCallback(
    (event: Extract<AnalysisRunEvent, { type: "artifact" }>) => {
      const storedArtifact = addArtifact(event.artifact, event.runId);
      attachArtifactToRun(event.runId, storedArtifact.id);

      const artifactState = useArtifactStore.getState();
      const canvasState = useCanvasStore.getState();

      if (
        artifactState.activeRunId === event.runId &&
        canvasState.userLockedModeForRunId !== event.runId
      ) {
        setActiveMode("artifacts", "system", event.runId);
        const bestArtifact = selectBestArtifactForRun(event.runId, "system");
        setSelectedArtifactForRun(event.runId, bestArtifact?.id ?? null);
      }
    },
    [
      addArtifact,
      attachArtifactToRun,
      selectBestArtifactForRun,
      setActiveMode,
      setSelectedArtifactForRun,
    ],
  );

  const handleRunEvent = React.useCallback(
    (
      event: AnalysisRunEvent,
      runId: string,
      pendingMessageId: string,
    ) => {
      appendRunEvent(event);

      if (isNotebookRunEvent(event)) {
        appendNotebookEvent(event);
      }

      if (event.type === "artifact") {
        handleArtifactEvent(event);
        return;
      }

      if (event.type === "run.error") {
        failStream(runId, pendingMessageId, event.errorMessage);
        return;
      }

      if (event.type === "run.final") {
        markRunComplete(runId, event.assistantMessage);
        resolveAssistantMessage(pendingMessageId, event.assistantMessage);
        setState({
          isStreaming: false,
          currentRunId: null,
          lastError: null,
          canRetry: Boolean(lastPromptRef.current),
        });
        finishStream(runId);
      }
    },
    [
      appendNotebookEvent,
      appendRunEvent,
      failStream,
      finishStream,
      handleArtifactEvent,
      markRunComplete,
      resolveAssistantMessage,
    ],
  );

  const attachStreamListeners = React.useCallback(
    (
      eventSource: EventSource,
      runId: string,
      pendingMessageId: string,
    ): (() => void) => {
      const handleRawEvent = (event: Event) => {
        const payload = parseMessagePayload(event);
        if (!payload.ok) {
          failStream(runId, pendingMessageId, STREAM_CONTRACT_FAILURE_MESSAGE);
          return;
        }

        const parsed = parseRunEvent(payload.value);
        if (!parsed || parsed.runId !== runId) {
          failStream(
            runId,
            pendingMessageId,
            isArtifactPayload(payload.value)
              ? ARTIFACT_CONTRACT_FAILURE_MESSAGE
              : STREAM_CONTRACT_FAILURE_MESSAGE,
          );
          return;
        }

        handleRunEvent(parsed, runId, pendingMessageId);
      };

      for (const eventName of RUN_EVENT_NAMES) {
        eventSource.addEventListener(eventName, handleRawEvent);
      }

      eventSource.onerror = () => {
        failStream(runId, pendingMessageId, STREAM_CONNECTION_FAILURE_MESSAGE);
      };

      return () => {
        for (const eventName of RUN_EVENT_NAMES) {
          eventSource.removeEventListener(eventName, handleRawEvent);
        }
        eventSource.onerror = null;
      };
    },
    [failStream, handleRunEvent],
  );

  const sendMessage = React.useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || !activeDataset) {
        return;
      }

      if (activeStreamRef.current) {
        setState((current) => ({
          ...current,
          lastError: STREAM_BUSY_MESSAGE,
          canRetry: Boolean(lastPromptRef.current),
        }));
        return;
      }

      lastPromptRef.current = trimmed;
      setState({
        isStreaming: true,
        currentRunId: null,
        lastError: null,
        canRetry: false,
      });

      addUserMessage(trimmed);
      const pendingMessage = addPendingAssistantMessage();
      let createdRunId: string | null = null;

      try {
        const run = await createAnalysisRun(
          buildAnalysisRunCreateRequest(activeDataset, trimmed),
        );
        createdRunId = run.runId;
        addRun({
          runId: run.runId,
          datasetId: activeDataset.id,
          prompt: trimmed,
        });
        attachRunToAssistantMessage(pendingMessage.id, run.runId);
        setActiveRunId(run.runId);
        resetRunFocusLock(run.runId);
        setState({
          isStreaming: true,
          currentRunId: run.runId,
          lastError: null,
          canRetry: false,
        });

        const eventSource = new EventSource(run.streamUrl);
        const removeListeners = attachStreamListeners(
          eventSource,
          run.runId,
          pendingMessage.id,
        );
        activeStreamRef.current = {
          runId: run.runId,
          pendingMessageId: pendingMessage.id,
          eventSource,
          removeListeners,
        };
      } catch {
        if (createdRunId) {
          markRunError(createdRunId, STREAM_CONNECTION_FAILURE_MESSAGE);
        }
        failAssistantMessage(
          pendingMessage.id,
          STREAM_CONNECTION_FAILURE_MESSAGE,
        );
        setState({
          isStreaming: false,
          currentRunId: null,
          lastError: STREAM_CONNECTION_FAILURE_MESSAGE,
          canRetry: Boolean(lastPromptRef.current),
        });
      }
    },
    [
      activeDataset,
      addPendingAssistantMessage,
      addRun,
      addUserMessage,
      attachRunToAssistantMessage,
      attachStreamListeners,
      failAssistantMessage,
      markRunError,
      resetRunFocusLock,
      setActiveRunId,
    ],
  );

  const retryLastMessage = React.useCallback(() => {
    const lastPrompt = lastPromptRef.current;
    if (!lastPrompt || activeStreamRef.current) {
      return;
    }

    void sendMessage(lastPrompt);
  }, [sendMessage]);

  React.useEffect(() => {
    return () => {
      closeActiveStream();
    };
  }, [closeActiveStream]);

  return {
    sendMessage,
    retryLastMessage,
    isStreaming: state.isStreaming,
    currentRunId: state.currentRunId,
    lastError: state.lastError,
    canRetry: state.canRetry && !state.isStreaming,
  };
}

function parseMessagePayload(
  event: Event,
): { ok: true; value: unknown } | { ok: false } {
  const data = (event as MessageEvent<string>).data;
  if (typeof data !== "string") {
    return { ok: false };
  }

  try {
    return { ok: true, value: JSON.parse(data) };
  } catch {
    return { ok: false };
  }
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

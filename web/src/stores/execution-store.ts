"use client";

import { create } from "zustand";

import type { AnalysisRunEvent } from "@/types/execution";

const EMPTY_RUN_EVENTS: AnalysisRunEvent[] = [];

type ExecutionStoreState = {
  eventsByRunId: Record<string, AnalysisRunEvent[]>;
  appendRunEvent: (event: AnalysisRunEvent) => void;
  clearRunEvents: (runId: string) => void;
  clearAllRunEvents: () => void;
};

export const useExecutionStore = create<ExecutionStoreState>((set) => ({
  eventsByRunId: {},

  appendRunEvent: (event) =>
    set((state) => {
      const existing = state.eventsByRunId[event.runId] ?? EMPTY_RUN_EVENTS;
      if (existing.some((item) => item.sequence === event.sequence)) {
        return state;
      }

      return {
        eventsByRunId: {
          ...state.eventsByRunId,
          [event.runId]: [...existing, event].sort(
            (left, right) => left.sequence - right.sequence,
          ),
        },
      };
    }),

  clearRunEvents: (runId) =>
    set((state) => {
      const next = { ...state.eventsByRunId };
      delete next[runId];
      return { eventsByRunId: next };
    }),

  clearAllRunEvents: () => set({ eventsByRunId: {} }),
}));

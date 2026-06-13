"use client";

import { create } from "zustand";

export type RunHistoryStatus = "running" | "complete" | "error";

export type RunHistoryRecord = {
  runId: string;
  datasetId: string;
  prompt: string;
  status: RunHistoryStatus;
  createdAt: string;
  completedAt: string | null;
  finalAnswer: string | null;
  artifactIds: string[];
  selectedArtifactId: string | null;
};

type AddRunInput = {
  runId: string;
  datasetId: string;
  prompt: string;
};

type RunHistoryStoreState = {
  runs: RunHistoryRecord[];
  selectedRunId: string | null;
  addRun: (input: AddRunInput) => void;
  markRunComplete: (runId: string, finalAnswer: string) => void;
  markRunError: (runId: string, finalAnswer?: string) => void;
  attachArtifactToRun: (runId: string, artifactId: string) => void;
  setSelectedArtifactForRun: (runId: string, artifactId: string | null) => void;
  selectRun: (runId: string) => void;
  clearHistory: () => void;
};

export const useRunHistoryStore = create<RunHistoryStoreState>((set) => ({
  runs: [],
  selectedRunId: null,

  addRun: ({ runId, datasetId, prompt }) =>
    set((state) => {
      if (state.runs.some((run) => run.runId === runId)) {
        return state;
      }

      const record: RunHistoryRecord = {
        runId,
        datasetId,
        prompt,
        status: "running",
        createdAt: new Date().toISOString(),
        completedAt: null,
        finalAnswer: null,
        artifactIds: [],
        selectedArtifactId: null,
      };

      return {
        runs: [record, ...state.runs],
        selectedRunId: runId,
      };
    }),

  markRunComplete: (runId, finalAnswer) =>
    set((state) => ({
      runs: state.runs.map((run) =>
        run.runId === runId
          ? {
              ...run,
              status: "complete",
              completedAt: new Date().toISOString(),
              finalAnswer,
            }
          : run,
      ),
    })),

  markRunError: (runId, finalAnswer = "Analysis run failed safely.") =>
    set((state) => ({
      runs: state.runs.map((run) =>
        run.runId === runId
          ? {
              ...run,
              status: "error",
              completedAt: new Date().toISOString(),
              finalAnswer,
            }
          : run,
      ),
    })),

  attachArtifactToRun: (runId, artifactId) =>
    set((state) => ({
      runs: state.runs.map((run) => {
        if (run.runId !== runId || run.artifactIds.includes(artifactId)) {
          return run;
        }

        return {
          ...run,
          artifactIds: [...run.artifactIds, artifactId],
        };
      }),
    })),

  setSelectedArtifactForRun: (runId, artifactId) =>
    set((state) => ({
      runs: state.runs.map((run) =>
        run.runId === runId ? { ...run, selectedArtifactId: artifactId } : run,
      ),
    })),

  selectRun: (runId) =>
    set((state) =>
      state.runs.some((run) => run.runId === runId)
        ? { selectedRunId: runId }
        : state,
    ),

  clearHistory: () => set({ runs: [], selectedRunId: null }),
}));

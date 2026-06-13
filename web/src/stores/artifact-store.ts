"use client";

import { create } from "zustand";

import type { InsightArtifact } from "@/types/artifact";

export type ArtifactSelectionSource = "system" | "user";

export type StoredInsightArtifact = InsightArtifact & {
  runId: string | null;
  createdAtIso: string;
  priority?: number;
};

type ArtifactStoreState = {
  artifacts: StoredInsightArtifact[];
  activeRunId: string | null;
  selectedArtifactId: string | null;
  userHasManuallySelectedArtifact: boolean;
  setActiveRunId: (runId: string) => void;
  addArtifact: (artifact: InsightArtifact, runId?: string | null) => StoredInsightArtifact;
  selectArtifact: (artifactId: string, source: ArtifactSelectionSource) => void;
  clearArtifacts: () => void;
  getArtifactsForRun: (runId: string) => StoredInsightArtifact[];
  selectBestArtifactForRun: (
    runId: string,
    source?: ArtifactSelectionSource,
  ) => StoredInsightArtifact | null;
};

export const useArtifactStore = create<ArtifactStoreState>((set, get) => ({
  artifacts: [],
  activeRunId: null,
  selectedArtifactId: null,
  userHasManuallySelectedArtifact: false,

  setActiveRunId: (runId) =>
    set({
      activeRunId: runId,
      userHasManuallySelectedArtifact: false,
    }),

  addArtifact: (artifact, runId) => {
    const effectiveRunId = runId ?? get().activeRunId;
    const existing = get().artifacts.find((item) => item.id === artifact.id);
    if (existing) {
      return existing;
    }

    const storedArtifact: StoredInsightArtifact = {
      ...artifact,
      runId: effectiveRunId,
      createdAtIso: new Date().toISOString(),
    };

    set((state) => ({
      artifacts: [...state.artifacts, storedArtifact],
      selectedArtifactId: state.selectedArtifactId ?? storedArtifact.id,
    }));

    return storedArtifact;
  },

  selectArtifact: (artifactId, source) =>
    set((state) => {
      if (!state.artifacts.some((artifact) => artifact.id === artifactId)) {
        return state;
      }
      return {
        selectedArtifactId: artifactId,
        userHasManuallySelectedArtifact:
          source === "user" ? true : state.userHasManuallySelectedArtifact,
      };
    }),

  clearArtifacts: () =>
    set({
      artifacts: [],
      activeRunId: null,
      selectedArtifactId: null,
      userHasManuallySelectedArtifact: false,
    }),

  getArtifactsForRun: (runId) =>
    get().artifacts.filter((artifact) => artifact.runId === runId),

  selectBestArtifactForRun: (runId, source = "system") => {
    if (source === "system" && get().userHasManuallySelectedArtifact) {
      return null;
    }
    const bestArtifact = pickBestArtifact(get().getArtifactsForRun(runId));
    if (!bestArtifact) {
      return null;
    }
    get().selectArtifact(bestArtifact.id, source);
    return bestArtifact;
  },
}));

function pickBestArtifact(
  artifacts: StoredInsightArtifact[],
): StoredInsightArtifact | null {
  if (artifacts.length === 0) {
    return null;
  }

  return [...artifacts].sort((left, right) => {
    const priorityDelta = (right.priority ?? 0) - (left.priority ?? 0);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }
    return kindRank(left.kind) - kindRank(right.kind);
  })[0];
}

function kindRank(kind: InsightArtifact["kind"]): number {
  if (kind === "chart") {
    return 0;
  }
  if (kind === "table") {
    return 1;
  }
  return 2;
}

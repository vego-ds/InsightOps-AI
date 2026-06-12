"use client";

import { create } from "zustand";

import type { InsightArtifact } from "@/types/artifact";

type ArtifactStoreState = {
  artifacts: InsightArtifact[];
  selectedArtifactId: string | null;
  addArtifact: (artifact: InsightArtifact) => void;
  selectArtifact: (artifactId: string) => void;
  clearArtifacts: () => void;
};

export const useArtifactStore = create<ArtifactStoreState>((set) => ({
  artifacts: [],
  selectedArtifactId: null,

  addArtifact: (artifact) =>
    set((state) => {
      if (state.artifacts.some((item) => item.id === artifact.id)) {
        return state;
      }

      return {
        artifacts: [...state.artifacts, artifact],
        selectedArtifactId: state.selectedArtifactId ?? artifact.id,
      };
    }),

  selectArtifact: (artifactId) =>
    set((state) => {
      if (!state.artifacts.some((artifact) => artifact.id === artifactId)) {
        return state;
      }
      return { selectedArtifactId: artifactId };
    }),

  clearArtifacts: () => set({ artifacts: [], selectedArtifactId: null }),
}));

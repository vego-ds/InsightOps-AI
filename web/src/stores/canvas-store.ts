"use client";

import { create } from "zustand";

import type { CanvasMode } from "@/components/workspace/canvas-mode-tabs";

type CanvasModeSource = "system" | "user";

type CanvasStoreState = {
  activeMode: CanvasMode;
  userLockedModeForRunId: string | null;
  setActiveMode: (
    mode: CanvasMode,
    source: CanvasModeSource,
    runId?: string | null,
  ) => void;
  resetRunFocusLock: (runId: string) => void;
  resetCanvas: () => void;
};

export const useCanvasStore = create<CanvasStoreState>((set) => ({
  activeMode: "preview",
  userLockedModeForRunId: null,

  setActiveMode: (mode, source, runId) =>
    set((state) => {
      if (source === "user") {
        return {
          activeMode: mode,
          userLockedModeForRunId: runId ?? state.userLockedModeForRunId,
        };
      }
      if (runId && state.userLockedModeForRunId === runId) {
        return state;
      }
      return { activeMode: mode };
    }),

  resetRunFocusLock: (runId) =>
    set((state) =>
      state.userLockedModeForRunId === runId
        ? { userLockedModeForRunId: null }
        : state,
    ),

  resetCanvas: () =>
    set({
      activeMode: "preview",
      userLockedModeForRunId: null,
    }),
}));

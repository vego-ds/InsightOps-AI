"use client";

import { create } from "zustand";
import type {
  DatasetUploadStatus,
  FilePreviewDataset,
} from "@/types/dataset";

type DatasetStoreState = {
  activeDataset: FilePreviewDataset | null;
  uploadStatus: DatasetUploadStatus;
  errorMessage: string | null;
  selectedColumnKey: string | null;

  setActiveDataset: (dataset: FilePreviewDataset) => void;
  clearActiveDataset: () => void;
  setUploadStatus: (status: DatasetUploadStatus) => void;
  setErrorMessage: (message: string | null) => void;
  setSelectedColumnKey: (columnKey: string | null) => void;
};

export const useDatasetStore = create<DatasetStoreState>((set) => ({
  activeDataset: null,
  uploadStatus: "idle",
  errorMessage: null,
  selectedColumnKey: null,

  setActiveDataset: (dataset) =>
    set({
      activeDataset: dataset,
      uploadStatus: "success",
      errorMessage: null,
      selectedColumnKey: dataset.columns[0]?.key ?? null,
    }),

  clearActiveDataset: () =>
    set({
      activeDataset: null,
      uploadStatus: "idle",
      errorMessage: null,
      selectedColumnKey: null,
    }),

  setUploadStatus: (status) =>
    set({
      uploadStatus: status,
    }),

  setErrorMessage: (message) =>
    set({
      errorMessage: message,
      uploadStatus: message ? "runtime_error" : "idle",
    }),

  setSelectedColumnKey: (columnKey) =>
    set({
      selectedColumnKey: columnKey,
    }),
}));

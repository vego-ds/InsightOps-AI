"use client";

import { create } from "zustand";

import type { ChatMessage } from "@/types/chat";

type ChatStoreState = {
  messages: ChatMessage[];
  addUserMessage: (content: string) => ChatMessage;
  addAssistantMessage: (content: string) => ChatMessage;
  addPendingAssistantMessage: () => ChatMessage;
  attachRunToAssistantMessage: (messageId: string, runId: string) => void;
  resolveAssistantMessage: (messageId: string, content: string) => void;
  failAssistantMessage: (messageId: string, errorMessage: string) => void;
  clearMessages: () => void;
};

export const useChatStore = create<ChatStoreState>((set) => ({
  messages: [],

  addUserMessage: (content) => {
    const message = buildMessage("user", content, "idle");
    set((state) => ({
      messages: [...state.messages, message],
    }));
    return message;
  },

  addAssistantMessage: (content) => {
    const message = buildMessage("assistant", content, "idle");
    set((state) => ({
      messages: [...state.messages, message],
    }));
    return message;
  },

  addPendingAssistantMessage: () => {
    const message = buildMessage(
      "assistant",
      "Preparing analysis request...",
      "loading",
    );
    set((state) => ({
      messages: [...state.messages, message],
    }));
    return message;
  },

  attachRunToAssistantMessage: (messageId, runId) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId ? { ...message, runId } : message,
      ),
    })),

  resolveAssistantMessage: (messageId, content) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId
          ? { ...message, content, status: "idle" }
          : message,
      ),
    })),

  failAssistantMessage: (messageId, errorMessage) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId
          ? { ...message, content: errorMessage, status: "error" }
          : message,
      ),
    })),

  clearMessages: () => set({ messages: [] }),
}));

function buildMessage(
  role: ChatMessage["role"],
  content: string,
  status: ChatMessage["status"],
): ChatMessage {
  return {
    id: createMessageId(),
    role,
    content,
    createdAtIso: new Date().toISOString(),
    status,
  };
}

function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

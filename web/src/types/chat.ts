export type ChatMessageRole = "user" | "assistant";

export type ChatMessageStatus = "idle" | "loading" | "error";

export type ChatMessage = {
  id: string;
  role: ChatMessageRole;
  content: string;
  createdAtIso: string;
  status: ChatMessageStatus;
};

export type ChatDraft = {
  content: string;
};

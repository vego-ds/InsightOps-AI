"use client";

import type React from "react";
import { Archive, Columns3, Lock, Table2 } from "lucide-react";

export type CanvasMode = "preview" | "schema" | "artifacts";

type CanvasModeTabsProps = {
  mode: CanvasMode;
  schemaDisabled: boolean;
  artifactsDisabled: boolean;
  onModeChange: (mode: CanvasMode) => void;
};

export function CanvasModeTabs({
  mode,
  schemaDisabled,
  artifactsDisabled,
  onModeChange,
}: CanvasModeTabsProps) {
  return (
    <div className="inline-flex w-full rounded-2xl border border-white/10 bg-black/20 p-1 sm:w-auto">
      <ModeButton
        active={mode === "preview"}
        icon={<Table2 className="h-4 w-4" />}
        label="Preview"
        onClick={() => onModeChange("preview")}
      />
      <ModeButton
        active={mode === "schema"}
        disabled={schemaDisabled}
        icon={
          schemaDisabled ? (
            <Lock className="h-4 w-4" />
          ) : (
            <Columns3 className="h-4 w-4" />
          )
        }
        label="Schema"
        onClick={() => onModeChange("schema")}
      />
      <ModeButton
        active={mode === "artifacts"}
        disabled={artifactsDisabled}
        icon={
          artifactsDisabled ? (
            <Lock className="h-4 w-4" />
          ) : (
            <Archive className="h-4 w-4" />
          )
        }
        label="Artifacts"
        onClick={() => onModeChange("artifacts")}
      />
    </div>
  );
}

function ModeButton({
  active,
  disabled = false,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  disabled?: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        "inline-flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition sm:flex-none",
        active
          ? "bg-cyan-300/15 text-cyan-100 shadow-sm"
          : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100",
        disabled ? "cursor-not-allowed opacity-50 hover:bg-transparent" : "",
      ].join(" ")}
      aria-pressed={active}
    >
      {icon}
      {label}
    </button>
  );
}

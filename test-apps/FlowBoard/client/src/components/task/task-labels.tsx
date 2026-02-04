"use client";

import * as React from "react";
import { useState, useCallback, useRef } from "react";
import { Plus, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { Label } from "@/types";

// =============================================================================
// Task Labels — display and edit task labels
//
// Shows current labels as colored tags.
// "Add label" button opens a popover with:
//   - Project labels with color dots (toggle on/off)
//   - Create new label inline (name + color picker)
// =============================================================================

// ---------------------------------------------------------------------------
// Popover shim: import dynamically or use radix directly
// We use @radix-ui/react-popover which is already a dependency.
// ---------------------------------------------------------------------------

// Check if popover component exists, otherwise inline it
// The project has @radix-ui/react-popover in deps but may not have the
// component file yet. We'll import from radix directly as a fallback.

const PRESET_COLORS = [
  "#6366f1", // violet
  "#8b5cf6", // purple
  "#ec4899", // pink
  "#ef4444", // red
  "#f97316", // orange
  "#eab308", // yellow
  "#22c55e", // green
  "#14b8a6", // teal
  "#06b6d4", // cyan
  "#3b82f6", // blue
  "#6b7280", // gray
];

interface TaskLabelsProps {
  labels: Label[];
  projectLabels: Label[];
  onToggle: (labelId: string) => Promise<void>;
  onCreate: (name: string, color: string) => Promise<void>;
}

export function TaskLabels({
  labels,
  projectLabels,
  onToggle,
  onCreate,
}: TaskLabelsProps) {
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState(PRESET_COLORS[0] ?? "#6366f1");
  const inputRef = useRef<HTMLInputElement>(null);

  // Set of currently assigned label IDs for quick lookup
  const assignedIds = new Set(labels.map((l) => l.id));

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleCreateLabel = useCallback(async () => {
    const trimmed = newName.trim();
    if (!trimmed) return;

    await onCreate(trimmed, newColor);
    setNewName("");
    setIsCreating(false);
  }, [newName, newColor, onCreate]);

  const handleCreateKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleCreateLabel();
      }
      if (e.key === "Escape") {
        setIsCreating(false);
        setNewName("");
      }
    },
    [handleCreateLabel],
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider select-none">
          Labels
        </h3>
      </div>

      <div className="flex flex-wrap gap-1.5 items-center">
        {labels.map((label) => (
          <Badge
            key={label.id}
            size="sm"
            className="gap-1 cursor-default"
            style={{
              backgroundColor: `${label.color}20`,
              color: label.color,
              borderColor: `${label.color}40`,
              border: "1px solid",
            }}
          >
            <span
              className="h-2 w-2 rounded-full shrink-0"
              style={{ backgroundColor: label.color }}
            />
            {label.name}
          </Badge>
        ))}

        {/* Add label popover */}
        <LabelPickerPopover
          isOpen={isPickerOpen}
          onOpenChange={setIsPickerOpen}
          projectLabels={projectLabels}
          assignedIds={assignedIds}
          onToggle={onToggle}
          isCreating={isCreating}
          setIsCreating={setIsCreating}
          newName={newName}
          setNewName={setNewName}
          newColor={newColor}
          setNewColor={setNewColor}
          inputRef={inputRef}
          handleCreateLabel={handleCreateLabel}
          handleCreateKeyDown={handleCreateKeyDown}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Label Picker Popover — internal component
// Uses a simple div-based popover since @radix-ui/react-popover is available
// but the component file may not exist. We use a portal-free approach.
// ---------------------------------------------------------------------------

function LabelPickerPopover({
  isOpen,
  onOpenChange,
  projectLabels,
  assignedIds,
  onToggle,
  isCreating,
  setIsCreating,
  newName,
  setNewName,
  newColor,
  setNewColor,
  inputRef,
  handleCreateLabel,
  handleCreateKeyDown,
}: {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  projectLabels: Label[];
  assignedIds: Set<string>;
  onToggle: (labelId: string) => Promise<void>;
  isCreating: boolean;
  setIsCreating: (v: boolean) => void;
  newName: string;
  setNewName: (v: string) => void;
  newColor: string;
  setNewColor: (v: string) => void;
  inputRef: React.RefObject<HTMLInputElement>;
  handleCreateLabel: () => Promise<void>;
  handleCreateKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 px-2 text-xs"
        onClick={() => onOpenChange(!isOpen)}
      >
        <Plus className="h-3 w-3 mr-1" />
        Add
      </Button>

      {isOpen && (
        <>
          {/* Backdrop to close on outside click */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => {
              onOpenChange(false);
              setIsCreating(false);
            }}
          />
          {/* Dropdown */}
          <div
            className={cn(
              "absolute left-0 top-full mt-1 z-50",
              "w-[240px] rounded-lg border border-border",
              "bg-surface-elevated shadow-dropdown",
              "p-1.5",
              "animate-scale-in",
            )}
          >
            {/* Label list */}
            <div className="max-h-[200px] overflow-y-auto space-y-0.5">
              {projectLabels.length === 0 && !isCreating ? (
                <p className="text-xs text-text-quaternary text-center py-3">
                  No labels yet
                </p>
              ) : (
                projectLabels.map((label) => {
                  const isActive = assignedIds.has(label.id);
                  return (
                    <button
                      key={label.id}
                      type="button"
                      onClick={() => onToggle(label.id)}
                      className={cn(
                        "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left text-sm",
                        "transition-colors duration-fast",
                        "hover:bg-surface-hover",
                        isActive && "bg-surface-hover/50",
                      )}
                    >
                      <span
                        className="h-3 w-3 rounded-full shrink-0 border"
                        style={{
                          backgroundColor: label.color,
                          borderColor: `${label.color}60`,
                        }}
                      />
                      <span className="flex-1 truncate text-text-primary">
                        {label.name}
                      </span>
                      {isActive && (
                        <Check className="h-3.5 w-3.5 text-primary shrink-0" />
                      )}
                    </button>
                  );
                })
              )}
            </div>

            {/* Separator */}
            <div className="h-px bg-border-subtle my-1.5" />

            {/* Create new label */}
            {isCreating ? (
              <div className="space-y-2 p-1">
                <Input
                  ref={inputRef}
                  inputSize="sm"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={handleCreateKeyDown}
                  placeholder="Label name..."
                  className="text-xs"
                  autoFocus
                />
                <div className="flex flex-wrap gap-1">
                  {PRESET_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setNewColor(color)}
                      className={cn(
                        "h-5 w-5 rounded-full border-2 transition-all duration-fast",
                        newColor === color
                          ? "border-text-primary scale-110"
                          : "border-transparent hover:scale-105",
                      )}
                      style={{ backgroundColor: color }}
                      aria-label={`Color ${color}`}
                    />
                  ))}
                </div>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="default"
                    size="sm"
                    className="h-6 px-2 text-xs flex-1"
                    onClick={handleCreateLabel}
                    disabled={!newName.trim()}
                  >
                    Create
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={() => {
                      setIsCreating(false);
                      setNewName("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setIsCreating(true);
                  setTimeout(() => inputRef.current?.focus(), 0);
                }}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-1.5 rounded-md",
                  "text-xs text-text-tertiary",
                  "hover:bg-surface-hover hover:text-text-primary",
                  "transition-colors duration-fast",
                )}
              >
                <Plus className="h-3 w-3" />
                <span>Create new label</span>
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}


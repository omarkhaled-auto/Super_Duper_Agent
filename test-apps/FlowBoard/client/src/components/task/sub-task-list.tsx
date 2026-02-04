"use client";

import * as React from "react";
import { useState, useCallback, useRef } from "react";
import { Plus, X, ListChecks } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SubTask } from "@/types";

// =============================================================================
// Sub-Task List — Checkable list of sub-tasks with add/delete
//
// Features:
//   - Checkbox to toggle completion (immediate API call)
//   - Strike-through for completed items
//   - Delete button on hover
//   - "Add sub-task" input at the bottom
//   - Progress indicator showing X/Y completed
// =============================================================================

interface SubTaskListProps {
  subtasks: SubTask[];
  subtaskTotal: number;
  subtaskCompleted: number;
  onToggle: (subtaskId: string) => Promise<void>;
  onAdd: (title: string) => Promise<void>;
  onDelete: (subtaskId: string) => Promise<void>;
}

export function SubTaskList({
  subtasks,
  subtaskTotal,
  subtaskCompleted,
  onToggle,
  onAdd,
  onDelete,
}: SubTaskListProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleAdd = useCallback(async () => {
    const trimmed = newTitle.trim();
    if (!trimmed) return;

    setNewTitle("");
    await onAdd(trimmed);

    // Keep the input focused for rapid entry
    inputRef.current?.focus();
  }, [newTitle, onAdd]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleAdd();
      }
      if (e.key === "Escape") {
        setIsAdding(false);
        setNewTitle("");
      }
    },
    [handleAdd],
  );

  const handleStartAdding = useCallback(() => {
    setIsAdding(true);
    // Focus after render
    setTimeout(() => inputRef.current?.focus(), 0);
  }, []);

  // ---------------------------------------------------------------------------
  // Progress
  // ---------------------------------------------------------------------------

  const progressPercent =
    subtaskTotal > 0 ? Math.round((subtaskCompleted / subtaskTotal) * 100) : 0;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider select-none">
            Sub-tasks
          </h3>
          {subtaskTotal > 0 && (
            <span className="text-xs text-text-quaternary tabular-nums">
              {subtaskCompleted}/{subtaskTotal}
            </span>
          )}
        </div>
        {!isAdding && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={handleStartAdding}
          >
            <Plus className="h-3 w-3 mr-1" />
            Add
          </Button>
        )}
      </div>

      {/* Progress bar */}
      {subtaskTotal > 0 && (
        <div className="h-1.5 w-full bg-surface-tertiary rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-normal",
              progressPercent === 100 ? "bg-green-500" : "bg-primary",
            )}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      {/* Sub-task items */}
      {subtasks.length > 0 ? (
        <div className="space-y-0.5">
          {subtasks
            .sort((a, b) => a.position - b.position)
            .map((subtask) => (
              <SubTaskItem
                key={subtask.id}
                subtask={subtask}
                onToggle={onToggle}
                onDelete={onDelete}
              />
            ))}
        </div>
      ) : !isAdding ? (
        <button
          type="button"
          onClick={handleStartAdding}
          className={cn(
            "w-full flex items-center gap-2 px-3 py-3 rounded-md",
            "text-sm text-text-quaternary",
            "bg-surface-elevated/30 hover:bg-surface-hover",
            "transition-colors duration-fast cursor-pointer",
            "border border-dashed border-border-subtle",
          )}
        >
          <ListChecks className="h-4 w-4" />
          <span>Add a sub-task...</span>
        </button>
      ) : null}

      {/* Add input */}
      {isAdding && (
        <div className="flex items-center gap-2">
          <Checkbox disabled className="opacity-30" />
          <Input
            ref={inputRef}
            inputSize="sm"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              if (!newTitle.trim()) {
                setIsAdding(false);
              }
            }}
            placeholder="Add a sub-task..."
            className="flex-1 bg-transparent border-transparent border-b border-b-border-subtle rounded-none px-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-b-primary"
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0"
            onClick={() => {
              setIsAdding(false);
              setNewTitle("");
            }}
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-task item
// ---------------------------------------------------------------------------

function SubTaskItem({
  subtask,
  onToggle,
  onDelete,
}: {
  subtask: SubTask;
  onToggle: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn(
        "group flex items-center gap-2 px-2 py-1.5 rounded-md",
        "hover:bg-surface-hover transition-colors duration-fast",
        "-mx-2",
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Checkbox
        checked={subtask.completed}
        onCheckedChange={() => onToggle(subtask.id)}
        className="shrink-0"
      />
      <span
        className={cn(
          "flex-1 text-sm font-body leading-snug",
          "transition-all duration-fast",
          subtask.completed && "line-through text-text-quaternary",
          !subtask.completed && "text-text-primary",
        )}
      >
        {subtask.title}
      </span>
      {isHovered && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(subtask.id);
          }}
          className={cn(
            "shrink-0 p-0.5 rounded-sm",
            "text-text-quaternary hover:text-destructive",
            "transition-colors duration-fast",
          )}
          aria-label={`Delete sub-task: ${subtask.title}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}

"use client";

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import type { Task, TaskStatus } from "@/types";

// =============================================================================
// AddTaskInline -- Inline task creation at the bottom of a kanban column
//
// - Click "Add task" to reveal a text input
// - Enter to create, Escape to cancel
// - Creates task with MEDIUM priority and the column's status
// - Optimistic: calls onTaskCreated immediately (parent adds to column)
// =============================================================================

interface AddTaskInlineProps {
  projectId: string;
  status: TaskStatus;
  position: number;
  onTaskCreated: (task: Task) => void;
}

// Server returns Task directly, no wrapper

export function AddTaskInline({
  projectId,
  status,
  position,
  onTaskCreated,
}: AddTaskInlineProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [value, setValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus the input when opening
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  function handleOpen() {
    setIsOpen(true);
    setValue("");
  }

  function handleClose() {
    setIsOpen(false);
    setValue("");
  }

  async function handleSubmit() {
    const title = value.trim();
    if (!title || isSubmitting) return;

    setIsSubmitting(true);

    // Optimistic: create a temporary task with a temp ID
    const tempId = `temp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const optimisticTask: Task = {
      id: tempId,
      title,
      description: null,
      status,
      priority: "MEDIUM" as Task["priority"],
      position,
      dueDate: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      projectId,
      creatorId: "",
      assigneeId: null,
      assignee: null,
      creator: { id: "", name: "", email: "", avatarUrl: null },
      labels: [],
      subtasks: [],
      subtaskTotal: 0,
      subtaskCompleted: 0,
      commentCount: 0,
    };

    // Add to column immediately
    onTaskCreated(optimisticTask);
    setValue("");

    try {
      const res = await api.post<Task>(
        `/projects/${projectId}/tasks`,
        {
          title,
          status,
          priority: "MEDIUM",
          position,
        },
      );

      // Replace the optimistic task with the real one
      // The parent will handle this by matching the temp ID or the returned task
      if (res) {
        onTaskCreated(res);
      }
    } catch {
      // The optimistic task will remain with a temp ID, but that is acceptable.
      // A refetch can correct the state. We keep the input open for retry.
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      void handleSubmit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleClose();
    }
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={handleOpen}
        className={cn(
          "flex items-center gap-1.5 w-full px-2 py-1.5 rounded-md",
          "text-xs font-medium font-body text-text-quaternary",
          "hover:text-text-tertiary hover:bg-surface-hover",
          "transition-colors duration-fast",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background",
        )}
      >
        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
        Add task
      </button>
    );
  }

  return (
    <div className="px-0.5">
      <div
        className={cn(
          "rounded-lg border border-border-accent bg-surface-elevated p-2",
          "shadow-sm",
        )}
      >
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            // If empty, close. If has content, keep open.
            if (!value.trim()) {
              handleClose();
            }
          }}
          placeholder="Task title..."
          disabled={isSubmitting}
          className={cn(
            "w-full text-sm font-body text-text-primary",
            "bg-transparent border-none outline-none p-0",
            "placeholder:text-text-quaternary",
            "disabled:opacity-50",
          )}
        />
        <p className="text-[10px] text-text-quaternary mt-1.5 font-body">
          Enter to create &middot; Esc to cancel
        </p>
      </div>
    </div>
  );
}

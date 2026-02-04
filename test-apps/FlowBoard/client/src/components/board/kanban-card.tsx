"use client";

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { GripVertical, Calendar } from "lucide-react";
import { isToday, isPast, parseISO, format } from "date-fns";
import type { Task, TaskPriority } from "@/types";

// =============================================================================
// KanbanCard -- Draggable task card for the board
//
// - Uses @dnd-kit/sortable for drag-and-drop
// - Left border colored by priority
// - Shows title, priority badge, assignee avatar, due date
// - Inline title editing on double-click
// - Hover elevation, drag opacity + placeholder
// =============================================================================

/** Priority -> left border color class mapping */
const PRIORITY_BORDER: Record<string, string> = {
  URGENT: "border-l-urgent",
  HIGH: "border-l-high",
  MEDIUM: "border-l-medium",
  LOW: "border-l-low",
};

/** Priority -> badge variant mapping */
const PRIORITY_BADGE_VARIANT: Record<string, "priority-urgent" | "priority-high" | "priority-medium" | "priority-low"> = {
  URGENT: "priority-urgent",
  HIGH: "priority-high",
  MEDIUM: "priority-medium",
  LOW: "priority-low",
};

/** Priority display labels */
const PRIORITY_LABEL: Record<string, string> = {
  URGENT: "Urgent",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

interface KanbanCardProps {
  task: Task;
  /** Whether this card is currently the active drag item */
  isDragOverlay?: boolean;
  onTaskClick?: (taskId: string) => void;
  onTitleUpdate?: (taskId: string, newTitle: string) => void;
}

export function KanbanCard({
  task,
  isDragOverlay = false,
  onTaskClick,
  onTitleUpdate,
}: KanbanCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(task.title);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: task.id,
    data: {
      type: "task",
      task,
    },
    disabled: isEditing,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? "transform 200ms ease-out",
  };

  // Focus the input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  // ---- Due date helpers ----
  const dueDateInfo = getDueDateInfo(task.dueDate);

  // ---- Priority border color ----
  const priorityBorder = PRIORITY_BORDER[task.priority as string] ?? "border-l-transparent";
  const priorityBadgeVariant = PRIORITY_BADGE_VARIANT[task.priority as string];
  const priorityLabel = PRIORITY_LABEL[task.priority as string];

  // ---- Assignee initials ----
  const assigneeInitials = task.assignee
    ? task.assignee.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : null;

  // ---- Inline edit handlers ----
  function handleDoubleClick(e: React.MouseEvent) {
    e.stopPropagation();
    setEditValue(task.title);
    setIsEditing(true);
  }

  function commitEdit() {
    const trimmed = editValue.trim();
    setIsEditing(false);
    if (trimmed && trimmed !== task.title && onTitleUpdate) {
      onTitleUpdate(task.id, trimmed);
    }
  }

  function cancelEdit() {
    setIsEditing(false);
    setEditValue(task.title);
  }

  function handleEditKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitEdit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancelEdit();
    }
  }

  function handleCardClick() {
    if (!isEditing && onTaskClick) {
      onTaskClick(task.id);
    }
  }

  // ---- Render ----
  return (
    <div
      ref={isDragOverlay ? undefined : setNodeRef}
      style={isDragOverlay ? undefined : style}
      className={cn(
        "group/card relative rounded-lg border border-border-subtle bg-surface-elevated",
        "border-l-[3px] transition-all duration-200 ease-out",
        "cursor-pointer select-none",
        priorityBorder,
        // Hover state: slightly elevated shadow
        !isDragging && !isDragOverlay && "hover:shadow-card-hover hover:border-border-strong",
        // Drag state: reduced opacity, acts as placeholder
        isDragging && "opacity-40 shadow-none",
        // Drag overlay: floating elevated card
        isDragOverlay && "shadow-lg rotate-[2deg] scale-[1.02] border-border-accent",
      )}
      onClick={handleCardClick}
      {...(isDragOverlay ? {} : attributes)}
    >
      {/* Card content */}
      <div className="p-3 space-y-2">
        {/* Top row: drag handle + title */}
        <div className="flex items-start gap-1.5">
          {/* Drag handle */}
          {!isDragOverlay && (
            <button
              className={cn(
                "shrink-0 mt-0.5 p-0.5 rounded-sm",
                "text-text-quaternary opacity-0 group-hover/card:opacity-100",
                "hover:text-text-tertiary hover:bg-surface-hover",
                "transition-all duration-fast cursor-grab active:cursor-grabbing",
                "focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
              aria-label="Drag to reorder"
              {...listeners}
            >
              <GripVertical className="h-4 w-4" aria-hidden="true" />
            </button>
          )}

          {/* Title or inline edit */}
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <input
                ref={inputRef}
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={handleEditKeyDown}
                className={cn(
                  "w-full text-sm font-medium font-body text-text-primary",
                  "bg-transparent border-none outline-none p-0",
                  "focus:ring-0",
                )}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <p
                className="text-sm font-medium font-body text-text-primary leading-snug line-clamp-2"
                onDoubleClick={handleDoubleClick}
                title={task.title}
              >
                {task.title}
              </p>
            )}
          </div>
        </div>

        {/* Labels (if any) */}
        {task.labels && task.labels.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {task.labels.slice(0, 3).map((label) => (
              <span
                key={label.id}
                className="inline-flex items-center px-1.5 py-px text-[10px] font-medium rounded-full"
                style={{
                  backgroundColor: `${label.color}20`,
                  color: label.color,
                }}
              >
                {label.name}
              </span>
            ))}
            {task.labels.length > 3 && (
              <span className="inline-flex items-center px-1.5 py-px text-[10px] font-medium rounded-full bg-secondary text-text-tertiary">
                +{task.labels.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Bottom row: priority badge, due date, subtask progress, assignee avatar */}
        <div className="flex items-center justify-between gap-2 pt-0.5">
          <div className="flex items-center gap-1.5 min-w-0">
            {/* Priority badge */}
            {priorityBadgeVariant && (
              <Badge variant={priorityBadgeVariant} size="sm">
                {priorityLabel}
              </Badge>
            )}

            {/* Due date */}
            {dueDateInfo && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 text-[10px] font-medium font-body whitespace-nowrap",
                  dueDateInfo.colorClass,
                )}
              >
                <Calendar className="h-3 w-3" aria-hidden="true" />
                {dueDateInfo.label}
              </span>
            )}

            {/* Subtask progress */}
            {task.subtaskTotal > 0 && (
              <span className="text-[10px] font-medium font-body text-text-tertiary whitespace-nowrap">
                {task.subtaskCompleted}/{task.subtaskTotal}
              </span>
            )}
          </div>

          {/* Assignee avatar */}
          {task.assignee && (
            <Avatar size="xs" className="shrink-0">
              {task.assignee.avatarUrl ? (
                <AvatarImage
                  src={task.assignee.avatarUrl}
                  alt={task.assignee.name}
                />
              ) : null}
              <AvatarFallback>{assigneeInitials}</AvatarFallback>
            </Avatar>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Due date helper
// =============================================================================

interface DueDateInfo {
  label: string;
  colorClass: string;
}

function getDueDateInfo(dueDate: string | null): DueDateInfo | null {
  if (!dueDate) return null;

  try {
    const date = parseISO(dueDate);

    if (isToday(date)) {
      return {
        label: "Today",
        colorClass: "text-warning",
      };
    }

    if (isPast(date)) {
      return {
        label: format(date, "MMM d"),
        colorClass: "text-error",
      };
    }

    return {
      label: format(date, "MMM d"),
      colorClass: "text-text-tertiary",
    };
  } catch {
    return null;
  }
}

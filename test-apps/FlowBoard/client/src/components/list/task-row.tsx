"use client";

import * as React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Avatar,
  AvatarImage,
  AvatarFallback,
} from "@/components/ui/avatar";
import { StatusSelect } from "@/components/list/status-select";
import { PrioritySelect } from "@/components/list/priority-select";
import { cn } from "@/lib/utils";
import { formatDate, formatRelativeDate } from "@/lib/utils";
import { parseISO, isPast, isToday } from "date-fns";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// TaskRow -- Single table row for a task.
//
// Features:
//   - Checkbox for multi-select
//   - Title (truncated)
//   - Inline status dropdown (optimistic update via API)
//   - Inline priority dropdown with colored badges
//   - Assignee with avatar + name
//   - Due date (red if overdue)
//   - Created date (relative)
//   - Hover state: surface-tertiary background
// =============================================================================

interface TaskRowProps {
  task: Task;
  isSelected: boolean;
  onToggleSelect: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onPriorityChange: (taskId: string, priority: TaskPriority) => void;
  onRowClick?: (taskId: string) => void;
}

/**
 * Get initials from a name string.
 * "John Doe" -> "JD", "Alice" -> "A"
 */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/**
 * Check if a date string is overdue (past and not today).
 */
function isOverdue(dateStr: string | null | undefined): boolean {
  if (!dateStr) return false;
  try {
    const date = parseISO(dateStr);
    return isPast(date) && !isToday(date);
  } catch {
    return false;
  }
}

export const TaskRow = React.memo(function TaskRow({
  task,
  isSelected,
  onToggleSelect,
  onStatusChange,
  onPriorityChange,
  onRowClick,
}: TaskRowProps) {
  const overdue = isOverdue(task.dueDate ?? undefined);
  const primaryAssignee = task.assignee;

  const handleRowClick = React.useCallback(
    (e: React.MouseEvent) => {
      // Don't trigger row click if user clicked on an interactive element
      const target = e.target as HTMLElement;
      if (
        target.closest("button") ||
        target.closest("[role='combobox']") ||
        target.closest("[role='listbox']") ||
        target.closest("[data-radix-select-trigger]") ||
        target.closest("label")
      ) {
        return;
      }
      onRowClick?.(task.id);
    },
    [task.id, onRowClick],
  );

  return (
    <tr
      className={cn(
        "group border-b border-border-subtle transition-colors duration-fast cursor-pointer",
        "hover:bg-surface-tertiary",
        isSelected && "bg-surface-selected hover:bg-surface-selected",
      )}
      onClick={handleRowClick}
      role="row"
      aria-selected={isSelected}
    >
      {/* ---- Checkbox ---- */}
      <td className="w-10 px-3 py-2.5">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelect(task.id)}
          onClick={(e) => e.stopPropagation()}
          aria-label={`Select task: ${task.title}`}
        />
      </td>

      {/* ---- Title ---- */}
      <td className="px-3 py-2.5">
        <span
          className={cn(
            "block truncate text-sm font-medium text-text-primary",
            "group-hover:text-violet transition-colors duration-fast",
            task.status === TaskStatus.DONE && "line-through text-text-tertiary",
          )}
          title={task.title}
        >
          {task.title}
        </span>
      </td>

      {/* ---- Status ---- */}
      <td className="px-3 py-2.5">
        <StatusSelect
          value={task.status}
          onChange={(status) => onStatusChange(task.id, status)}
        />
      </td>

      {/* ---- Priority ---- */}
      <td className="px-3 py-2.5">
        <PrioritySelect
          value={task.priority}
          onChange={(priority) => onPriorityChange(task.id, priority)}
        />
      </td>

      {/* ---- Assignee (hidden on mobile <768px) ---- */}
      <td className="hidden md:table-cell px-3 py-2.5">
        {primaryAssignee ? (
          <div className="flex items-center gap-2 min-w-0">
            <Avatar size="xs">
              {primaryAssignee.avatarUrl && (
                <AvatarImage
                  src={primaryAssignee.avatarUrl}
                  alt={primaryAssignee.name}
                />
              )}
              <AvatarFallback>
                {getInitials(primaryAssignee.name)}
              </AvatarFallback>
            </Avatar>
            <span className="truncate text-xs text-text-secondary">
              {primaryAssignee.name}
            </span>
          </div>
        ) : (
          <span className="text-xs text-text-quaternary">Unassigned</span>
        )}
      </td>

      {/* ---- Due Date ---- */}
      <td className="px-3 py-2.5">
        {task.dueDate ? (
          <span
            className={cn(
              "text-xs",
              overdue
                ? "text-error font-medium"
                : "text-text-secondary",
            )}
          >
            {formatDate(task.dueDate)}
            {overdue && (
              <span className="ml-1 text-2xs text-error/70">(overdue)</span>
            )}
          </span>
        ) : (
          <span className="text-xs text-text-quaternary">--</span>
        )}
      </td>

      {/* ---- Created (hidden on mobile + tablet <1024px) ---- */}
      <td className="hidden lg:table-cell px-3 py-2.5">
        <span className="text-xs text-text-tertiary">
          {formatRelativeDate(task.createdAt)}
        </span>
      </td>
    </tr>
  );
});

"use client";

import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { KanbanCard } from "./kanban-card";
import { AddTaskInline } from "./add-task-inline";
import type { Task, TaskStatus } from "@/types";

// =============================================================================
// KanbanColumn -- A single status column in the board
//
// - Column header with status name, colored indicator, and task count
// - Droppable area via @dnd-kit
// - SortableContext wrapping the card list for within-column reordering
// - ScrollArea for vertical overflow
// - AddTaskInline at the bottom
// =============================================================================

/** Display configuration for each column status */
const STATUS_CONFIG: Record<
  string,
  { label: string; colorClass: string; dotColor: string }
> = {
  BACKLOG: {
    label: "Backlog",
    colorClass: "text-status-backlog",
    dotColor: "bg-status-backlog",
  },
  TODO: {
    label: "To Do",
    colorClass: "text-status-todo",
    dotColor: "bg-status-todo",
  },
  IN_PROGRESS: {
    label: "In Progress",
    colorClass: "text-status-in-progress",
    dotColor: "bg-status-in-progress",
  },
  IN_REVIEW: {
    label: "In Review",
    colorClass: "text-status-in-review",
    dotColor: "bg-status-in-review",
  },
  DONE: {
    label: "Done",
    colorClass: "text-status-done",
    dotColor: "bg-status-done",
  },
};

interface KanbanColumnProps {
  status: TaskStatus;
  tasks: Task[];
  projectId: string;
  onTaskClick?: (taskId: string) => void;
  onTitleUpdate?: (taskId: string, newTitle: string) => void;
  onTaskCreated?: (task: Task) => void;
}

export function KanbanColumn({
  status,
  tasks,
  projectId,
  onTaskClick,
  onTitleUpdate,
  onTaskCreated,
}: KanbanColumnProps) {
  const config = STATUS_CONFIG[status as string] ?? {
    label: status,
    colorClass: "text-text-tertiary",
    dotColor: "bg-text-tertiary",
  };

  const { setNodeRef, isOver } = useDroppable({
    id: `column-${status}`,
    data: {
      type: "column",
      status,
    },
  });

  const taskIds = tasks.map((t) => t.id);

  function handleTaskCreated(task: Task) {
    if (onTaskCreated) {
      onTaskCreated(task);
    }
  }

  return (
    <div
      className={cn(
        "flex flex-col h-full",
        // Mobile: full width (parent handles sizing via snap container)
        // Tablet+: standard kanban column width
        "w-full md:w-kanban-col md:min-w-kanban-col md:shrink-0",
        "motion-safe:transition-colors duration-fast",
      )}
    >
      {/* Column header */}
      <div className="flex items-center gap-2 px-2 pb-3 shrink-0">
        {/* Colored status dot */}
        <div
          className={cn("h-2.5 w-2.5 rounded-full shrink-0", config.dotColor)}
          aria-hidden="true"
        />

        {/* Status label */}
        <span className="text-sm font-semibold font-heading text-text-primary tracking-tight">
          {config.label}
        </span>

        {/* Task count badge */}
        <Badge variant="default" size="sm" className="tabular-nums">
          {tasks.length}
        </Badge>
      </div>

      {/* Droppable card list area */}
      <div
        ref={setNodeRef}
        className={cn(
          "flex-1 min-h-0 rounded-lg transition-colors duration-200",
          isOver && "bg-surface-hover/50",
        )}
      >
        <ScrollArea className="h-full">
          <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
            <div className="flex flex-col gap-2 px-0.5 pb-2">
              {tasks.map((task) => (
                <KanbanCard
                  key={task.id}
                  task={task}
                  onTaskClick={onTaskClick}
                  onTitleUpdate={onTitleUpdate}
                />
              ))}

              {/* Empty column message */}
              {tasks.length === 0 && !isOver && (
                <div className="flex items-center justify-center py-8 text-text-quaternary text-xs font-body">
                  No tasks
                </div>
              )}

              {/* Drop indicator when dragging over empty column */}
              {tasks.length === 0 && isOver && (
                <div className="h-16 rounded-lg border-2 border-dashed border-border-accent bg-violet-subtle/30 transition-all duration-200" />
              )}
            </div>
          </SortableContext>

          {/* Inline add task */}
          <div className="px-0.5 pb-1 pt-1">
            <AddTaskInline
              projectId={projectId}
              status={status}
              position={tasks.length}
              onTaskCreated={handleTaskCreated}
            />
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

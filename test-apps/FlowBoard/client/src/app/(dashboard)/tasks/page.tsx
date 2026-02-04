"use client";

import * as React from "react";

import {
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { formatRelativeDate } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTasks } from "@/hooks/use-tasks";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// My Tasks Page -- Shows all tasks assigned to the current user
// =============================================================================

const PRIORITY_CONFIG: Record<string, { label: string; variant: string }> = {
  [TaskPriority.URGENT]: { label: "Urgent", variant: "priority-urgent" },
  [TaskPriority.HIGH]: { label: "High", variant: "priority-high" },
  [TaskPriority.MEDIUM]: { label: "Medium", variant: "priority-medium" },
  [TaskPriority.LOW]: { label: "Low", variant: "priority-low" },
};

const STATUS_ICON: Record<string, React.ElementType> = {
  [TaskStatus.BACKLOG]: Circle,
  [TaskStatus.TODO]: Circle,
  [TaskStatus.IN_PROGRESS]: Clock,
  [TaskStatus.IN_REVIEW]: AlertCircle,
  [TaskStatus.DONE]: CheckCircle2,
};

const STATUS_COLOR: Record<string, string> = {
  [TaskStatus.BACKLOG]: "text-status-backlog",
  [TaskStatus.TODO]: "text-status-todo",
  [TaskStatus.IN_PROGRESS]: "text-status-in-progress",
  [TaskStatus.IN_REVIEW]: "text-status-in-review",
  [TaskStatus.DONE]: "text-status-done",
};

export default function TasksPage() {
  const { tasks, isLoading } = useTasks({
    status: [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
    limit: 50,
    sortBy: "dueDate",
    sortOrder: "asc",
  });

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-heading font-bold tracking-tight text-text-primary">
          My Tasks
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          All tasks assigned to you across every project
        </p>
      </div>

      {isLoading ? (
        <TasksSkeleton />
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-surface-quaternary mb-3">
              <CheckCircle2 className="h-6 w-6 text-text-quaternary" />
            </div>
            <h3 className="text-sm font-medium text-text-primary">All caught up!</h3>
            <p className="text-xs text-text-tertiary mt-1 max-w-[240px]">
              You have no pending tasks. Enjoy the calm.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            {tasks.map((task, index) => (
              <MyTaskRow
                key={task.id}
                task={task}
                showBorder={index < tasks.length - 1}
              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

function MyTaskRow({ task, showBorder }: { task: Task; showBorder: boolean }) {
  const StatusIcon = STATUS_ICON[task.status as string] ?? Circle;
  const statusColor = STATUS_COLOR[task.status as string] ?? "text-text-quaternary";
  const priorityConfig = PRIORITY_CONFIG[task.priority as string];

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5",
        "hover:bg-surface-hover transition-colors duration-fast cursor-pointer",
        showBorder && "border-b border-border-subtle",
      )}
    >
      <StatusIcon className={cn("h-4 w-4 shrink-0", statusColor)} />

      <div className="min-w-0 flex-1">
        <p className="text-sm text-text-primary truncate">{task.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {task.dueDate && (
            <span
              className={cn(
                "text-xs",
                new Date(task.dueDate) < new Date()
                  ? "text-error"
                  : "text-text-quaternary",
              )}
            >
              {formatRelativeDate(task.dueDate)}
            </span>
          )}
        </div>
      </div>

      {priorityConfig && (
        <Badge variant={priorityConfig.variant as never} size="sm">
          {priorityConfig.label}
        </Badge>
      )}
    </div>
  );
}

function TasksSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "flex items-center gap-3 px-4 py-3",
              i < 7 && "border-b border-border-subtle",
            )}
          >
            <Skeleton className="h-4 w-4 rounded-full" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3.5 w-48" />
              <Skeleton className="h-2.5 w-24" />
            </div>
            <Skeleton className="h-5 w-12 rounded-full" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

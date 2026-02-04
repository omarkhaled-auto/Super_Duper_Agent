"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import {
  Plus,
  CheckCircle2,
  Circle,
  Clock,
  ArrowRight,
  Activity,
  FolderKanban,
  AlertCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { formatRelativeDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useProjects } from "@/hooks/use-projects";
import { useTasks } from "@/hooks/use-tasks";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";
import { ProjectCard, ProjectCardSkeleton } from "@/components/projects/project-card";
import { useAuth } from "@/contexts/auth-context";

// =============================================================================
// Greeting helper
// =============================================================================

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

// =============================================================================
// Priority config for badge rendering
// =============================================================================

const PRIORITY_CONFIG: Record<string, { label: string; variant: string }> = {
  [TaskPriority.URGENT]: { label: "Urgent", variant: "priority-urgent" },
  [TaskPriority.HIGH]: { label: "High", variant: "priority-high" },
  [TaskPriority.MEDIUM]: { label: "Medium", variant: "priority-medium" },
  [TaskPriority.LOW]: { label: "Low", variant: "priority-low" },
};

// =============================================================================
// Status config for icon rendering
// =============================================================================

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

// =============================================================================
// Task grouping by due date
// =============================================================================

interface TaskGroup {
  label: string;
  tasks: Task[];
}

function groupTasksByDue(tasks: Task[]): TaskGroup[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const nextWeek = new Date(today);
  nextWeek.setDate(nextWeek.getDate() + 7);

  const overdue: Task[] = [];
  const todayTasks: Task[] = [];
  const tomorrowTasks: Task[] = [];
  const thisWeekTasks: Task[] = [];
  const later: Task[] = [];
  const noDue: Task[] = [];

  tasks.forEach((task) => {
    if (!task.dueDate) {
      noDue.push(task);
      return;
    }

    const due = new Date(task.dueDate);
    const dueDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());

    if (dueDay < today) {
      overdue.push(task);
    } else if (dueDay.getTime() === today.getTime()) {
      todayTasks.push(task);
    } else if (dueDay.getTime() === tomorrow.getTime()) {
      tomorrowTasks.push(task);
    } else if (dueDay < nextWeek) {
      thisWeekTasks.push(task);
    } else {
      later.push(task);
    }
  });

  const groups: TaskGroup[] = [];
  if (overdue.length) groups.push({ label: "Overdue", tasks: overdue });
  if (todayTasks.length) groups.push({ label: "Today", tasks: todayTasks });
  if (tomorrowTasks.length) groups.push({ label: "Tomorrow", tasks: tomorrowTasks });
  if (thisWeekTasks.length) groups.push({ label: "This Week", tasks: thisWeekTasks });
  if (later.length) groups.push({ label: "Later", tasks: later });
  if (noDue.length) groups.push({ label: "No Due Date", tasks: noDue });

  return groups;
}

// =============================================================================
// Mock activity feed (placeholder until real-time is wired)
// =============================================================================

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  target: string;
  timestamp: string;
}

const MOCK_ACTIVITY: ActivityItem[] = [
  {
    id: "1",
    user: "Omar K.",
    action: "created task",
    target: "Implement auth flow",
    timestamp: new Date(Date.now() - 25 * 60_000).toISOString(),
  },
  {
    id: "2",
    user: "Sara M.",
    action: "completed",
    target: "Design system tokens",
    timestamp: new Date(Date.now() - 2 * 3600_000).toISOString(),
  },
  {
    id: "3",
    user: "Alex R.",
    action: "commented on",
    target: "API rate limiting",
    timestamp: new Date(Date.now() - 5 * 3600_000).toISOString(),
  },
  {
    id: "4",
    user: "Omar K.",
    action: "moved",
    target: "Dashboard layout",
    timestamp: new Date(Date.now() - 24 * 3600_000).toISOString(),
  },
];

// =============================================================================
// Dashboard Page Component
// =============================================================================

export default function DashboardPage() {
  const { user } = useAuth();
  const { projects, isLoading: projectsLoading } = useProjects();
  const {
    tasks,
    isLoading: tasksLoading,
  } = useTasks({
    status: [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
    limit: 20,
    sortBy: "dueDate",
    sortOrder: "asc",
  });

  const greeting = getGreeting();
  const firstName = user?.name?.split(" ")[0] ?? "there";

  // Group tasks by due date
  const taskGroups = useMemo(() => groupTasksByDue(tasks), [tasks]);

  // Stats
  const totalTasks = tasks.length;
  const overdueTasks = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return tasks.filter(
      (t) => t.dueDate && new Date(t.dueDate) < today,
    ).length;
  }, [tasks]);

  return (
    <div className={cn(
      // Responsive padding: 16px mobile, 24px tablet, 32px desktop
      "p-4 md:p-6 lg:p-8",
      "space-y-6 md:space-y-8",
      "max-w-dashboard mx-auto",
    )}>
      {/* ============================================================
          Welcome Header
          ============================================================ */}
      <section className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-heading tracking-tight">
            {greeting}, {firstName}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {totalTasks > 0
              ? `You have ${totalTasks} active task${totalTasks !== 1 ? "s" : ""}${
                  overdueTasks > 0
                    ? ` and ${overdueTasks} overdue`
                    : ""
                }.`
              : "No active tasks right now. Time to start something new!"}
          </p>
        </div>

        <Button size="md" className="shrink-0 gap-2 self-start min-h-[44px]">
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Quick Add Task</span>
          <span className="sm:hidden">New Task</span>
        </Button>
      </section>

      {/* ============================================================
          Stats Row (compact)
          ============================================================ */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatsCard
          label="Active Tasks"
          value={tasksLoading ? null : totalTasks}
          icon={CheckCircle2}
        />
        <StatsCard
          label="Overdue"
          value={tasksLoading ? null : overdueTasks}
          icon={AlertCircle}
          accent={overdueTasks > 0 ? "destructive" : undefined}
        />
        <StatsCard
          label="Projects"
          value={projectsLoading ? null : projects.length}
          icon={FolderKanban}
        />
        <StatsCard
          label="Completed Today"
          value={tasksLoading ? null : 0}
          icon={CheckCircle2}
          accent="success"
        />
      </section>

      {/* ============================================================
          Projects Grid
          ============================================================ */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold font-heading">Projects</h2>
          <Link
            href="/dashboard"
            className="flex items-center gap-1 text-xs text-text-tertiary hover:text-text-primary transition-colors duration-fast"
          >
            View all
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {projectsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <ProjectCardSkeleton key={i} />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <EmptyState
            icon={FolderKanban}
            title="No projects yet"
            description="Create your first project to start organizing tasks."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            {projects.slice(0, 8).map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </section>

      {/* ============================================================
          Two-column: My Tasks + Activity
          ============================================================ */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 md:gap-6">
        {/* ---- My Tasks Section (full width on mobile, 3/5 on desktop) ---- */}
        <section className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold font-heading">My Tasks</h2>
            <Link
              href="/tasks"
              className="flex items-center gap-1 text-xs text-text-tertiary hover:text-text-primary transition-colors duration-fast"
            >
              View all
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {tasksLoading ? (
            <TasksSkeleton />
          ) : tasks.length === 0 ? (
            <EmptyState
              icon={CheckCircle2}
              title="All caught up!"
              description="You have no pending tasks. Enjoy the calm."
            />
          ) : (
            <Card>
              <CardContent className="p-0">
                {taskGroups.map((group, groupIndex) => (
                  <div key={group.label}>
                    {groupIndex > 0 && <Separator />}
                    <div className="px-4 py-2 bg-surface-secondary/50">
                      <span
                        className={cn(
                          "text-xs font-semibold uppercase tracking-wider",
                          group.label === "Overdue"
                            ? "text-error"
                            : "text-text-quaternary",
                        )}
                      >
                        {group.label}
                      </span>
                    </div>
                    <div>
                      {group.tasks.map((task, taskIndex) => (
                        <TaskRow
                          key={task.id}
                          task={task}
                          showBorder={taskIndex < group.tasks.length - 1}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </section>

        {/* ---- Recent Activity (2/5 width) ---- */}
        <section className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold font-heading">
              Recent Activity
            </h2>
          </div>

          <Card>
            <CardContent className="p-0">
              {MOCK_ACTIVITY.map((item, index) => (
                <div key={item.id}>
                  {index > 0 && <Separator />}
                  <div className="flex items-start gap-3 px-4 py-3">
                    <Avatar size="xs" className="mt-0.5 shrink-0">
                      <AvatarFallback>
                        {item.user
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-text-secondary">
                        <span className="font-medium text-text-primary">
                          {item.user}
                        </span>{" "}
                        {item.action}{" "}
                        <span className="font-medium text-text-primary">
                          {item.target}
                        </span>
                      </p>
                      <p className="text-xs text-text-quaternary mt-0.5">
                        {formatRelativeDate(item.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {MOCK_ACTIVITY.length === 0 && (
                <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
                  <Activity className="h-8 w-8 text-text-quaternary mb-2" />
                  <p className="text-sm text-text-tertiary">
                    No recent activity
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

/** Compact stats card */
function StatsCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number | null;
  icon: React.ElementType;
  accent?: "destructive" | "success";
}) {
  const valueColor =
    accent === "destructive"
      ? "text-error"
      : accent === "success"
        ? "text-success"
        : "text-text-primary";

  return (
    <Card className="p-3">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-surface-quaternary">
          <Icon className="h-4 w-4 text-text-tertiary" />
        </div>
        <div className="min-w-0">
          {value === null ? (
            <Skeleton className="h-5 w-8 mb-0.5" />
          ) : (
            <p className={cn("text-lg font-bold font-heading", valueColor)}>
              {value}
            </p>
          )}
          <p className="text-[10px] text-text-quaternary truncate">{label}</p>
        </div>
      </div>
    </Card>
  );
}

/** Single task row */
function TaskRow({
  task,
  showBorder,
}: {
  task: Task;
  showBorder: boolean;
}) {
  const StatusIcon = STATUS_ICON[task.status] ?? Circle;
  const statusColor = STATUS_COLOR[task.status] ?? "text-text-quaternary";
  const priorityConfig = PRIORITY_CONFIG[task.priority];

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5",
        // Minimum 44px touch target on mobile
        "min-h-[44px]",
        "hover:bg-surface-hover motion-safe:transition-colors duration-fast cursor-pointer",
        showBorder && "border-b border-border-subtle",
      )}
    >
      <StatusIcon className={cn("h-4 w-4 shrink-0", statusColor)} />

      <div className="min-w-0 flex-1">
        <p className="text-sm text-text-primary truncate">{task.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {task.projectName && (
            <span
              className="text-xs text-text-quaternary truncate max-w-[120px]"
            >
              {task.projectName}
            </span>
          )}
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
        <Badge
          variant={priorityConfig.variant as never}
          size="sm"
        >
          {priorityConfig.label}
        </Badge>
      )}
    </div>
  );
}

/** Loading skeleton for the tasks section */
function TasksSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "flex items-center gap-3 px-4 py-3",
              i < 4 && "border-b border-border-subtle",
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

/** Empty state placeholder */
function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-surface-quaternary mb-3">
          <Icon className="h-6 w-6 text-text-quaternary" />
        </div>
        <h3 className="text-sm font-medium text-text-primary">{title}</h3>
        <p className="text-xs text-text-tertiary mt-1 max-w-[240px]">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}

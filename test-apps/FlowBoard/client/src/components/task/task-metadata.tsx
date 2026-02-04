"use client";

import * as React from "react";
import {
  Circle,
  CircleDot,
  Timer,
  CheckCircle2,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Minus,
  CalendarDays,
  UserCircle2,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { TaskStatus, TaskPriority } from "@/types";
import type { Task, UserProfile, ProjectMember } from "@/types";

// =============================================================================
// Task Metadata Section
//
// Displays and allows inline editing of:
//   - Status (dropdown with colored icons)
//   - Priority (dropdown with colored badges)
//   - Assignee (avatar with member selector)
//   - Due date (native date input, styled)
//
// Each change fires the updateField callback immediately (optimistic).
// =============================================================================

// ---------------------------------------------------------------------------
// Status config
// ---------------------------------------------------------------------------

interface StatusConfig {
  label: string;
  icon: React.ElementType;
  className: string;
  dotClassName: string;
}

const STATUS_CONFIG: Record<TaskStatus, StatusConfig> = {
  [TaskStatus.BACKLOG]: {
    label: "Backlog",
    icon: Circle,
    className: "text-text-tertiary",
    dotClassName: "text-text-tertiary",
  },
  [TaskStatus.TODO]: {
    label: "Todo",
    icon: CircleDot,
    className: "text-text-secondary",
    dotClassName: "text-blue-400",
  },
  [TaskStatus.IN_PROGRESS]: {
    label: "In Progress",
    icon: Timer,
    className: "text-yellow-500",
    dotClassName: "text-yellow-500",
  },
  [TaskStatus.IN_REVIEW]: {
    label: "In Review",
    icon: AlertTriangle,
    className: "text-purple-400",
    dotClassName: "text-purple-400",
  },
  [TaskStatus.DONE]: {
    label: "Done",
    icon: CheckCircle2,
    className: "text-green-500",
    dotClassName: "text-green-500",
  },
};

// ---------------------------------------------------------------------------
// Priority config
// ---------------------------------------------------------------------------

interface PriorityConfig {
  label: string;
  icon: React.ElementType;
  variant: "priority-urgent" | "priority-high" | "priority-medium" | "priority-low" | "default";
  className: string;
}

const PRIORITY_CONFIG: Record<TaskPriority, PriorityConfig> = {
  [TaskPriority.URGENT]: {
    label: "Urgent",
    icon: AlertTriangle,
    variant: "priority-urgent",
    className: "text-urgent",
  },
  [TaskPriority.HIGH]: {
    label: "High",
    icon: ArrowUp,
    variant: "priority-high",
    className: "text-high",
  },
  [TaskPriority.MEDIUM]: {
    label: "Medium",
    icon: Minus,
    variant: "priority-medium",
    className: "text-medium",
  },
  [TaskPriority.LOW]: {
    label: "Low",
    icon: ArrowDown,
    variant: "priority-low",
    className: "text-low",
  },
};

// ---------------------------------------------------------------------------
// Helper: get initials from a name
// ---------------------------------------------------------------------------

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

// ---------------------------------------------------------------------------
// Component Props
// ---------------------------------------------------------------------------

interface TaskMetadataProps {
  task: Task;
  members: ProjectMember[];
  updateField: (field: string, value: unknown) => Promise<void>;
}

// ---------------------------------------------------------------------------
// TaskMetadata Component
// ---------------------------------------------------------------------------

export function TaskMetadata({
  task,
  members,
  updateField,
}: TaskMetadataProps) {
  return (
    <div className="space-y-3">
      {/* Status */}
      <MetadataRow label="Status">
        <Select
          value={task.status}
          onValueChange={(value) => updateField("status", value)}
        >
          <SelectTrigger className="h-8 w-[160px] bg-transparent border-transparent hover:bg-surface-hover transition-colors text-sm">
            <SelectValue>
              <StatusDisplay status={task.status} />
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {Object.values(TaskStatus).map((status) => {
              const config = STATUS_CONFIG[status];
              if (!config) return null;
              const Icon = config.icon;
              return (
                <SelectItem key={status} value={status}>
                  <span className="flex items-center gap-2">
                    <Icon className={cn("h-3.5 w-3.5", config.className)} />
                    <span>{config.label}</span>
                  </span>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </MetadataRow>

      {/* Priority */}
      <MetadataRow label="Priority">
        <Select
          value={task.priority}
          onValueChange={(value) => updateField("priority", value)}
        >
          <SelectTrigger className="h-8 w-[160px] bg-transparent border-transparent hover:bg-surface-hover transition-colors text-sm">
            <SelectValue>
              <PriorityDisplay priority={task.priority} />
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {Object.values(TaskPriority).map((priority) => {
              const config = PRIORITY_CONFIG[priority];
              if (!config) return null;
              const Icon = config.icon;
              return (
                <SelectItem key={priority} value={priority}>
                  <span className="flex items-center gap-2">
                    <Icon className={cn("h-3.5 w-3.5", config.className)} />
                    <span>{config.label}</span>
                  </span>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </MetadataRow>

      {/* Assignee */}
      <MetadataRow label="Assignee">
        <Select
          value={task.assigneeId ?? "__unassigned__"}
          onValueChange={(value) =>
            updateField(
              "assigneeId",
              value === "__unassigned__" ? null : value,
            )
          }
        >
          <SelectTrigger className="h-8 w-[200px] bg-transparent border-transparent hover:bg-surface-hover transition-colors text-sm">
            <SelectValue>
              <AssigneeDisplay assignee={task.assignee} />
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__unassigned__">
              <span className="flex items-center gap-2 text-text-tertiary">
                <UserCircle2 className="h-4 w-4" />
                <span>Unassigned</span>
              </span>
            </SelectItem>
            {members.map((member) => (
              <SelectItem key={member.user.id} value={member.user.id}>
                <span className="flex items-center gap-2">
                  <Avatar size="xs">
                    {member.user.avatarUrl && (
                      <AvatarImage
                        src={member.user.avatarUrl}
                        alt={member.user.name}
                      />
                    )}
                    <AvatarFallback>
                      {getInitials(member.user.name)}
                    </AvatarFallback>
                  </Avatar>
                  <span>{member.user.name}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </MetadataRow>

      {/* Due Date */}
      <MetadataRow label="Due date">
        <div className="relative">
          <CalendarDays className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary pointer-events-none" />
          <Input
            type="date"
            inputSize="sm"
            className={cn(
              "w-[170px] pl-8 bg-transparent border-transparent",
              "hover:bg-surface-hover transition-colors",
              "text-sm cursor-pointer",
              "[&::-webkit-calendar-picker-indicator]:opacity-0 [&::-webkit-calendar-picker-indicator]:absolute [&::-webkit-calendar-picker-indicator]:inset-0 [&::-webkit-calendar-picker-indicator]:w-full [&::-webkit-calendar-picker-indicator]:cursor-pointer",
              !task.dueDate && "text-text-tertiary",
            )}
            value={task.dueDate ? task.dueDate.split("T")[0] : ""}
            onChange={(e) => {
              const val = e.target.value;
              updateField("dueDate", val || null);
            }}
            placeholder="No due date"
          />
        </div>
      </MetadataRow>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Internal helper components
// ---------------------------------------------------------------------------

function MetadataRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-medium text-text-tertiary w-[80px] shrink-0 select-none">
        {label}
      </span>
      {children}
    </div>
  );
}

function StatusDisplay({ status }: { status: TaskStatus }) {
  const config = STATUS_CONFIG[status];
  if (!config) return <span className="text-text-tertiary">Unknown</span>;
  const Icon = config.icon;
  return (
    <span className="flex items-center gap-2">
      <Icon className={cn("h-3.5 w-3.5", config.className)} />
      <span>{config.label}</span>
    </span>
  );
}

function PriorityDisplay({ priority }: { priority: TaskPriority }) {
  const config = PRIORITY_CONFIG[priority];
  if (!config) return <span className="text-text-tertiary">None</span>;
  const Icon = config.icon;
  return (
    <span className="flex items-center gap-2">
      <Icon className={cn("h-3.5 w-3.5", config.className)} />
      <span>{config.label}</span>
    </span>
  );
}

function AssigneeDisplay({ assignee }: { assignee: UserProfile | null }) {
  if (!assignee) {
    return (
      <span className="flex items-center gap-2 text-text-tertiary">
        <UserCircle2 className="h-4 w-4" />
        <span>Unassigned</span>
      </span>
    );
  }
  return (
    <span className="flex items-center gap-2">
      <Avatar size="xs">
        {assignee.avatarUrl && (
          <AvatarImage src={assignee.avatarUrl} alt={assignee.name} />
        )}
        <AvatarFallback>{getInitials(assignee.name)}</AvatarFallback>
      </Avatar>
      <span>{assignee.name}</span>
    </span>
  );
}

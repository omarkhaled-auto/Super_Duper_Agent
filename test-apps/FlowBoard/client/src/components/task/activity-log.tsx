"use client";

import * as React from "react";
import { useEffect } from "react";
import {
  Plus,
  Pencil,
  Trash2,
  ArrowRightLeft,
  UserPlus,
  UserMinus,
  MessageSquarePlus,
  Tag,
  XCircle,
  CalendarDays,
  Signal,
  CheckSquare,
  Square,
  XSquare,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatRelativeDate } from "@/lib/utils";
import type { ActivityEvent } from "@/types";

// =============================================================================
// Activity Log — chronological list of task events
//
// Each entry shows:
//   - Icon per action type
//   - Actor avatar + name
//   - Action description
//   - Relative timestamp
//
// The activity type is matched by string value rather than enum reference
// to handle both the base and extended ActivityType enums gracefully.
// =============================================================================

// ---------------------------------------------------------------------------
// Activity type configuration
// ---------------------------------------------------------------------------

interface ActivityConfig {
  icon: React.ElementType;
  label: (metadata: Record<string, unknown>) => string;
  iconClassName: string;
}

/** Map activity type string to display configuration. */
function getActivityConfig(type: string): ActivityConfig {
  switch (type) {
    case "TASK_CREATED":
      return {
        icon: Plus,
        label: () => "created this task",
        iconClassName: "text-green-500 bg-green-500/10",
      };
    case "TASK_UPDATED":
      return {
        icon: Pencil,
        label: (m) => {
          const field = m.field as string | undefined;
          const from = m.from as string | undefined;
          const to = m.to as string | undefined;
          if (field && from && to) {
            return `changed ${formatFieldName(field)} from "${formatValue(from)}" to "${formatValue(to)}"`;
          }
          if (field && to) {
            return `set ${formatFieldName(field)} to "${formatValue(to)}"`;
          }
          return "updated this task";
        },
        iconClassName: "text-blue-400 bg-blue-400/10",
      };
    case "TASK_DELETED":
      return {
        icon: Trash2,
        label: () => "deleted this task",
        iconClassName: "text-destructive bg-destructive/10",
      };
    case "TASK_MOVED":
      return {
        icon: ArrowRightLeft,
        label: (m) => {
          const from = m.fromStatus as string | undefined;
          const to = m.toStatus as string | undefined;
          if (from && to) {
            return `moved from ${formatValue(from)} to ${formatValue(to)}`;
          }
          return "moved this task";
        },
        iconClassName: "text-yellow-500 bg-yellow-500/10",
      };
    case "TASK_ASSIGNED":
      return {
        icon: UserPlus,
        label: (m) => {
          const assignee = m.assigneeName as string | undefined;
          if (assignee) {
            return `assigned to ${assignee}`;
          }
          return "assigned this task";
        },
        iconClassName: "text-violet-400 bg-violet-400/10",
      };
    case "TASK_UNASSIGNED":
      return {
        icon: UserMinus,
        label: () => "unassigned this task",
        iconClassName: "text-text-tertiary bg-surface-tertiary",
      };
    case "TASK_COMMENT_ADDED":
      return {
        icon: MessageSquarePlus,
        label: () => "added a comment",
        iconClassName: "text-cyan-400 bg-cyan-400/10",
      };
    case "TASK_COMMENT_UPDATED":
      return {
        icon: Pencil,
        label: () => "edited a comment",
        iconClassName: "text-cyan-300 bg-cyan-300/10",
      };
    case "TASK_COMMENT_DELETED":
      return {
        icon: Trash2,
        label: () => "deleted a comment",
        iconClassName: "text-text-tertiary bg-surface-tertiary",
      };
    case "TASK_LABEL_ADDED":
      return {
        icon: Tag,
        label: (m) => {
          const name = m.labelName as string | undefined;
          return name ? `added label "${name}"` : "added a label";
        },
        iconClassName: "text-pink-400 bg-pink-400/10",
      };
    case "TASK_LABEL_REMOVED":
      return {
        icon: XCircle,
        label: (m) => {
          const name = m.labelName as string | undefined;
          return name ? `removed label "${name}"` : "removed a label";
        },
        iconClassName: "text-text-tertiary bg-surface-tertiary",
      };
    case "TASK_DUE_DATE_CHANGED":
      return {
        icon: CalendarDays,
        label: (m) => {
          const to = m.to as string | undefined;
          if (to) return `set due date to ${to}`;
          return "changed the due date";
        },
        iconClassName: "text-orange-400 bg-orange-400/10",
      };
    case "TASK_PRIORITY_CHANGED":
      return {
        icon: Signal,
        label: (m) => {
          const from = m.from as string | undefined;
          const to = m.to as string | undefined;
          if (from && to) {
            return `changed priority from ${formatValue(from)} to ${formatValue(to)}`;
          }
          return "changed the priority";
        },
        iconClassName: "text-amber-400 bg-amber-400/10",
      };
    case "SUBTASK_CREATED":
      return {
        icon: Plus,
        label: (m) => {
          const title = m.subtaskTitle as string | undefined;
          return title ? `added sub-task "${title}"` : "added a sub-task";
        },
        iconClassName: "text-green-400 bg-green-400/10",
      };
    case "SUBTASK_COMPLETED":
      return {
        icon: CheckSquare,
        label: (m) => {
          const title = m.subtaskTitle as string | undefined;
          return title
            ? `completed sub-task "${title}"`
            : "completed a sub-task";
        },
        iconClassName: "text-green-500 bg-green-500/10",
      };
    case "SUBTASK_UNCOMPLETED":
      return {
        icon: Square,
        label: (m) => {
          const title = m.subtaskTitle as string | undefined;
          return title
            ? `uncompleted sub-task "${title}"`
            : "uncompleted a sub-task";
        },
        iconClassName: "text-text-tertiary bg-surface-tertiary",
      };
    case "SUBTASK_DELETED":
      return {
        icon: XSquare,
        label: (m) => {
          const title = m.subtaskTitle as string | undefined;
          return title
            ? `deleted sub-task "${title}"`
            : "deleted a sub-task";
        },
        iconClassName: "text-destructive bg-destructive/10",
      };
    default:
      return {
        icon: Activity,
        label: () => "performed an action",
        iconClassName: "text-text-tertiary bg-surface-tertiary",
      };
  }
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatFieldName(field: string): string {
  return field
    .replace(/([A-Z])/g, " $1")
    .replace(/_/g, " ")
    .toLowerCase()
    .trim();
}

function formatValue(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ActivityLogProps {
  activities: ActivityEvent[];
  onMount?: () => void;
}

export function ActivityLog({ activities, onMount }: ActivityLogProps) {
  // Fetch activities on mount
  useEffect(() => {
    onMount?.();
  }, [onMount]);

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Activity className="h-8 w-8 text-text-quaternary mx-auto mb-2" />
        <p className="text-sm text-text-quaternary">No activity yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {activities.map((activity, index) => {
        const config = getActivityConfig(activity.type);
        const Icon = config.icon;
        const isLast = index === activities.length - 1;

        return (
          <div key={activity.id} className="flex gap-3 relative">
            {/* Timeline connector */}
            {!isLast && (
              <div className="absolute left-[13px] top-[28px] bottom-0 w-px bg-border-subtle" />
            )}

            {/* Icon */}
            <div
              className={cn(
                "h-[26px] w-[26px] rounded-full flex items-center justify-center shrink-0 relative z-10",
                config.iconClassName,
              )}
            >
              <Icon className="h-3 w-3" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pb-4">
              <p className="text-sm leading-snug">
                <span className="font-medium text-text-primary">
                  {activity.actor.name}
                </span>{" "}
                <span className="text-text-secondary">
                  {config.label(activity.metadata)}
                </span>
              </p>
              <p className="text-[11px] text-text-quaternary mt-0.5">
                {formatRelativeDate(activity.createdAt)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

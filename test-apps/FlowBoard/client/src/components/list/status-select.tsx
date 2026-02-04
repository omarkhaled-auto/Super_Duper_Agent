"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { TaskStatus } from "@/types";

// =============================================================================
// StatusSelect -- Compact inline dropdown for changing task status in a table
// cell.  Renders a colored dot + label.  On change fires an optimistic update
// via the provided callback.
// =============================================================================

interface StatusOption {
  value: TaskStatus;
  label: string;
  /** Tailwind bg class for the colored dot. */
  dotClass: string;
}

const STATUS_OPTIONS: StatusOption[] = [
  { value: TaskStatus.BACKLOG, label: "Backlog", dotClass: "bg-status-backlog" },
  { value: TaskStatus.TODO, label: "Todo", dotClass: "bg-status-todo" },
  {
    value: TaskStatus.IN_PROGRESS,
    label: "In Progress",
    dotClass: "bg-status-in-progress",
  },
  {
    value: TaskStatus.IN_REVIEW,
    label: "In Review",
    dotClass: "bg-status-in-review",
  },
  { value: TaskStatus.DONE, label: "Done", dotClass: "bg-status-done" },
];

const STATUS_MAP = Object.fromEntries(
  STATUS_OPTIONS.map((o) => [o.value, o]),
) as Record<TaskStatus, StatusOption>;

interface StatusSelectProps {
  value: TaskStatus;
  onChange: (status: TaskStatus) => void;
  disabled?: boolean;
  className?: string;
}

export function StatusSelect({
  value,
  onChange,
  disabled,
  className,
}: StatusSelectProps) {
  const current = STATUS_MAP[value];

  return (
    <Select
      value={value}
      onValueChange={(v) => onChange(v as TaskStatus)}
      disabled={disabled}
    >
      <SelectTrigger
        className={cn(
          "h-7 w-auto min-w-[7rem] gap-1.5 border-transparent bg-transparent px-2 text-xs font-body",
          "hover:bg-surface-hover hover:border-border",
          "focus:ring-1 focus:ring-ring focus:ring-offset-0",
          "transition-colors duration-fast",
          "[&>svg]:h-3 [&>svg]:w-3",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <SelectValue>
          <span className="inline-flex items-center gap-1.5">
            <span
              className={cn(
                "h-2 w-2 shrink-0 rounded-full",
                current?.dotClass,
              )}
              aria-hidden="true"
            />
            <span className="truncate">{current?.label ?? value}</span>
          </span>
        </SelectValue>
      </SelectTrigger>

      <SelectContent align="start" className="min-w-[10rem]">
        {STATUS_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value} className="text-xs">
            <span className="inline-flex items-center gap-1.5">
              <span
                className={cn("h-2 w-2 shrink-0 rounded-full", opt.dotClass)}
                aria-hidden="true"
              />
              {opt.label}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export { STATUS_OPTIONS, STATUS_MAP };

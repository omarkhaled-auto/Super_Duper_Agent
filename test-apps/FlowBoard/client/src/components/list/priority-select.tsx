"use client";

import * as React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { TaskPriority } from "@/types";

// =============================================================================
// PrioritySelect -- Compact inline dropdown for changing task priority in a
// table cell.  Shows a colored badge matching the priority level.  On change,
// fires an optimistic update via the provided callback.
// =============================================================================

interface PriorityOption {
  value: TaskPriority;
  label: string;
  /** Badge variant matching the design system. */
  badgeVariant:
    | "priority-urgent"
    | "priority-high"
    | "priority-medium"
    | "priority-low"
    | "default";
}

const PRIORITY_OPTIONS: PriorityOption[] = [
  { value: TaskPriority.URGENT, label: "Urgent", badgeVariant: "priority-urgent" },
  { value: TaskPriority.HIGH, label: "High", badgeVariant: "priority-high" },
  { value: TaskPriority.MEDIUM, label: "Medium", badgeVariant: "priority-medium" },
  { value: TaskPriority.LOW, label: "Low", badgeVariant: "priority-low" },
];

const PRIORITY_MAP = Object.fromEntries(
  PRIORITY_OPTIONS.map((o) => [o.value, o]),
) as Record<TaskPriority, PriorityOption>;

interface PrioritySelectProps {
  value: TaskPriority;
  onChange: (priority: TaskPriority) => void;
  disabled?: boolean;
  className?: string;
}

export function PrioritySelect({
  value,
  onChange,
  disabled,
  className,
}: PrioritySelectProps) {
  const current = PRIORITY_MAP[value];

  return (
    <Select
      value={value}
      onValueChange={(v) => onChange(v as TaskPriority)}
      disabled={disabled}
    >
      <SelectTrigger
        className={cn(
          "h-7 w-auto min-w-[5.5rem] gap-1.5 border-transparent bg-transparent px-1.5 text-xs font-body",
          "hover:bg-surface-hover hover:border-border",
          "focus:ring-1 focus:ring-ring focus:ring-offset-0",
          "transition-colors duration-fast",
          "[&>svg]:h-3 [&>svg]:w-3",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <SelectValue>
          <Badge variant={current?.badgeVariant ?? "default"} size="sm">
            {current?.label ?? value}
          </Badge>
        </SelectValue>
      </SelectTrigger>

      <SelectContent align="start" className="min-w-[9rem]">
        {PRIORITY_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value} className="text-xs">
            <Badge variant={opt.badgeVariant} size="sm">
              {opt.label}
            </Badge>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export { PRIORITY_OPTIONS, PRIORITY_MAP };

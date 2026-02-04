"use client";

import React from "react";
import {
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  FileText,
  FolderKanban,
  ArrowRight,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import type {
  SearchResultItem as SearchResultItemType,
  SearchTaskResult,
  SearchProjectResult,
  SearchMemberResult,
} from "@/hooks/use-search";

// =============================================================================
// SearchResultItem — Individual result row in the command palette
//
// Renders a different layout per result type (task / project / member).
// Highlights the row when selected via keyboard navigation.
// =============================================================================

interface SearchResultItemProps {
  item: SearchResultItemType;
  isSelected: boolean;
  onClick: () => void;
  onMouseEnter: () => void;
}

// ---------------------------------------------------------------------------
// Status icon mapping
// ---------------------------------------------------------------------------

const STATUS_ICONS: Record<string, React.ReactNode> = {
  BACKLOG: <Circle className="h-3.5 w-3.5 text-text-quaternary" />,
  TODO: <Circle className="h-3.5 w-3.5 text-text-tertiary" />,
  IN_PROGRESS: <Clock className="h-3.5 w-3.5 text-blue-400" />,
  IN_REVIEW: <AlertCircle className="h-3.5 w-3.5 text-amber-400" />,
  DONE: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />,
};

const STATUS_LABELS: Record<string, string> = {
  BACKLOG: "Backlog",
  TODO: "Todo",
  IN_PROGRESS: "In Progress",
  IN_REVIEW: "In Review",
  DONE: "Done",
};

const STATUS_BADGE_VARIANT: Record<string, "default" | "status" | "outline"> = {
  BACKLOG: "default",
  TODO: "default",
  IN_PROGRESS: "status",
  IN_REVIEW: "status",
  DONE: "status",
};

// ---------------------------------------------------------------------------
// Task result row
// ---------------------------------------------------------------------------

function TaskResultRow({ task }: { task: SearchTaskResult }) {
  return (
    <div className="flex items-center gap-3 min-w-0 w-full">
      {/* Status icon */}
      <span className="shrink-0">
        {STATUS_ICONS[task.status] ?? (
          <FileText className="h-3.5 w-3.5 text-text-quaternary" />
        )}
      </span>

      {/* Task title */}
      <span className="truncate text-sm text-text-primary font-medium flex-1 min-w-0">
        {task.title}
      </span>

      {/* Status badge */}
      <Badge
        variant={STATUS_BADGE_VARIANT[task.status] ?? "default"}
        size="sm"
        className="shrink-0"
      >
        {STATUS_LABELS[task.status] ?? task.status}
      </Badge>

      {/* Project name */}
      <div className="hidden sm:flex items-center gap-1.5 shrink-0 ml-1">
        {task.projectColor && (
          <span
            className="h-2 w-2 rounded-full shrink-0"
            style={{ backgroundColor: task.projectColor }}
          />
        )}
        <span className="text-xs text-text-tertiary truncate max-w-[120px]">
          {task.projectName}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Project result row
// ---------------------------------------------------------------------------

function ProjectResultRow({ project }: { project: SearchProjectResult }) {
  return (
    <div className="flex items-center gap-3 min-w-0 w-full">
      {/* Color dot / icon */}
      <span className="shrink-0 flex items-center justify-center h-6 w-6 rounded-md bg-surface-tertiary">
        {project.icon ? (
          <span className="text-sm">{project.icon}</span>
        ) : (
          <FolderKanban className="h-3.5 w-3.5 text-text-tertiary" />
        )}
      </span>

      {/* Project name */}
      <span className="truncate text-sm text-text-primary font-medium flex-1 min-w-0">
        {project.name}
      </span>

      {/* Color swatch */}
      {project.color && (
        <span
          className="h-3 w-3 rounded-full shrink-0 ring-1 ring-white/10"
          style={{ backgroundColor: project.color }}
        />
      )}

      {/* Navigate hint */}
      <ArrowRight className="h-3.5 w-3.5 text-text-quaternary shrink-0" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Member result row
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

function MemberResultRow({ member }: { member: SearchMemberResult }) {
  return (
    <div className="flex items-center gap-3 min-w-0 w-full">
      {/* Avatar */}
      <Avatar size="xs" className="shrink-0">
        {member.avatarUrl && <AvatarImage src={member.avatarUrl} alt={member.name} />}
        <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
      </Avatar>

      {/* Name and email */}
      <div className="flex flex-col min-w-0 flex-1">
        <span className="truncate text-sm text-text-primary font-medium">
          {member.name}
        </span>
        <span className="truncate text-xs text-text-tertiary">
          {member.email}
        </span>
      </div>

      {/* Navigate hint */}
      <ArrowRight className="h-3.5 w-3.5 text-text-quaternary shrink-0" />
    </div>
  );
}

// =============================================================================
// Exported Component
// =============================================================================

export const SearchResultItem = React.memo(function SearchResultItem({
  item,
  isSelected,
  onClick,
  onMouseEnter,
}: SearchResultItemProps) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center px-3 rounded-lg",
        // 44px min touch target on mobile, smaller on desktop
        "py-3 md:py-2 min-h-[44px] md:min-h-0",
        "text-left motion-safe:transition-colors duration-75 cursor-pointer",
        "outline-none focus-visible:outline-none",
        isSelected
          ? "bg-surface-hover text-text-primary"
          : "text-text-secondary hover:bg-surface-hover/50",
      )}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      role="option"
      aria-selected={isSelected}
      tabIndex={-1}
    >
      {item.type === "task" && <TaskResultRow task={item.data as SearchTaskResult} />}
      {item.type === "project" && (
        <ProjectResultRow project={item.data as SearchProjectResult} />
      )}
      {item.type === "member" && (
        <MemberResultRow member={item.data as SearchMemberResult} />
      )}
    </button>
  );
});

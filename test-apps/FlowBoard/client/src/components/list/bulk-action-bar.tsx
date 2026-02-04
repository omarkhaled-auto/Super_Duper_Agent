"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, Trash2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { STATUS_OPTIONS } from "@/components/list/status-select";
import { PRIORITY_OPTIONS } from "@/components/list/priority-select";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// BulkActionBar -- Slides up from the bottom when 1+ rows are selected.
//
// Actions:
//   - Change Status (dropdown)
//   - Change Priority (dropdown)
//   - Delete (with confirmation)
//   - Deselect All
// =============================================================================

interface BulkActionBarProps {
  selectedCount: number;
  onBulkStatus: (status: TaskStatus) => void;
  onBulkPriority: (priority: TaskPriority) => void;
  onBulkDelete: () => void;
  onDeselectAll: () => void;
  isProcessing?: boolean;
  className?: string;
}

export function BulkActionBar({
  selectedCount,
  onBulkStatus,
  onBulkPriority,
  onBulkDelete,
  onDeselectAll,
  isProcessing = false,
  className,
}: BulkActionBarProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);

  // Reset delete confirm when selection changes
  React.useEffect(() => {
    setShowDeleteConfirm(false);
  }, [selectedCount]);

  if (selectedCount === 0) return null;

  return (
    <div
      className={cn(
        "fixed bottom-0 left-0 right-0 z-sticky",
        "animate-in slide-in-from-bottom-4 duration-200 fill-mode-forwards",
        className,
      )}
    >
      <div
        className={cn(
          "mx-auto max-w-4xl",
          "mx-4 sm:mx-auto mb-4 sm:mb-6",
          "flex items-center justify-between gap-3",
          "rounded-xl border border-border bg-surface-elevated px-4 py-3",
          "shadow-xl backdrop-blur-sm",
        )}
      >
        {/* ---- Left: count + deselect ---- */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-text-primary tabular-nums">
            {selectedCount} selected
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-text-tertiary"
            onClick={onDeselectAll}
            disabled={isProcessing}
          >
            <X className="mr-1 h-3 w-3" />
            Deselect
          </Button>
        </div>

        {/* ---- Right: action buttons ---- */}
        <div className="flex items-center gap-2">
          {/* Status change */}
          <Select
            onValueChange={(v) => onBulkStatus(v as TaskStatus)}
            disabled={isProcessing}
          >
            <SelectTrigger className="h-8 w-auto min-w-[7.5rem] gap-1.5 border-border bg-transparent px-3 text-xs [&>svg]:h-3 [&>svg]:w-3">
              <SelectValue placeholder="Set status" />
            </SelectTrigger>
            <SelectContent align="end" className="min-w-[10rem]">
              {STATUS_OPTIONS.map((opt) => (
                <SelectItem
                  key={opt.value}
                  value={opt.value}
                  className="text-xs"
                >
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className={cn(
                        "h-2 w-2 shrink-0 rounded-full",
                        opt.dotClass,
                      )}
                      aria-hidden="true"
                    />
                    {opt.label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Priority change */}
          <Select
            onValueChange={(v) => onBulkPriority(v as TaskPriority)}
            disabled={isProcessing}
          >
            <SelectTrigger className="h-8 w-auto min-w-[7.5rem] gap-1.5 border-border bg-transparent px-3 text-xs [&>svg]:h-3 [&>svg]:w-3">
              <SelectValue placeholder="Set priority" />
            </SelectTrigger>
            <SelectContent align="end" className="min-w-[9rem]">
              {PRIORITY_OPTIONS.map((opt) => (
                <SelectItem
                  key={opt.value}
                  value={opt.value}
                  className="text-xs"
                >
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Delete */}
          {showDeleteConfirm ? (
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-warning shrink-0" />
              <span className="text-xs text-warning whitespace-nowrap">
                Delete {selectedCount}?
              </span>
              <Button
                variant="destructive"
                size="sm"
                className="h-7 text-xs px-2"
                onClick={() => {
                  onBulkDelete();
                  setShowDeleteConfirm(false);
                }}
                disabled={isProcessing}
                loading={isProcessing}
              >
                Confirm
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs px-2"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isProcessing}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 text-xs text-error hover:text-error hover:bg-error-muted"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={isProcessing}
            >
              <Trash2 className="mr-1 h-3.5 w-3.5" />
              Delete
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

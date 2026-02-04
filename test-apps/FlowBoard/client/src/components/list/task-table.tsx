"use client";

import * as React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { TaskRow } from "@/components/list/task-row";
import { TablePagination } from "@/components/list/table-pagination";
import { BulkActionBar } from "@/components/list/bulk-action-bar";
import { TableSkeleton } from "@/components/list/table-skeleton";
import { ArrowUp, ArrowDown, ListChecks } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";
import type { TableSort, SortField } from "@/hooks/use-table-tasks";

// =============================================================================
// TaskTable -- Main table component for the list view.
//
// Features:
//   - Sticky header row
//   - Clickable column headers with sort indicator arrows
//   - Multi-row selection with select-all checkbox
//   - Responsive horizontal scroll on small screens
//   - Delegates row rendering to TaskRow
//   - Pagination bar at bottom
//   - Bulk action bar slides in when items are selected
//
// Responsive behavior:
//   Mobile (<768px): Hide assignee + created columns; show title, status, priority
//   Tablet (768-1023px): Hide created column
//   Desktop (1024px+): Show all columns
// =============================================================================

// ---------------------------------------------------------------------------
// Column definitions
// ---------------------------------------------------------------------------

interface ColumnDef {
  key: SortField | "checkbox";
  label: string;
  /** If true, this column is sortable. */
  sortable: boolean;
  /** Tailwind width class. */
  width: string;
  /** Text alignment. */
  align?: "left" | "center" | "right";
  /** Responsive visibility class -- hides column on smaller breakpoints */
  responsiveClass?: string;
}

const COLUMNS: ColumnDef[] = [
  { key: "checkbox", label: "", sortable: false, width: "w-10", align: "center" },
  { key: "title", label: "Title", sortable: true, width: "w-[30%]", align: "left" },
  { key: "status", label: "Status", sortable: true, width: "w-[14%]", align: "left" },
  { key: "priority", label: "Priority", sortable: true, width: "w-[12%]", align: "left" },
  // Hidden on mobile (<768px), visible on tablet+
  { key: "assignee", label: "Assignee", sortable: true, width: "w-[16%]", align: "left", responsiveClass: "hidden md:table-cell" },
  { key: "dueDate", label: "Due Date", sortable: true, width: "w-[14%]", align: "left" },
  // Hidden on mobile + tablet (<1024px), visible on desktop
  { key: "createdAt", label: "Created", sortable: true, width: "w-[14%]", align: "left", responsiveClass: "hidden lg:table-cell" },
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface TaskTableProps {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
  sort: TableSort;
  isLoading: boolean;
  selectedIds: Set<string>;
  onSortChange: (sort: TableSort) => void;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  onToggleSelect: (taskId: string) => void;
  onToggleSelectAll: () => void;
  onClearSelection: () => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onPriorityChange: (taskId: string, priority: TaskPriority) => void;
  onBulkAction: (
    action: "status" | "priority" | "delete",
    value?: string,
  ) => Promise<void>;
  onRowClick?: (taskId: string) => void;
}

// ---------------------------------------------------------------------------
// Sort header helper
// ---------------------------------------------------------------------------

function SortIndicator({
  field,
  currentSort,
}: {
  field: SortField;
  currentSort: TableSort;
}) {
  if (currentSort.field !== field) return null;

  return currentSort.order === "asc" ? (
    <ArrowUp className="h-3 w-3 text-violet shrink-0" />
  ) : (
    <ArrowDown className="h-3 w-3 text-violet shrink-0" />
  );
}

// =============================================================================
// Component
// =============================================================================

export function TaskTable({
  tasks,
  total,
  page,
  limit,
  sort,
  isLoading,
  selectedIds,
  onSortChange,
  onPageChange,
  onLimitChange,
  onToggleSelect,
  onToggleSelectAll,
  onClearSelection,
  onStatusChange,
  onPriorityChange,
  onBulkAction,
  onRowClick,
}: TaskTableProps) {
  const [isBulkProcessing, setIsBulkProcessing] = React.useState(false);

  // Check if all tasks on this page are selected
  const allPageSelected =
    tasks.length > 0 && tasks.every((t) => selectedIds.has(t.id));
  const somePageSelected =
    tasks.some((t) => selectedIds.has(t.id)) && !allPageSelected;

  // ---- Sort handler ---- //
  const handleSort = React.useCallback(
    (field: SortField) => {
      if (sort.field === field) {
        // Toggle order
        onSortChange({
          field,
          order: sort.order === "asc" ? "desc" : "asc",
        });
      } else {
        // New field, default to ascending
        onSortChange({ field, order: "asc" });
      }
    },
    [sort, onSortChange],
  );

  // ---- Bulk action handlers ---- //
  const handleBulkStatus = React.useCallback(
    async (status: TaskStatus) => {
      setIsBulkProcessing(true);
      try {
        await onBulkAction("status", status);
      } finally {
        setIsBulkProcessing(false);
      }
    },
    [onBulkAction],
  );

  const handleBulkPriority = React.useCallback(
    async (priority: TaskPriority) => {
      setIsBulkProcessing(true);
      try {
        await onBulkAction("priority", priority);
      } finally {
        setIsBulkProcessing(false);
      }
    },
    [onBulkAction],
  );

  const handleBulkDelete = React.useCallback(async () => {
    setIsBulkProcessing(true);
    try {
      await onBulkAction("delete");
    } finally {
      setIsBulkProcessing(false);
    }
  }, [onBulkAction]);

  // ---- Loading state ---- //
  if (isLoading && tasks.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <TableSkeleton />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* ---- Scrollable table area ---- */}
      <div className="flex-1 overflow-x-auto overflow-y-auto min-h-0">
        <table className="w-full min-w-[500px] md:min-w-[700px] lg:min-w-[900px] table-fixed border-collapse">
          {/* ---- Sticky header ---- */}
          <thead className="sticky top-0 z-sticky bg-surface-secondary">
            <tr className="border-b border-border">
              {COLUMNS.map((col) => {
                if (col.key === "checkbox") {
                  return (
                    <th
                      key={col.key}
                      className={cn(col.width, "px-3 py-2.5", col.responsiveClass)}
                    >
                      <Checkbox
                        checked={
                          allPageSelected
                            ? true
                            : somePageSelected
                              ? "indeterminate"
                              : false
                        }
                        onCheckedChange={() => onToggleSelectAll()}
                        aria-label="Select all tasks on this page"
                      />
                    </th>
                  );
                }

                const sortField = col.key as SortField;

                return (
                  <th
                    key={col.key}
                    className={cn(
                      col.width,
                      "px-3 py-2.5 text-left",
                      col.sortable && "cursor-pointer select-none",
                      "group/header",
                      col.responsiveClass,
                    )}
                    onClick={col.sortable ? () => handleSort(sortField) : undefined}
                    role={col.sortable ? "columnheader" : undefined}
                    aria-sort={
                      sort.field === sortField
                        ? sort.order === "asc"
                          ? "ascending"
                          : "descending"
                        : undefined
                    }
                  >
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider",
                        sort.field === sortField
                          ? "text-text-primary"
                          : "text-text-tertiary",
                        col.sortable &&
                          "group-hover/header:text-text-primary transition-colors duration-fast",
                      )}
                    >
                      {col.label}
                      {col.sortable && (
                        <SortIndicator field={sortField} currentSort={sort} />
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>

          {/* ---- Body ---- */}
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td
                  colSpan={COLUMNS.length}
                  className="py-20 text-center"
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="rounded-full bg-surface-tertiary p-3">
                      <ListChecks
                        className="h-6 w-6 text-text-quaternary"
                        aria-hidden="true"
                      />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-secondary">
                        No tasks found
                      </p>
                      <p className="mt-1 text-xs text-text-quaternary">
                        Tasks you create for this project will appear here.
                      </p>
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  isSelected={selectedIds.has(task.id)}
                  onToggleSelect={onToggleSelect}
                  onStatusChange={onStatusChange}
                  onPriorityChange={onPriorityChange}
                  onRowClick={onRowClick}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ---- Pagination ---- */}
      {total > 0 && (
        <TablePagination
          page={page}
          limit={limit}
          total={total}
          onPageChange={onPageChange}
          onLimitChange={onLimitChange}
        />
      )}

      {/* ---- Bulk action bar ---- */}
      <BulkActionBar
        selectedCount={selectedIds.size}
        onBulkStatus={handleBulkStatus}
        onBulkPriority={handleBulkPriority}
        onBulkDelete={handleBulkDelete}
        onDeselectAll={onClearSelection}
        isProcessing={isBulkProcessing}
      />
    </div>
  );
}

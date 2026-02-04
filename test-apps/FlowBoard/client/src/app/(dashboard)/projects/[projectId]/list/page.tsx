"use client";

import * as React from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { TaskTable } from "@/components/list/task-table";
import {
  useTableTasks,
  type SortField,
  type SortOrder,
  type TableSort,
} from "@/hooks/use-table-tasks";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// List Page -- Full-featured table view for project tasks.
//
// Reads sort/filter/pagination state from URL search params so the view is
// shareable and back-button-friendly.  Delegates all rendering to TaskTable.
// =============================================================================

/** Valid sort fields that can appear in the URL. */
const VALID_SORT_FIELDS = new Set<string>([
  "title",
  "status",
  "priority",
  "assignee",
  "dueDate",
  "createdAt",
]);

const VALID_LIMITS = new Set([10, 25, 50]);

/**
 * Parse URL search params into typed table state.
 */
function parseSearchParams(searchParams: URLSearchParams): {
  page: number;
  limit: number;
  sort: TableSort;
} {
  const rawPage = Number(searchParams.get("page"));
  const rawLimit = Number(searchParams.get("limit"));
  const rawSortBy = searchParams.get("sortBy");
  const rawSortOrder = searchParams.get("sortOrder");

  const page = rawPage > 0 ? rawPage : 1;
  const limit = VALID_LIMITS.has(rawLimit) ? rawLimit : 25;

  const sortField: SortField =
    rawSortBy && VALID_SORT_FIELDS.has(rawSortBy)
      ? (rawSortBy as SortField)
      : "createdAt";

  const sortOrder: SortOrder =
    rawSortOrder === "asc" || rawSortOrder === "desc"
      ? rawSortOrder
      : "desc";

  return { page, limit, sort: { field: sortField, order: sortOrder } };
}

// =============================================================================
// Component
// =============================================================================

export default function ListPage() {
  const params = useParams<{ projectId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const projectId = params.projectId;

  // ---- Parse initial state from URL ---- //
  const initial = React.useMemo(
    () => parseSearchParams(searchParams),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [], // Only parse on mount -- hook manages state from there
  );

  const {
    tasks,
    total,
    page,
    limit,
    sort,
    isLoading,
    selectedIds,
    setSort,
    setPage,
    setLimit,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    updateTask,
    bulkAction,
  } = useTableTasks(projectId, initial);

  // ---- Sync state changes back to URL (shallow) ---- //
  const updateURL = React.useCallback(
    (nextPage: number, nextLimit: number, nextSort: TableSort) => {
      const sp = new URLSearchParams();
      sp.set("page", String(nextPage));
      sp.set("limit", String(nextLimit));
      sp.set("sortBy", nextSort.field);
      sp.set("sortOrder", nextSort.order);
      router.replace(`?${sp.toString()}`, { scroll: false });
    },
    [router],
  );

  // ---- Wrapped handlers that also update URL ---- //

  const handleSortChange = React.useCallback(
    (nextSort: TableSort) => {
      setSort(nextSort);
      updateURL(1, limit, nextSort);
    },
    [setSort, limit, updateURL],
  );

  const handlePageChange = React.useCallback(
    (nextPage: number) => {
      setPage(nextPage);
      updateURL(nextPage, limit, sort);
    },
    [setPage, limit, sort, updateURL],
  );

  const handleLimitChange = React.useCallback(
    (nextLimit: number) => {
      setLimit(nextLimit);
      updateURL(1, nextLimit, sort);
    },
    [setLimit, sort, updateURL],
  );

  // ---- Inline edit handlers (optimistic) ---- //

  const handleStatusChange = React.useCallback(
    (taskId: string, status: TaskStatus) => {
      void updateTask(taskId, { status });
    },
    [updateTask],
  );

  const handlePriorityChange = React.useCallback(
    (taskId: string, priority: TaskPriority) => {
      void updateTask(taskId, { priority });
    },
    [updateTask],
  );

  // ---- Row click -- placeholder for task detail panel ---- //

  const handleRowClick = React.useCallback(
    (_taskId: string) => {
      // TODO: open task detail slide-over panel
    },
    [],
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TaskTable
        tasks={tasks}
        total={total}
        page={page}
        limit={limit}
        sort={sort}
        isLoading={isLoading}
        selectedIds={selectedIds}
        onSortChange={handleSortChange}
        onPageChange={handlePageChange}
        onLimitChange={handleLimitChange}
        onToggleSelect={toggleSelect}
        onToggleSelectAll={toggleSelectAll}
        onClearSelection={clearSelection}
        onStatusChange={handleStatusChange}
        onPriorityChange={handlePriorityChange}
        onBulkAction={bulkAction}
        onRowClick={handleRowClick}
      />
    </div>
  );
}

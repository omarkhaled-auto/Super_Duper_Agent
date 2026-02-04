"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// useTableTasks -- Table-specific data hook with sort, pagination, selection,
// optimistic updates, and bulk actions.
// =============================================================================

export type SortField =
  | "title"
  | "status"
  | "priority"
  | "assignee"
  | "dueDate"
  | "createdAt";
export type SortOrder = "asc" | "desc";

export interface TableSort {
  field: SortField;
  order: SortOrder;
}

export interface TableParams {
  projectId: string;
  page: number;
  limit: number;
  sort: TableSort;
  status?: TaskStatus | TaskStatus[];
  priority?: TaskPriority | TaskPriority[];
  search?: string;
}

interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface UseTableTasksReturn {
  /** Current page of tasks. */
  tasks: Task[];
  /** Total number of matching tasks across all pages. */
  total: number;
  /** Current page number (1-based). */
  page: number;
  /** Items per page. */
  limit: number;
  /** Current sort configuration. */
  sort: TableSort;
  /** True while data is loading. */
  isLoading: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Set of selected task IDs. */
  selectedIds: Set<string>;

  // --- Mutators ---------------------------------------------------------- //

  /** Change the sort field/order. */
  setSort: (sort: TableSort) => void;
  /** Navigate to a specific page. */
  setPage: (page: number) => void;
  /** Change items per page (resets to page 1). */
  setLimit: (limit: number) => void;
  /** Toggle selection of a single task. */
  toggleSelect: (taskId: string) => void;
  /** Select or deselect all tasks on the current page. */
  toggleSelectAll: () => void;
  /** Clear the entire selection. */
  clearSelection: () => void;
  /** Optimistically update a single task field (status/priority). */
  updateTask: (taskId: string, patch: Partial<Task>) => Promise<void>;
  /** Execute a bulk action on all selected tasks. */
  bulkAction: (
    action: "status" | "priority" | "assignee" | "delete",
    value?: string,
  ) => Promise<void>;
  /** Re-fetch the current page. */
  refetch: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Query string builder
// ---------------------------------------------------------------------------

function buildQueryString(params: TableParams): string {
  const sp = new URLSearchParams();

  sp.set("page", String(params.page));
  sp.set("limit", String(params.limit));
  sp.set("sortBy", params.sort.field);
  sp.set("sortOrder", params.sort.order);

  if (params.status) {
    const statuses = Array.isArray(params.status)
      ? params.status
      : [params.status];
    statuses.forEach((s) => sp.append("status", s));
  }
  if (params.priority) {
    const priorities = Array.isArray(params.priority)
      ? params.priority
      : [params.priority];
    priorities.forEach((p) => sp.append("priority", p));
  }
  if (params.search) {
    sp.set("search", params.search);
  }

  return `?${sp.toString()}`;
}

// =============================================================================
// Hook
// =============================================================================

export function useTableTasks(
  projectId: string,
  initialParams?: Partial<Pick<TableParams, "page" | "limit" | "sort">>,
): UseTableTasksReturn {
  // ---- State ------------------------------------------------------------- //
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPageState] = useState(initialParams?.page ?? 1);
  const [limit, setLimitState] = useState(initialParams?.limit ?? 25);
  const [sort, setSortState] = useState<TableSort>(
    initialParams?.sort ?? { field: "createdAt", order: "desc" },
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Keep a stable reference to current params for the fetch callback
  const paramsRef = useRef<TableParams>({
    projectId,
    page,
    limit,
    sort,
  });

  // Update ref whenever state changes
  useEffect(() => {
    paramsRef.current = { projectId, page, limit, sort };
  }, [projectId, page, limit, sort]);

  // ---- Fetch ------------------------------------------------------------- //
  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = paramsRef.current;
      const endpoint = `/projects/${params.projectId}/tasks${buildQueryString(params)}`;
      const res = await api.get<TasksResponse>(endpoint);
      setTasks(res.tasks);
      setTotal(res.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load tasks");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Serialize dependency key
  const depsKey = `${projectId}:${page}:${limit}:${sort.field}:${sort.order}`;

  useEffect(() => {
    void fetchTasks();
  }, [depsKey, fetchTasks]);

  // ---- Mutators ---------------------------------------------------------- //

  const setSort = useCallback((next: TableSort) => {
    setSortState(next);
    setPageState(1); // reset page on sort change
  }, []);

  const setPage = useCallback((next: number) => {
    setPageState(next);
  }, []);

  const setLimit = useCallback((next: number) => {
    setLimitState(next);
    setPageState(1); // reset page on limit change
  }, []);

  // ---- Selection --------------------------------------------------------- //

  const toggleSelect = useCallback((taskId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(taskId)) {
        next.delete(taskId);
      } else {
        next.add(taskId);
      }
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelectedIds((prev) => {
      const allOnPage = tasks.map((t) => t.id);
      const allSelected = allOnPage.every((id) => prev.has(id));

      if (allSelected) {
        // Deselect all on current page
        const next = new Set(prev);
        allOnPage.forEach((id) => next.delete(id));
        return next;
      } else {
        // Select all on current page
        const next = new Set(prev);
        allOnPage.forEach((id) => next.add(id));
        return next;
      }
    });
  }, [tasks]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // ---- Optimistic single-task update ------------------------------------ //

  const updateTask = useCallback(
    async (taskId: string, patch: Partial<Task>) => {
      // 1. Snapshot for rollback
      const snapshot = tasks.map((t) => ({ ...t }));

      // 2. Optimistic update
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, ...patch } : t)),
      );

      try {
        // 3. Persist to server
        await api.patch(`/projects/${projectId}/tasks/${taskId}`, patch);
      } catch (err) {
        // 4. Rollback on failure
        setTasks(snapshot);
        throw err;
      }
    },
    [tasks, projectId],
  );

  // ---- Bulk actions ------------------------------------------------------ //

  const bulkAction = useCallback(
    async (
      action: "status" | "priority" | "assignee" | "delete",
      value?: string,
    ) => {
      const ids = Array.from(selectedIds);
      if (ids.length === 0) return;

      try {
        if (action === "delete") {
          // Delete tasks via individual calls or bulk endpoint
          await api.post(`/projects/${projectId}/tasks/bulk`, {
            action: "delete",
            taskIds: ids,
          });
        } else {
          await api.post(`/projects/${projectId}/tasks/bulk`, {
            action,
            taskIds: ids,
            value,
          });
        }

        // Clear selection and re-fetch after bulk action
        setSelectedIds(new Set());
        await fetchTasks();
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Bulk action failed");
        }
        // Re-fetch to ensure consistency
        await fetchTasks();
      }
    },
    [selectedIds, projectId, fetchTasks],
  );

  return {
    tasks,
    total,
    page,
    limit,
    sort,
    isLoading,
    error,
    selectedIds,
    setSort,
    setPage,
    setLimit,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    updateTask,
    bulkAction,
    refetch: fetchTasks,
  };
}

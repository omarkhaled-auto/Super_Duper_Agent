"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";
import type { Task, TaskStatus } from "@/types";

// =============================================================================
// Board State Hook -- Manages tasks grouped by status for the kanban board
//
// - Fetches tasks for a project, groups them by TaskStatus column
// - Provides optimistic moveTask / addTask / updateTask mutations
// - Reverts local state on API failure
// =============================================================================

/** Column identifiers in display order */
export const BOARD_COLUMNS: TaskStatus[] = [
  "BACKLOG" as TaskStatus,
  "TODO" as TaskStatus,
  "IN_PROGRESS" as TaskStatus,
  "IN_REVIEW" as TaskStatus,
  "DONE" as TaskStatus,
];

/** Map of status -> ordered task list */
export type ColumnMap = Record<string, Task[]>;

interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

interface UseBoardReturn {
  columns: ColumnMap;
  isLoading: boolean;
  error: string | null;
  moveTask: (
    taskId: string,
    newStatus: TaskStatus,
    newPosition: number,
  ) => Promise<void>;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;
  refetch: () => Promise<void>;
}

/** Group a flat task list into columns keyed by status. */
function groupByStatus(tasks: Task[]): ColumnMap {
  const columns: ColumnMap = {};
  for (const status of BOARD_COLUMNS) {
    columns[status] = [];
  }
  for (const task of tasks) {
    const status = task.status as string;
    if (columns[status]) {
      columns[status].push(task);
    } else {
      // Fallback: put unrecognized statuses in BACKLOG
      columns[BOARD_COLUMNS[0] as string].push(task);
    }
  }
  // Sort each column by position ascending
  for (const status of BOARD_COLUMNS) {
    columns[status as string].sort((a, b) => a.position - b.position);
  }
  return columns;
}

export function useBoard(projectId: string): UseBoardReturn {
  const [columns, setColumns] = useState<ColumnMap>(() => {
    const initial: ColumnMap = {};
    for (const status of BOARD_COLUMNS) {
      initial[status as string] = [];
    }
    return initial;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Keep a snapshot for rollback on failed API calls
  const snapshotRef = useRef<ColumnMap | null>(null);

  // ---- Fetch all tasks for the project ----
  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await api.get<TasksResponse>(
        `/projects/${projectId}/tasks?limit=500&sortBy=position&sortOrder=asc`,
      );
      const grouped = groupByStatus(res.tasks);
      setColumns(grouped);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load board tasks");
      }
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  // ---- Move task: optimistic update + API call ----
  const moveTask = useCallback(
    async (taskId: string, newStatus: TaskStatus, newPosition: number) => {
      // Save snapshot for rollback
      setColumns((prev) => {
        snapshotRef.current = prev;

        const next: ColumnMap = {};
        let movedTask: Task | null = null;

        // Remove task from its current column
        for (const status of BOARD_COLUMNS) {
          const key = status as string;
          const filtered = prev[key].filter((t) => {
            if (t.id === taskId) {
              movedTask = { ...t, status: newStatus, position: newPosition };
              return false;
            }
            return true;
          });
          next[key] = [...filtered];
        }

        if (!movedTask) return prev;

        // Insert task into the new column at the correct position
        const targetKey = newStatus as string;
        const targetColumn = [...next[targetKey]];
        const clampedPos = Math.min(newPosition, targetColumn.length);
        targetColumn.splice(clampedPos, 0, movedTask);

        // Re-index positions for the target column
        targetColumn.forEach((t, i) => {
          t.position = i;
        });

        next[targetKey] = targetColumn;

        return next;
      });

      // Call the API
      try {
        await api.put(`/tasks/${taskId}/reorder`, {
          status: newStatus,
          position: newPosition,
        });
      } catch {
        // Revert to snapshot on failure
        if (snapshotRef.current) {
          setColumns(snapshotRef.current);
          snapshotRef.current = null;
        }
        // Re-throw so callers can show an error toast
        throw new Error("Failed to move task. Changes have been reverted.");
      }
    },
    [],
  );

  // ---- Add task to local state ----
  const addTask = useCallback((task: Task) => {
    setColumns((prev) => {
      const key = task.status as string;
      const column = prev[key] ? [...prev[key], task] : [task];
      return { ...prev, [key]: column };
    });
  }, []);

  // ---- Update a task in local state ----
  const updateTask = useCallback(
    (taskId: string, updates: Partial<Task>) => {
      setColumns((prev) => {
        const next: ColumnMap = {};
        for (const status of BOARD_COLUMNS) {
          const key = status as string;
          next[key] = prev[key].map((t) =>
            t.id === taskId ? { ...t, ...updates } : t,
          );
        }
        return next;
      });
    },
    [],
  );

  // ---- Remove a task from local state ----
  const removeTask = useCallback((taskId: string) => {
    setColumns((prev) => {
      const next: ColumnMap = {};
      for (const status of BOARD_COLUMNS) {
        const key = status as string;
        next[key] = prev[key].filter((t) => t.id !== taskId);
      }
      return next;
    });
  }, []);

  return {
    columns,
    isLoading,
    error,
    moveTask,
    addTask,
    updateTask,
    removeTask,
    refetch: fetchTasks,
  };
}

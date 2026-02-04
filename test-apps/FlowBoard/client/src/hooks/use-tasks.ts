"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";
import type { Task } from "@/types";
import { TaskStatus, TaskPriority } from "@/types";

// =============================================================================
// Re-export types so downstream consumers that import from "@/hooks/use-tasks"
// continue to work without changes.  The canonical types live in "@/types"
// (backed by the flowboard-shared package).
// =============================================================================

export type { Task };
export { TaskStatus, TaskPriority };

// Legacy aliases used by list-view components that expect a TaskAssignee shape.
// The shared Task type uses `assignee: UserProfile | null` (singular).  If
// list-view code still references `task.assignees`, those call-sites need
// updating separately.
export interface TaskAssignee {
  id: string;
  name: string;
  avatar?: string;
}

interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface TaskQueryParams {
  projectId?: string;
  status?: TaskStatus | TaskStatus[];
  priority?: TaskPriority | TaskPriority[];
  assigneeId?: string;
  dueDate?: string;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

interface UseTasksReturn {
  tasks: Task[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// =============================================================================
// useTasks -- Fetch tasks with query params and filtering support
// =============================================================================

function buildQueryString(params: TaskQueryParams): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;

    if (Array.isArray(value)) {
      value.forEach((v) => searchParams.append(key, String(v)));
    } else {
      searchParams.set(key, String(value));
    }
  });

  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

export function useTasks(params: TaskQueryParams = {}): UseTasksReturn {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const paramsRef = useRef(params);
  const fetchedRef = useRef(false);

  // Serialize params for dependency tracking
  const paramsKey = JSON.stringify(params);

  const fetchTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const currentParams = paramsRef.current;
      const endpoint = currentParams.projectId
        ? `/projects/${currentParams.projectId}/tasks${buildQueryString(
            // Omit projectId from query string since it's in the path
            (() => {
              const { projectId: _, ...rest } = currentParams;
              return rest;
            })(),
          )}`
        : `/tasks/me${buildQueryString(currentParams)}`;

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

  useEffect(() => {
    paramsRef.current = params;
  }, [paramsKey]);

  useEffect(() => {
    fetchedRef.current = true;
    fetchTasks();
  }, [paramsKey, fetchTasks]);

  return { tasks, total, isLoading, error, refetch: fetchTasks };
}

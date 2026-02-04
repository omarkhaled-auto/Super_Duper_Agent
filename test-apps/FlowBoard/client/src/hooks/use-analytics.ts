"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api, { ApiError } from "@/lib/api";

import type { TasksOverTimeDataPoint } from "@/components/analytics/tasks-over-time-chart";
import type { TasksByStatusDataPoint } from "@/components/analytics/tasks-by-status-chart";
import type { TasksByPriorityDataPoint } from "@/components/analytics/tasks-by-priority-chart";
import type { VelocityDataPoint } from "@/components/analytics/velocity-chart";

// =============================================================================
// Analytics Data Types
// =============================================================================

export interface AnalyticsData {
  tasksOverTime: TasksOverTimeDataPoint[];
  tasksByStatus: TasksByStatusDataPoint[];
  tasksByPriority: TasksByPriorityDataPoint[];
  velocity: VelocityDataPoint[];
}

// Server returns AnalyticsData directly, no wrapper

interface UseAnalyticsReturn {
  data: AnalyticsData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// =============================================================================
// useAnalytics -- Fetch analytics data for a project
// =============================================================================

/**
 * Hook to fetch analytics data for a given project.
 *
 * Makes a GET request to /analytics/projects/:id and returns
 * structured data for all four chart types:
 *   - tasksOverTime (last 30 days)
 *   - tasksByStatus (donut breakdown)
 *   - tasksByPriority (bar breakdown)
 *   - velocity (last 8 weeks)
 *
 * @param projectId - The project ID to fetch analytics for. Pass null to skip.
 * @returns { data, isLoading, error, refetch }
 */
export function useAnalytics(projectId: string | null): UseAnalyticsReturn {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const prevProjectIdRef = useRef<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    if (!projectId) {
      setData(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.get<AnalyticsData>(
        `/analytics/projects/${projectId}`
      );
      setData(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load analytics data");
      }
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    // Re-fetch when projectId changes
    if (projectId !== prevProjectIdRef.current) {
      prevProjectIdRef.current = projectId;
      fetchAnalytics();
    }
  }, [projectId, fetchAnalytics]);

  return { data, isLoading, error, refetch: fetchAnalytics };
}

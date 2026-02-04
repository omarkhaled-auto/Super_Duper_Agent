import { useState, useEffect, useCallback } from "react";
import api, { ApiError } from "@/lib/api";
import type { Project } from "@/types";

// =============================================================================
// useProject — fetch a single project by ID
// =============================================================================

interface UseProjectReturn {
  project: Project | null;
  isLoading: boolean;
  error: string | null;
  errorStatus: number | null;
  refetch: () => Promise<void>;
}

/**
 * Hook that fetches a single project from `GET /api/projects/:id`.
 *
 * @param projectId - The project identifier to fetch.
 * @returns The project data, loading / error states, and a refetch function.
 */
export function useProject(projectId: string): UseProjectReturn {
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);

  const fetchProject = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setErrorStatus(null);

    try {
      const res = await api.get<Project>(
        `/projects/${projectId}`,
      );
      setProject(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setErrorStatus(err.status);
      } else {
        setError("Failed to load project.");
        setErrorStatus(500);
      }
      setProject(null);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchProject();
  }, [fetchProject]);

  return { project, isLoading, error, errorStatus, refetch: fetchProject };
}
